# 单词背诵助手（微信小程序）

基于艾宾浩斯遗忘曲线的背单词小程序：8 个页面、188 个 CET-4 词条、三种学习模式，带复习调度与学习统计。

> 运行需要一个微信开发者工具。这个仓库里能做的是静态校验和核心算法单测（见下方「验证」），模拟器截图需要在开发者工具里跑。

## 功能

| 页面 | 做什么 |
| --- | --- |
| `index` | 今日任务：待学 / 待复习数量、每日目标进度、连续打卡天数 |
| `study` | 学习主界面，三种模式：闪卡（看词想义）、拼写（看义拼词）、听音（TTS 发音辨词） |
| `review` | 到期复习队列，按 `nextReviewDate` 排序 |
| `wordlist` | 词库浏览、筛选（新词 / 学习中 / 已掌握）、搜索 |
| `addword` | 手动添加生词 |
| `stats` | 学习统计：每日学习量、掌握率、累计时长 |
| `profile` | 个人资料、每日目标设置、清空数据 |
| `login` | 登录页（本地模拟，不接后端） |

## 记忆调度

`utils/memory.js` 是纯函数模块，不依赖任何 `wx.*` API：

```js
const REVIEW_INTERVALS = [1, 2, 4, 7, 15, 30, 60];   // 天
```

- 每次答完，`getNextReviewDate(上次复习日期, reviewCount)` 按档位推进；`reviewCount` 超出档位时封顶在 60 天。
- `needsReview(word)`：新词、学习中、或 `nextReviewDate <= 今天` 的都算待复习。
- `calculateMemoryScore(反应时间, 是否正确)`：答错 0 分；答对按反应时间给 5/4/3/2/1 分，用来调整下一次间隔。

数据落在 `wx.setStorageSync`，`utils/storage.js` 做了懒加载——词库 27 KB，不在启动时一次性塞进内存。

## 怎么跑

1. 安装[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 「导入项目」→ 选本目录 → AppID 选「测试号」或填自己的
3. 编译后从 `pages/login` 进入，任意用户名密码即可（本地模拟登录）

`project.config.json` 里的 `appid` 是原开发用的，导入时会被替换成你自己的。

## 验证

在没有开发者工具的机器上，用仓库里的脚本做静态校验：

```bash
node tools/check-miniprogram.js .
```

覆盖 49 项：8 个页面的 `.js/.wxml/.json` 是否齐全、tabBar 指向的页面是否都已注册、14 个 JSON 是否可解析、16 个 JS 语法是否通过、WXML 标签是否配对、词库 188 条是否都有 `word`/`meaning`，以及记忆算法的 17 项断言（各档位间隔、封顶、三种状态的复习判定、四档评分）。

实测输出：`49 通过, 0 失败`。

## 目录

```
├── app.js / app.json / app.wxss    全局入口、页面注册、全局样式
├── components/
│   ├── navigation-bar/   自定义导航栏（navigationStyle: custom）
│   └── tab-bar/          自定义 tabBar（tabBar.custom: true）
├── pages/                8 个页面，每个 4 个文件
├── utils/
│   ├── memory.js         艾宾浩斯调度（纯函数）
│   ├── storage.js        本地存储封装
│   ├── user.js           用户会话
│   └── words.js          188 条 CET-4 词库
└── tools/check-miniprogram.js  静态校验 + 算法单测
```

## 实现上值得说的两点

- **导航栏和 tabBar 都是自定义组件**（`navigationStyle: "custom"`、`tabBar.custom: true`），为的是在真机上做到沉浸式顶部和带图标的底栏；代价是每个页面要自己处理状态栏高度，`components/navigation-bar` 里按 `wx.getSystemInfoSync().statusBarHeight` 做了适配。
- **词库懒加载**：`storage.js` 里用 `static _cet4Words = null` 缓存，第一次进词库页才 `require('./words.js')`，避免冷启动时解析 27 KB。
