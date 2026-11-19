# 校园招聘智能简历平台后端骨架

基于三份需求/模块/数据库文档创建的 Spring Boot 后端骨架，包含：

- Spring Boot Web MVC
- MyBatis-Plus
- MySQL 8.0 表结构
- 阿里云 OSS 文件上传基础能力
- 学生端、企业端、管理端、公共基础模块的实体、Mapper、Service、Controller

## 启动前准备

1. 创建数据库并执行 `src/main/resources/db/schema.sql`。
2. 修改 `src/main/resources/application.yml` 中的数据库账号密码。
3. 如需启用 OSS 上传，配置环境变量：

```bash
ALIYUN_OSS_ENDPOINT=
ALIYUN_OSS_ACCESS_KEY_ID=
ALIYUN_OSS_ACCESS_KEY_SECRET=
ALIYUN_OSS_BUCKET_NAME=
ALIYUN_OSS_URL_PREFIX=
```

## 本地启动

```bash
mvn spring-boot:run
```
