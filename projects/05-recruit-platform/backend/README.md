# 后端（Spring Boot 3.3 / Java 17）

完整的项目说明、架构与演示账号见上一级目录的 [README](../README.md)。这个文件只记后端单独启动的步骤。

## 启动

前提：MySQL 已就绪（在项目根目录执行 `docker compose up -d`，会建表并导入演示数据）。

```bash
# 首次运行会下载 Maven 与依赖，约 5 分钟
./mvnw -s settings.xml spring-boot:run        # Linux / macOS
mvnw.cmd -s settings.xml spring-boot:run      # Windows

# 或用 wrapper 打好的 jar
./mvnw -s settings.xml -DskipTests package
java -jar target/resume-platform-backend-0.0.1-SNAPSHOT.jar
```

`-s settings.xml` 让 Maven 走阿里云镜像，国内网络下明显更快；网络通畅时可以去掉。

## 配置

`src/main/resources/application.yml` 里没有任何明文凭据，全部走环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DB_URL` | `jdbc:mysql://localhost:3307/recruit_resume?...` | 对应 compose 映射到宿主机的 3307 |
| `DB_USERNAME` | `recruit` | |
| `DB_PASSWORD` | `recruit_pwd_2026` | |
| `JWT_SECRET` | 一段开发用默认值 | 上线必须改 |
| `ALIYUN_OSS_*` | 空 | 全空时上传走本地磁盘，不需要云账号 |

## 数据库

`src/main/resources/db/` 下两个脚本：

- `schema.sql`：13 张表（含外键、CHECK 约束、索引）。文件开头有 `SET NAMES utf8mb4`，容器里初始化时缺了这一句会让 CHECK 约束里的中文变成 latin1，之后任何中文取值都通不过。
- `02-seed.sql`：三个演示账号（`student01` / `company01` / `admin`，密码统一 `Demo@1234`）、学生档案与技能、一家演示企业、三个已发布岗位。

## 测试

```bash
./mvnw -s settings.xml test
```

`src/test/java` 下有 10 个测试类，覆盖认证、企业、岗位、投递、文件与简历生成。
