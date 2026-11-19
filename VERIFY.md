# 验证记录

不是「在我机器上能跑」，而是每一项都复制到 `%TEMP%\pf-verify` 这类干净目录、按 README 的命令从零执行，贴的是实际退出码与产物。

**环境**：Windows 11、Python 3.14.0、JDK 17.0.14、Node 24.18、Docker 29.6（MySQL 8.0.46 容器）、微信开发者工具 2.01.2510280

| 项目 | 执行的命令 | 结果 |
| --- | --- | --- |
| 01 MNIST | `python src/mnist_dim_reduction.py` | exit 0，55 秒，5 种算法指标全部输出，11 张图重生成；t-SNE trustworthiness 0.9895 |
| 02 关联规则 | `python run_all.py` | exit 0，29.5 秒，正确性校验 → 实验一~五 → 11 张图，全部重跑成功 |
| 03 Titanic | `python src/analyze.py` | exit 0，输出 6 张图 + `results.json`（93 个键），控制台报告完整 |
| 04 Spaceship | `run_experiment.py --models logreg,knn,lightgbm,mlp --seeds 42,2025,7` | exit 0，4 模型 × 3 种子全部完成，见下表 |
| 05 智聘通 | `docker compose up -d` → `mvnw -s settings.xml -DskipTests package` → `java -jar ...` → `npm run dev` | 容器 healthy；jar 构建 exit 0；登录接口返回 200 + JWT；前端 5173 返回 200 |
| 05 三端界面 | 用 puppeteer 驱动 Chrome 登录三种角色后截图 | 学生端 4 页、企业端 3 页、管理端 2 页全部正常渲染，种子数据正确显示 |
| 05 前端构建 | `npm run build`（`vue-tsc -b && vite build`） | exit 0，`✓ built in 1.08s`，类型检查通过 |
| 05 后端测试 | `mvnw -s settings.xml test` | exit 0，10 个测试类全部通过；日志里能看到 OSS 不可用时降级到本地存储的 fallback 正常触发 |
| 05 安全回归 | `python scripts/check-authz.py` | 18 项断言全通过：8 条越权用例返回 403、5 条合法请求返回 200、认证 3 条 + CORS 2 条 |
| 05 一致性回归 | `python scripts/check-consistency.py` | 25 项断言全通过：自封/冒名被忽略、状态机拒绝回退、重复投递 400、审核通过后 reviewReason 为 null、通知落库 |
| 05 N+1 | 查后端日志的 `Preparing:` 条数 | 2 条投递的 `by-company/detail` 只发 5 条 SQL（1 企业 + 1 投递 + 3 批量），改前是 1+3×2=7 |
| 05 前端回归 | puppeteer 走 11 个页面（学生端 5 + 企业端 4 + 管理端 2） | 全部正常渲染，0 个 `/api` 请求失败、0 个 JS 异常 |
| 06 小程序 | 开发者工具打开项目 → 登录 / 首页 / 学习 / 统计 | 4 个页面渲染正常，跳转与进度条工作；修掉废弃 API + 基础库固定 3.15.0 后控制台 **0 错误**，见 `projects/06-word-memo-miniprogram/docs/` |
| 06 静态校验 | `node tools/check-miniprogram.js .` | 49 项通过、0 失败（页面完整性 / JSON / JS 语法 / WXML 配对 / 188 条词库 / 记忆算法 17 项断言） |
| 08 网页 | 用 Chrome 打开 `index.html` 截图 | 3 张截图，无失败请求；26 张照片引用全部命中磁盘 |

### 04 的完整交叉验证结果

4 模型 × 3 种子（TabPFN 只有 1 个种子，数据来自原实验的完整运行）：

| 模型 | 种子数 | 准确率 | AUC | 本机总耗时 |
| --- | --- | --- | --- | --- |
| lightgbm | 3 | **0.8157** (±0.0010) | 0.9046 | 3.2 s |
| tabpfn | 1 | 0.8163 | **0.9063** | 63 min |
| mlp | 3 | 0.7995 (±0.0039) | 0.8872 | 31 s |
| logreg | 3 | 0.7934 (±0.0022) | 0.8620 | 1.2 s |
| knn | 3 | 0.7783 (±0.0017) | 0.8594 | 1.4 s |

结论：调好参的 LightGBM 和 TabPFN 几乎打平（差 0.0006），而 TabPFN 单次推理的成本高三个数量级——这个对比正是报告里的核心论点。

## 这一轮修掉的问题

都是「原目录能跑、换地方就不行」或「根本跑不通」的：

1. **01**：`data/` 里的 14 MB npz 不进仓库，README 里写清了首次运行的两个数据获取脚本。
2. **03**：脚本里 6 个 `↔`（U+2194）和 2 个 `²`（U+00B2）在 GBK 控制台上抛 `UnicodeEncodeError`，原样跑必崩。已换成 ASCII，并在文件头加了 stdout UTF-8 兜底。
3. **04**：`raw/` 里原本有 4 份逐字节相同的镜像数据（A/B/HF1/HF2），只保留了一份；TabPFN 改为可选，不装也能跑其余四类模型。
4. **05**：
   - `application.yml` 里有明文的远程 MySQL 密码和阿里云 OSS AccessKey，全部改为环境变量、默认值指向本地 compose；
   - `student_skill` / `student_experience` 实体有 `fileId` 字段但建表语句没有这一列，`/api/student/skills/by-student` 直接 500——补列；
   - `company_draft` 表整个缺失，但 `CompanyController` 和 `AdminReviewController` 都在用——补建表；
   - `schema.sql` 在容器里初始化时没声明字符集，CHECK 约束里的中文被当成 latin1，导致任何中文取值都通不过——文件头加 `SET NAMES utf8mb4`；
   - 删掉 59 MB 的 vite 错误日志和 `node_modules` / `target`。
5. **06**：微信开发者工具的登录态已过期，CLI 直连报 `需要重新登录`；最终用**测试号**（`touristappid`）在临时副本里打开——只改 `project.config.json` 的 `appid` 一个字段，其余 49 个代码文件与仓库逐字节相同（逐文件 MD5 比对）。截图时为了直接进首页，临时把 `pages/index/index` 调到 `app.json` 首位，仓库里的版本仍是登录页在前。
6. **07**：补了 `run.bat`；截图脚本改成直接渲染窗口到 PNG，绕开 DPI 缩放导致的屏幕拷贝错位。
7. **08**：
   - 图片路径全是 `C:\Users\...\Desktop\源代码\photos\...` 绝对路径，换机器必裂——全部改相对路径；
   - 5 张图指向 `picsum.photos`，该站本机不可达——换成本地文件（实景照片裁剪 + 生成的字母头像）；
   - 26 张 PNG 共 19.3 MB，转 JPEG 后 4.8 MB。

## 没做到的事

- **06 的真机 / 真实 AppID 验证**：截图用的是测试号，没有在真实 AppID 下验证过上传与发布流程；TTS 发音依赖有道词典接口，真机需要配合法域名，模拟器里没有实际听到声音。
- **05 的简历 PDF 生成**：页面和接口都在，但没验证「点生成 → Playwright 打印 PDF」这条路径（首次使用要下载约 150 MB 的 Chromium）。
- **04 的 TabPFN 没有重跑**：上表里 TabPFN 的数字来自原实验的完整运行（63 分钟），本轮只重跑了其余四个模型。
