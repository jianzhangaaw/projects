# 后端代码审查

审查对象：`projects/05-recruit-platform/backend`（Spring Boot 3.3.6 / Java 17）

规模：118 个 Java 文件、6006 行；15 个 Controller、70 个端点；13 张表、13 个实体。

**范围说明**：8 个作品里只有这一个有真正的服务端。另外七个是 Python 脚本（无服务）、微信小程序（全本地存储）、Java Swing 桌面（无网络）、静态网页（无后端），文末单独说它们的"要不要加后端"。

---

## 一句话结论

分层是有的，但**权限边界基本没做**：角色校验做了（`/api/admin/` 只有管理员能进），资源归属校验几乎没有。13 个 `*ServiceImpl` 里有 11 个是 9 行的空类，业务逻辑全堆在 Controller，所以事务也无处可加。

现在这套代码如果部署到公网，任何一个注册用户都能删掉别人的简历。

> **状态（2026-11-19）**：下面 P0 的 7 项已经修复并跑过越权用例（`scripts/check-authz.py`，18 项全通过）；
> P1–P4 未动，留作下一阶段。逐项改动见文末「修复记录」。

---

## P0 安全

### 1. 企业资料接口信任客户端传来的 userId　`已修复`

`CompanyController.java:35 / 43 / 55 / 102`

四个接口都写成 `@RequestParam Long userId`，服务端从不校验它是否等于当前登录用户：

```java
@GetMapping("/mine")
public Result<Company> mine(@RequestParam Long userId) {
    Company company = service.getOne(new LambdaQueryWrapper<Company>()
            .eq(Company::getUserId, userId)      // userId 完全由客户端给
            .last("limit 1"));
    return Result.success(company);
}
```

任何 COMPANY 账号改一个 query 参数就能读、改别家企业的资料：

```
GET  /api/company/companies/mine?userId=2          # 读别人
POST /api/company/companies/mine?userId=2          # 改别人（名称/联系人/电话/简介）
PATCH /api/company/companies/mine/logo?userId=2&logoFileId=9   # 换别人的 logo
```

**改法**：删掉 `userId` 参数，从 `CurrentUserContext.userId()` 取。四个接口改完不到 20 行。

### 2. BaseCrudController 是裸 CRUD，没有归属校验　`已修复`

`BaseCrudController.java:31-62`

6 个 Controller 继承了它：`Company`、`Job`、`Resume`、`StudentExperience`、`StudentProfile`、`StudentSkill`。继承来的这三个端点只受"URL 前缀角色"保护：

| 端点 | 现状 | 后果 |
| --- | --- | --- |
| `GET /{id}` | 直接 `getById(id)` | 读任意记录 |
| `PUT /{id}` | `BeanWrapper` 强设 id 后 `updateById` | 改任意记录 |
| `DELETE /{id}` | 直接 `removeById(id)` | 删任意记录 |

因为拦截器只校验 `/api/student/` 前缀要求 STUDENT 角色，任何学生都能：

```
DELETE /api/student/resumes/{别人的简历id}
PUT    /api/student/skills/{别人的技能id}
PUT    /api/company/companies/{别家企业id}      # 企业账号同理
```

`BaseCrudController.java:43` 的 update 尤其危险——它把请求体里的任意字段按 id 写回去，连 `userId`、`reviewStatus` 都能被改。

**改法（二选一）**：
- 简单：在 6 个子类里 `@Override` update/delete，先查记录再比对 `userId`；
- 彻底：删掉 `BaseCrudController` 的写操作，只保留分页查询，写操作全部走带归属校验的自定义方法。

### 3. 企业能看任意学生的简历文件　`已修复`

`FileResourceController.java:124`

```java
if ("COMPANY".equals(CurrentUserContext.role()) && "RESUME".equals(resource.getBusinessType())) {
    return resource;   // 不校验这份简历是否投给当前企业
}
```

任何企业账号遍历 `GET /api/files/{id}/preview` 就能拿到全平台所有学生上传的简历 PDF/Word。文件 id 是自增的，遍历成本极低。

**改法**：校验存在一条 `job_application`，同时满足 `resume_id = 该文件所属简历` 且 `company_id = 当前企业`。

### 4. 登录错误信息可枚举用户名　`已修复`

`AuthService.java:99-100`

账号不存在 → `"账号不存在或已被禁用"`；密码错 → `"用户名或密码错误"`。两条不同的返回让攻击者能批量判断哪些用户名是有效的。**改法**：两种情况统一返回 `"用户名或密码错误"`，只在日志里区分。

### 5. 密码没有强度校验　`已修复`

`RegisterRequest.java` 只标了 `@NotBlank`。`{"password":"1"}` 能注册成功。

**改法**：`@Size(min=8, max=64)` + 至少两类字符的正则，或者直接用 `@Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d).{8,}$")`。

### 6. 登录没有防爆破　`已修复`

没有失败计数、没有临时锁定、没有验证码。挂着字典跑一晚上就能撞开弱密码。**改法**：按 `username + IP` 计数，5 次失败锁 15 分钟（在校人数有限，内存 `ConcurrentHashMap` 就够，不用上 Redis）。

### 7. CORS 是危险组合　`已修复`

`WebMvcConfig.java`：

```java
registry.addMapping("/**")
        .allowedOriginPatterns("*")
        .allowCredentials(true);
```

`allowedOriginPatterns("*")` + `allowCredentials(true)` 等价于允许任意站点带着凭证发请求。现在认证走 `Authorization` 头不走 Cookie，风险被压低了，但这个配置不该留着——前端部署在固定域名，就应该写死。

---

## P1 正确性

### 8. 投递 + 发通知没有事务　`已修复`

`JobApplicationController.java:97-120`

```java
service.save(body);              // 投递落库
createNotification(...);         // 通知失败不影响上面
```

通知抛异常时投递已经提交，企业永远收不到这条提醒。`AdminReviewController.java:201` 的审核分支更严重——"改主表 + 删草稿 + 发通知"三步里任何一步失败都会留下半完成状态（比如草稿删了、主表没更新）。

**改法**：这两个方法下沉到 Service 并加 `@Transactional`。注意 `@Transactional` 只在同类方法互调时失效的问题——`doReviewCompany` 是 private，被同类 public 方法调用，加了注解也不生效，必须挪到独立 Service。

### 9. 重复投递有并发窗口　`已修复`

`JobApplicationController.java:101`

```java
long alreadyApplied = service.count(...);   // 先查
if (alreadyApplied > 0) throw ...;
service.save(body);                          // 再插
```

两个并发请求都能通过 count 检查，然后各插一条。数据库上也没有 `(student_id, job_id)` 唯一约束兜底。

**改法**：加唯一索引 `uk_application_student_job (student_id, job_id)`，插入时 catch `DuplicateKeyException` 转成业务提示。查询可以保留（提前给出友好提示），但正确性靠数据库。

### 10. 投递状态没有状态机　`已修复`

`JobApplicationController.java:203`

```java
if (!"PENDING".equals(status) && !"PASSED".equals(status) && !"REJECTED".equals(status))
    throw new BusinessException("投递状态只能是 PENDING、PASSED 或 REJECTED");
```

只校验了**目标**状态合法，没校验**当前**状态。企业可以把自己的 PASSED 改回 PENDING，也可以把 REJECTED 改成 PASSED，学生已经收到"通过"通知再改成"拒绝"。

**改法**：定义 `PENDING → PASSED | REJECTED`，已终态拒绝再改。

### 11. 审核通过后驳回原因残留　`已修复`

`AdminReviewController.java:201` 附近，草稿分支通过时只设 `reviewStatus = "APPROVED"`，没清 `reviewReason`。上一次驳回的原因会一直挂在这条记录上，前端展示出来就是"已通过，原因：材料不全"。

---

## P2 性能

### 12. 列表接口 N+1　`已修复`

`JobApplicationController.toCompanyDetail`：每条投递查 3 次（job、student、resume）。企业端 100 条投递 = 300 次查询。

同一个类里 `AdminReviewController.pendingJobs` 已经写了正确做法（`listByIds` + `toMap` 批量装配），照搬即可。

### 13. 每个请求重复查"当前学生/企业"

`currentStudentProfile()` 在一个请求里可能被调 2-3 次（`create` 里一次、`scopedWrapper` 里又一次），每次一条 SQL。**改法**：请求级缓存，`StudentProfileResolver` 里用 `ThreadLocal` 存一次（注意在 `afterCompletion` 清理），或者直接查一次传下去。

### 14. 日志级别把 SQL 全打出来

`application.yml`：

```yaml
logging:
  level:
    com.recruit_resume: DEBUG
    com.recruit_resume.mapper: DEBUG
```

生产环境会把每条 SQL 和参数（含手机号、邮箱、简历内容）写进日志文件。应该改成 `INFO`，把 `mapper: DEBUG` 挪到 `application-dev.yml`。

---

## P3 架构

### 15. Service 层是空壳　`部分修复`

13 个 `*ServiceImpl`，11 个只有这 9 行：

```java
@Service
public class StudentProfileServiceImpl extends ServiceImpl<StudentProfileMapper, StudentProfile>
        implements StudentProfileService {
}
```

业务逻辑全在 Controller：`JobApplicationController` 370 行、`AdminReviewController` 229 行。后果是三重的——不能复用（"取当前学生"在三处各写一遍）、不能事务、不能单测（Controller 依赖 Servlet）。

### 16. 每个动作两个端点

`AdminReviewController` 用 12 个端点做 4 件事（每个动作都有 `@PatchMapping` + `@PutMapping` 两份）；`JobApplicationController`、`AdminUserController` 也有同样问题。这是历史兼容遗留，现在删掉 PUT 版本不影响任何前端调用（前端只用了其中一套）。

### 17. 实体直接当 API 响应

`Result<UserAccount>`、`Result<Company>`、`Result<Resume>` 一共 11 处。现在靠 `account.setPassword(null)`、`erasePassword()` 打补丁——只要实体新增一个敏感字段就会漏。**改法**：请求/响应各一套 DTO。

### 18. 两套权限模型并存

拦截器按 URL 前缀判角色（`/api/admin/`、`/api/student/`、`/api/company/`），但 `/api/applications`、`/api/files`、`/api/jobs`、`/api/notifications` 这些公共前缀的接口在 Controller 里自己判角色。加新接口时很容易忘记判。

**改法**：统一到 `@PreAuthorize` 或自定义注解，把"哪个角色能访问"写在方法上，而不是靠 URL 前缀约定。

---

## P4 运维

| 问题 | 现状 | 建议 |
| --- | --- | --- |
| 没有健康检查 | 没有 Actuator，docker-compose 只检查 MySQL | 加 `spring-boot-starter-actuator`，`/actuator/health` 加进 compose healthcheck |
| 连接池用默认值 | Hikari 默认 10 连接 | 显式配 `maximum-pool-size` / `connection-timeout` |
| HTTP 状态码恒定 200 | 业务失败也返回 200，只有 body 里 `code` 不同 | 鉴权失败返 401/403，未找到返 404，让网关能按 status 报警 |
| 没有请求 id | 日志里无法串起一次请求 | 加 `MDC` + `X-Request-Id` |
| 文件预览无大小上限 | `openStream().transferTo()` 没有上限 | 限制最大字节数，超了中断 |

---

## 优化方案

### 阶段一：安全止血（1–2 天，优先级最高）

| # | 动作 | 涉及文件 | 工作量 |
| --- | --- | --- | --- |
| 1 | `CompanyController` 四个接口改用 `CurrentUserContext.userId()` | 1 个文件 | 0.5 h |
| 2 | `BaseCrudController` 的 update/delete 加归属校验（6 个子类覆写） | 7 个文件 | 3 h |
| 3 | 简历预览校验"是否投给当前企业" | 1 个文件 + 1 个查询 | 1 h |
| 4 | 登录错误信息统一 | 1 处 | 10 min |
| 5 | 密码强度校验 | 1 个 DTO | 10 min |
| 6 | 登录失败计数与临时锁定 | 新增 1 个类 | 2 h |
| 7 | CORS 收紧 | 1 处 | 10 min |

做完这一阶段，水平越权和暴力破解两条路就堵上了。**如果只做一件事，做这个阶段。**

### 阶段二：数据一致性（2–3 天）

1. 把 `JobApplicationController` 的业务下沉到 `JobApplicationService`，加 `@Transactional`（投递 + 通知、状态变更 + 通知）
2. 把 `AdminReviewController` 的审核流程同样下沉，三步操作进一个事务
3. `job_application` 加唯一索引 `(student_id, job_id)`，插入时捕获 `DuplicateKeyException`
4. 投递状态加状态机校验
5. 审核通过时清空 `reviewReason`

### 阶段三：性能与可观测（1–2 天）

1. 三处 N+1 改成批量装配（照 `pendingJobs` 的写法）
2. 当前用户 profile 请求级缓存
3. 日志级别分离 dev/prod
4. Actuator + health check

### 阶段四：工程化（3–5 天）

1. 引入 Spring Security，用 `@PreAuthorize` 替换手写拦截器，统一权限模型
2. 请求/响应 DTO 分离
3. 删除 12 个重复的 PUT 端点
4. 连接池、文件大小上限、请求 id
5. 补集成测试：越权用例（用学生 A 的 token 删学生 B 的简历，断言 403）

### 一件事能做的话

阶段一。理由不是"更规范"，而是现在这套代码里：

- 企业 A 能改企业 B 的资料（改一个 query 参数）
- 任何学生能删任何学生的简历（改一个 path 参数）
- 任何企业能下载全平台学生的简历（遍历自增 id）

这三条放到公网上是数据事故，不是代码风格问题。

---

## 其他项目要不要加后端

| 项目 | 现状 | 建议 |
| --- | --- | --- |
| 01 MNIST / 02 关联规则 / 03 Titanic / 04 Spaceship | 离线脚本，命令行跑完出图 | **不需要**。加了服务反而把一个"能复现的实验"变成一个"要运维的服务"，对作品集是减分 |
| 06 单词小程序 | 全本地 `wx.setStorageSync` | 想展示后端能力可以做个同步接口，但现在的本地版更完整（离线可用），不建议改 |
| 07 Swing 成绩管理 | 序列化到本地 `students.dat` | 同上 |
| 08 静态旅游站 | 纯静态 | 同上 |

如果目标是"作品集里体现后端能力"，智聘通这一个够了，把阶段一做扎实，比再起三个小服务更有说服力。

---

## 修复记录（阶段一）

对应 `scripts/check-authz.py` 里的 18 条断言，全部通过。

| # | 问题 | 改法 | 文件 |
| --- | --- | --- | --- |
| 1 | 企业资料接口信任客户端 `userId` | 参数改为 `required=false`，传了就必须等于 `CurrentUserContext.userId()`，否则 403；不传直接用当前用户。同时 `saveMine` 里强制 `body.setId(existing.getId())`，防止客户端带 id 覆盖别的记录 | `CompanyController.java` |
| 2 | 泛型裸 CRUD 无归属校验 | `BaseCrudController` 增加抽象方法 `isOwnedBy(T, CurrentUser)`，`get/update/delete` 先 `requireOwned(id)`：不存在 404、不属于自己 403。抽象方法没有默认实现，漏实现会编译失败而不是静默放行。6 个子类各自实现（Company/Profile 比 `userId`，Skill/Experience/Resume 比 `studentId`，Job 经 `company.userId` 比对） | `BaseCrudController.java` + 6 个 Controller |
| 3 | 企业能看任意学生简历 | 校验链路 `file_resource.id → resume.file_id → job_application.resume_id + company_id`，只有存在一条"投给当前企业"的投递才放行 | `FileResourceController.java` |
| 4 | 登录信息可枚举用户名 | 账号不存在、密码错误统一返回「用户名或密码错误」，日志里仍分开记 | `AuthService.java` |
| 5 | 密码无强度 | `@Size(8,64)` + `^(?=.*[A-Za-z])(?=.*\d).+$`；用户名也加了 3–32 位和字符集限制。前端 `RegisterView` 同步加了两条规则，避免前后端口径不一致 | `RegisterRequest.java`、`RegisterView.vue` |
| 6 | 无防爆破 | 新增 `LoginAttemptService`：按用户名计失败次数，5 次锁 15 分钟；锁定期内直接拒，不再做一次 BCrypt 校验（省 CPU）。用 `ConcurrentHashMap`，每 100 次操作清理一次过期项 | `LoginAttemptService.java`、`AuthService.java` |
| 7 | CORS 过宽 | `allowedOriginPatterns("*")` 改为 `allowedOrigins` 白名单，默认只允许 `localhost:5173` / `127.0.0.1:5173`，部署时用 `CORS_ALLOWED_ORIGINS` 覆盖 | `WebMvcConfig.java`、`application.yml` |

顺带修的两处：

- `JobController.updateStatus` 原来没有任何归属校验，企业能改任意岗位的状态。现在先 `requireOwned(id)`，并限制成只能置为 `DRAFT / PENDING / OFFLINE`，已发布的岗位不能退回待审。
- `CompanyController.saveMine` 里 `body.setId(...)` 的补丁（见上表第 1 行），不然后果是客户端能通过请求体指定 id 覆盖任意企业。

### 为什么用「兼容校验」而不是直接删参数

`mine?userId=` 这套参数前端有 9 处调用。直接删参数要同时改 5 个 `.vue`，改漏一个就是 400。这一轮的目标是止血，所以选「参数保留、值必须等于当前用户」——前端零改动，越权立刻失效。下一阶段（配合 Service 下沉）再把参数彻底去掉。

### 还没做的

P1–P4 原样保留：投递/审核仍无事务、重复投递仍靠 count 兜底、列表仍有 N+1、11 个 ServiceImpl 仍是空壳、日志仍是 DEBUG 全量打 SQL。这些在阶段二、三处理。

---

## 修复记录（阶段二：数据一致性）

对应 `scripts/check-consistency.py` 的 25 条断言，全部通过；阶段一的 `check-authz.py` 18 条同时回归通过；前端 11 个页面无请求失败。

### 1. 业务下沉到 Service，事务落在正确的位置

| 新增 | 职责 |
| --- | --- |
| `JobApplicationService` / `Impl` | 投递、撤回、状态变更、分页、详情装配 |
| `AdminReviewService` / `Impl` | 待审列表、企业审核、岗位审核 |

两个 Controller 从 370 / 229 行降到约 190 / 150 行，只做参数解析、角色门禁、包 `Result`。

事务边界：

- `apply`：插入投递 + 写通知 —— 一个事务，通知失败整体回滚
- `updateStatus`：改状态 + 写通知 —— 一个事务
- `reviewCompany`：改主表 + 删草稿 + 写通知 —— 一个事务
- `reviewJob`：改状态 + 写通知 —— 一个事务

Service 方法都显式接收 `userId` / `role`，不读 `CurrentUserContext`——单测里不用伪造 ThreadLocal。

### 2. 重复投递：唯一索引早就有，缺的是异常处理

排查时发现 `job_application` 上已经有 `uk_job_application_job_student (job_id, student_id)`，报告里写「表上也没有唯一索引」是我看漏了。数据库层本来拦得住，问题是代码没捕获 `DuplicateKeyException`，并发时第二个请求返回 500。现在 catch 后转成 400「已投递过该岗位」。

### 3. 状态机

| 对象 | 允许的流转 | 原来 |
| --- | --- | --- |
| 投递 | `PENDING → PASSED \| REJECTED`，终态不可回退 | 可从 PASSED 改回 PENDING，学生收到「通过」再被改成「拒绝」 |
| 岗位审核 | `PENDING → PUBLISHED \| REJECTED` | 可对任意状态的岗位反复审核 |
| 企业审核 | `PENDING → APPROVED \| REJECTED` | 已通过的企业可以再审一次 |

### 4. 一个 MyBatis-Plus 的坑

「审核通过后 reviewReason 残留」第一版改成 `update.setReviewReason(null)` + `updateById`——**不生效**。`updateById` 默认 `FieldStrategy.NOT_NULL`，null 字段直接跳过，不会生成 `SET review_reason = NULL`。是测试脚本直接查库才发现的（接口返回的还是旧值）。

改用 `LambdaUpdateWrapper.set(field, null)` 显式置空。同样的坑还埋在 `JobController.updateStatus` 和 `CompanyController.saveMine`（重新提交时清驳回原因），一起修了。

### 5. 建岗位 / 建企业资料时的自封与冒名

`POST /api/jobs` 和 `POST /api/company/companies` 原来走泛型 create，`companyId` / `userId` / `status` / `reviewStatus` 全由请求体决定：企业可以给别家发岗位、把自己建到别人名下、岗位直接建成 PUBLISHED、企业自封 APPROVED。

两个 Controller 各覆写 create：强制当前用户、强制草稿态 / 待审态，请求体里的这些字段一律忽略。

### 6. N+1 顺手消掉

`by-company/detail` 原来每条投递查 3 次（job / student / resume），100 条就是 300 次查询。改成批量装配后实测：**2 条投递只发 5 条 SQL**（1 查企业 + 1 查投递 + 3 次批量），与投递条数无关；改前是 1 + 3×2 = 7 条。

### 7. 顺带修的两个回归

- `BaseCrudController.requireOwned` 加了归属校验后，管理员访问 `/api/jobs/{id}` 也被 403——审核场景需要读任意记录，加了 ADMIN 例外（`/api/student/`、`/api/company/` 前缀在拦截器层就挡住了管理员，所以这个例外只影响公共前缀的读接口）。
- `CompanyController.updateLogo` 改成从上下文取 userId 后，`CompanyControllerTest` 没设置登录上下文，测试从「400 企业不存在」变成「401 未登录」——修了测试，并补了一条「传别人的 userId 返回 403」的用例。

### 还没做的（阶段三、四）

- 日志仍是 DEBUG 全量打 SQL（`application-logging` 没拆 dev/prod）
- 没有 Actuator、连接池仍是默认 10
- `HTTP 状态码恒 200`：业务失败也返回 200，只有 body 里 code 不同
- 另外 9 个 `ServiceImpl` 仍是空壳（`Resume`、`Company`、`Job`、`StudentProfile` 等），它们的业务逻辑还在 Controller
- 每个动作的 PATCH/PUT 双端点还在
