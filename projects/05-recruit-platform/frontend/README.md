# 前端（Vue 3 + TypeScript + Element Plus）

完整说明见上级目录的 [README](../README.md)。

## 启动

```bash
npm install
npm run dev        # http://localhost:5173
```

后端要同时跑在 `localhost:8080`，`vite.config.ts` 里把 `/api` 代理过去了。

## 构建

```bash
npm run build      # vue-tsc 类型检查 + vite 打包
npm run preview    # 预览构建产物
```

## 结构

```
src/
├── api/          按模块拆的请求封装，axios 实例在 http.ts（拦截器注入 JWT、统一解 Result 包装）
├── views/
│   ├── auth/     LoginView / RegisterView
│   ├── student/  职位大厅、简历、个人信息、技能、经历、投递、消息
│   ├── company/  企业看板、企业资料、岗位、投递、消息
│   └── admin/    审核、用户、简历模板
├── layouts/      DashboardLayout（侧边栏 + 顶栏）
├── stores/       Pinia 会话（token 持久化到 localStorage 的 auth 键）
├── router/       路由守卫：未登录跳 /login，登录后按角色分流
└── types/        接口类型定义
```

## 测试

```bash
npm test
```

`tests/` 下 4 个 `.mjs`：页面结构、设计系统（颜色与间距约定）、投递页交互、职位详情面板。
