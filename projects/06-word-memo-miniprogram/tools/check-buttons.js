/**
 * 按钮与交互的离线验证：不依赖开发者工具。
 *
 * 做三件事：
 *   1. 静态核对：每个 WXML 里的 bind / catch 事件绑定，处理函数在页面或组件 JS 里是否真的存在；
 *   2. 导航核对：navigateTo 的目标不能是 tabBar 页，switchTab 的目标必须是 tabBar 页；
 *   3. 运行时核对：用假的 wx 环境加载每个页面，逐个触发按钮/输入，记录 setData、跳转、
 *      Toast、存储写入，并对关键数据（单词状态、复习次数、统计值）做断言。
 *
 * 用法：node tools/check-buttons.js [项目目录]
 * 退出码 0 表示全部通过。
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(process.argv[2] || path.join(__dirname, '..'));

// ---------------------------------------------------------------- 假 wx 环境
const store = new Map();
const calls = { nav: [], toast: [], modal: [], storage: [], vibrate: 0 };
let now = 0;
let timers = [];
let timerSeq = 0;

function clone(v) {
  return v === undefined ? v : JSON.parse(JSON.stringify(v));
}

global.setTimeout = (fn, ms) => {
  const id = ++timerSeq;
  timers.push({ id, at: now + (ms || 0), fn });
  return id;
};
global.clearTimeout = (id) => {
  timers = timers.filter((t) => t.id !== id);
};

function flush(ms) {
  const target = now + (ms === undefined ? 100000 : ms);
  let guard = 0;
  for (;;) {
    timers.sort((a, b) => a.at - b.at);
    if (!timers.length || timers[0].at > target) break;
    const t = timers.shift();
    now = t.at;
    t.fn();
    if (++guard > 500) throw new Error('定时器死循环');
  }
}

global.wx = {
  getStorageSync: (k) => (store.has(k) ? clone(store.get(k)) : ''),
  setStorageSync: (k, v) => {
    store.set(k, clone(v));
    calls.storage.push(k);
  },
  removeStorageSync: (k) => store.delete(k),
  clearStorageSync: () => {
    store.clear();
    calls.storage.push('*clear*');
  },
  showToast: (o) => calls.toast.push(o),
  showModal: (o) => {
    calls.modal.push(o);
    if (o.success) o.success({ confirm: true, cancel: false });
  },
  switchTab: (o) => calls.nav.push({ type: 'switchTab', url: o.url }),
  navigateTo: (o) => calls.nav.push({ type: 'navigateTo', url: o.url }),
  navigateBack: () => calls.nav.push({ type: 'navigateBack' }),
  reLaunch: (o) => calls.nav.push({ type: 'reLaunch', url: o.url }),
  createInnerAudioContext: () => ({
    src: '',
    play() {},
    stop() {},
    destroy() {},
    onEnded(cb) {
      this._ended = cb;
    },
    onError(cb) {
      this._error = cb;
    },
  }),
  vibrateShort: () => (calls.vibrate += 1),
  getWindowInfo: () => ({ windowWidth: 390, safeArea: { top: 47 }, statusBarHeight: 47 }),
  getDeviceInfo: () => ({ platform: 'devtools' }),
  getSystemInfoSync: () => ({
    windowWidth: 390,
    platform: 'devtools',
    statusBarHeight: 47,
    safeArea: { top: 47 },
  }),
  getMenuButtonBoundingClientRect: () => ({ left: 290 }),
  nextTick: (fn) => fn(),
  setNavigationBarTitle() {},
  setNavigationBarColor() {},
  hideHomeButton() {},
};

global.getCurrentPages = () => [];
global.getApp = () => ({ globalData: {} });
global.App = () => {};

// ---------------------------------------------------------------- 加载页面
function setPath(obj, key, value) {
  const parts = [];
  const re = /([^.[\]]+)|\[(\d+)\]/g;
  let m;
  while ((m = re.exec(key))) parts.push(m[2] !== undefined ? Number(m[2]) : m[1]);
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const p = parts[i];
    const nextIsIndex = typeof parts[i + 1] === 'number';
    if (cur[p] === undefined || cur[p] === null) cur[p] = nextIsIndex ? [] : {};
    cur = cur[p];
  }
  cur[parts[parts.length - 1]] = value;
}

function loadModule(fileOrRel) {
  const file = path.isAbsolute(fileOrRel) ? fileOrRel : path.join(ROOT, fileOrRel);
  delete require.cache[require.resolve(file)];
  let captured = null;
  global.Page = (cfg) => {
    captured = cfg;
  };
  global.Component = (cfg) => {
    captured = cfg;
  };
  require(file);
  return captured;
}

function instantiate(cfg, kind) {
  const inst = Object.create(null);
  const source = kind === 'component' ? cfg.methods || {} : cfg;
  for (const [k, v] of Object.entries(source)) {
    if (typeof v === 'function') inst[k] = v;
  }
  inst.data = clone((kind === 'component' ? cfg.data : cfg.data) || {});
  if (kind === 'component' && cfg.properties) {
    for (const [k, def] of Object.entries(cfg.properties)) {
      inst.data[k] = def.value;
    }
  }
  inst._setCount = 0;
  inst._changed = [];
  inst.setData = function (patch, cb) {
    for (const [k, v] of Object.entries(patch)) {
      setPath(this.data, k, v);
      this._changed.push(k);
    }
    this._setCount += 1;
    if (cb) cb();
  };
  inst.triggerEvent = () => {};
  inst.selectComponent = () => null;
  return inst;
}

// ---------------------------------------------------------------- 静态扫描
const APP = JSON.parse(fs.readFileSync(path.join(ROOT, 'app.json'), 'utf8'));
const TAB_PAGES = new Set((APP.tabBar.list || []).map((t) => '/' + t.pagePath));

function wxmlFiles(dir) {
  const out = [];
  for (const name of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, name.name);
    if (name.isDirectory()) out.push(...wxmlFiles(p));
    else if (name.name.endsWith('.wxml')) out.push(p);
  }
  return out;
}

/** 从 WXML 里抽出 [标签名, {属性: 值}] */
function parseTags(text) {
  const clean = text.replace(/<!--[\s\S]*?-->/g, '');
  const tags = [];
  const tagRe = /<([a-zA-Z][\w-]*)((?:\s+[^<>]*?)?)\/?>/g;
  let m;
  while ((m = tagRe.exec(clean))) {
    const attrs = {};
    const attrRe = /([:\w-]+)="([^"]*)"/g;
    let a;
    while ((a = attrRe.exec(m[2]))) attrs[a[1]] = a[2];
    tags.push({ tag: m[1], attrs });
  }
  return tags;
}

const staticRows = [];
const handlerBindings = []; // {file, tag, attr, handler}

for (const file of wxmlFiles(path.join(ROOT, 'pages')).concat(wxmlFiles(path.join(ROOT, 'components')))) {
  const rel = path.relative(ROOT, file).replace(/\\/g, '/');
  const jsFile = file.replace(/\.wxml$/, '.js');
  const isComponent = rel.startsWith('components/');
  const cfg = loadModule(jsFile);
  const methods = new Set(
    Object.keys(isComponent ? (cfg && cfg.methods) || {} : cfg || {}).filter(
      (k) => typeof (isComponent ? cfg.methods[k] : cfg[k]) === 'function'
    )
  );
  for (const { tag, attrs } of parseTags(fs.readFileSync(file, 'utf8'))) {
    for (const [attr, value] of Object.entries(attrs)) {
      if (!/^(bind|catch)/.test(attr)) continue;
      handlerBindings.push({ file: rel, tag, attr, handler: value });
      if (!methods.has(value)) {
        staticRows.push({ file: rel, tag, attr, handler: value, ok: false, why: 'JS 里没有这个方法' });
      } else {
        staticRows.push({ file: rel, tag, attr, handler: value, ok: true, why: '' });
      }
    }
  }
}

// 导航目标核对
const navRows = [];
function walkJs(dir) {
  const out = [];
  for (const name of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, name.name);
    if (name.isDirectory()) out.push(...walkJs(p));
    else if (name.name.endsWith('.js')) out.push(p);
  }
  return out;
}
for (const file of walkJs(ROOT).filter((f) => !f.includes('node_modules'))) {
  const src = fs.readFileSync(file, 'utf8');
  const rel = path.relative(ROOT, file).replace(/\\/g, '/');
  const re = /wx\.(navigateTo|switchTab|reLaunch)\(\{\s*url:\s*['"]([^'"]+)['"]/g;
  let m;
  while ((m = re.exec(src))) {
    const api = m[1];
    const url = m[2].split('?')[0];
    let ok = true;
    let why = '';
    if (api === 'navigateTo' && TAB_PAGES.has(url)) {
      ok = false;
      why = 'tabBar 页面不能用 navigateTo（会静默失败）';
    }
    if (api === 'switchTab' && !TAB_PAGES.has(url)) {
      ok = false;
      why = 'switchTab 只能跳 tabBar 页';
    }
    navRows.push({ file: rel, api, url, ok, why });
  }
}

// ---------------------------------------------------------------- 运行时场景
const results = [];
function freshStore() {
  store.clear();
  timers = [];
  now = 0;
  calls.nav.length = 0;
  calls.toast.length = 0;
  calls.modal.length = 0;
  calls.storage.length = 0;
}
function seedWords(count) {
  const { cet4Words } = require(path.join(ROOT, 'utils/words.js'));
  const words = cet4Words.slice(0, count).map((w, i) => ({
    ...w,
    id: 'w' + i,
    status: 0,
    reviewCount: 0,
    nextReviewDate: '2020-01-01',
    addedDate: '2020-01-01',
  }));
  store.set('words', words);
  store.set('settings', { dailyGoal: 20, autoPlay: true, showPhonetic: true, studyMode: 'flashcard' });
  store.set('stats', {
    totalLearned: 12,
    totalMastered: 3,
    consecutiveDays: 4,
    lastStudyDate: '2026-11-19',
    dailyStats: { '2026-11-19': { studied: 20, learned: 12, duration: 3000 } },
    totalStudyTime: 5400,
  });
  return words;
}

function ev(dataset, detail) {
  return { type: 'tap', currentTarget: { dataset: dataset || {} }, target: { dataset: dataset || {} }, detail: detail || {} };
}

function run(name, pageRel, opts) {
  const row = { name, page: pageRel, steps: [], failures: [], warnings: [], asserts: [] };
  try {
    freshStore();
    const seeded = seedWords(opts.seed || 30);
    const cfg = loadModule(pageRel + '.js');
    const inst = instantiate(cfg, pageRel.startsWith('components/') ? 'component' : 'page');
    const setupNav = () => {
      calls.nav.length = 0;
      calls.toast.length = 0;
      calls.modal.length = 0;
      calls.storage.length = 0;
      inst._changed = [];
    };
    const ctx = { inst, seeded, cfg, setupNav, row };

    if (inst.onLoad) inst.onLoad(opts.options || {});
    flush();
    if (inst.onShow) inst.onShow();
    flush();
    if (opts.before) opts.before(ctx);
    setupNav();

    for (const step of opts.steps) {
      const before = JSON.stringify(inst.data);
      let error = null;
      try {
        step.call(inst, ctx);
      } catch (e) {
        error = e;
      }
      flush();
      const changed = inst._changed.slice();
      inst._changed = [];
      const dataChanged = JSON.stringify(inst.data) !== before || changed.length > 0;
      const nav = calls.nav.splice(0);
      const toast = calls.toast.splice(0);
      const modal = calls.modal.splice(0);
      const storage = calls.storage.splice(0);
      const effect = nav.length || toast.length || modal.length || storage.length || dataChanged;
      row.steps.push({
        name: step.name,
        error: error ? error.message : '',
        changed: changed.length,
        dataChanged,
        nav: nav.map((n) => n.type + ' ' + (n.url || '')),
        toast: toast.map((t) => t.title),
        modal: modal.map((m) => m.title),
        storage: storage.slice(0, 3),
        effect: !!effect,
      });
      if (error) row.failures.push(`${step.name} 抛异常：${error.message}`);
      else if (!effect) row.warnings.push(`${step.name} 没有任何副作用`);
      if (step.check) {
        let msg = '';
        try {
          msg = step.check({ inst, store, seeded, calls: { nav, toast, modal, storage } }) || '';
        } catch (e) {
          msg = '断言执行失败：' + e.message;
        }
        if (msg) row.failures.push(`${step.name} 断言失败：${msg}`);
        else row.asserts.push(step.name);
      }
    }
  } catch (e) {
    row.failures.push('装载/执行失败：' + e.message);
  }
  results.push(row);
}

// ---- login
run('登录页', 'pages/login/login', {
  options: {},
  before: (ctx) => {
    ctx.inst.onNicknameInput(ev({}, { value: '小明' }));
  },
  steps: [
    { name: '填写昵称', call: (inst) => inst.onNicknameInput(ev({}, { value: '小明' })) },
    { name: '选择头像', call: (inst) => inst.onChooseAvatar(ev({}, { avatarUrl: 'wxfile://a.png' })) },
    { name: '未填昵称点微信登录', call: (inst) => { inst.data.nickname = ''; inst.onWechatLogin(); } },
    { name: '微信授权登录', call: (inst) => { inst.data.nickname = '小明'; inst.onWechatLogin(); }, check: ({ store }) => (store.get('is_logged_in') === true ? '' : '登录态没写进存储') },
    { name: '快速登录', call: (inst) => { inst.data.nickname = '小明'; inst.onPhoneLogin(); } },
    { name: '暂不登录先体验', call: (inst) => inst.onSkipLogin() },
  ],
});

// ---- index
run('首页', 'pages/index/index', {
  seed: 30,
  steps: [
    {
      name: '刷新今日数据',
      call: (inst) => inst.refreshData(),
      check: ({ inst }) => {
        if (inst.data.newCount !== 30) return `新词 ${inst.data.newCount}，应为 30`;
        if (inst.data.todayGoal !== 20) return `今日目标 ${inst.data.todayGoal}`;
        if (inst.data.progressPercent !== 0) return `进度 ${inst.data.progressPercent}%`;
        return '';
      },
    },
    { name: '学习新词', call: (inst) => inst.goNewWords(), check: ({ store }) => (store.get('settings').pendingStudyMode === 'new' ? '' : '没有留下 pendingStudyMode 标记') },
    { name: '复习旧词', call: (inst) => inst.goReview() },
    { name: '开始学习', call: (inst) => inst.goStudy() },
  ],
});

// ---- study 三种模式
run('学习页·闪卡', 'pages/study/study', {
  seed: 30,
  options: {},
  steps: [
    { name: '显示答案', call: (inst) => inst.onShowAnswer(), check: ({ inst }) => (inst.data.showAnswer === true ? '' : 'showAnswer 没置位') },
    { name: '发音', call: (inst) => { inst.playAudio(); const c = inst.getAudioContext(); if (c._error) c._error(new Error('x')); }, check: ({ inst }) => (inst.data.isPlaying === false ? '' : '播放失败后 isPlaying 没复位') },
    {
      name: '认识',
      call: (inst) => inst.onKnow(),
      check: ({ inst, store }) => {
        const learned = store.get('words').filter((w) => w.status === 1).length;
        if (learned !== 1) return `存储里状态变为学习中的有 ${learned} 个，应为 1`;
        if (inst.data.studiedCount !== 1) return `studiedCount=${inst.data.studiedCount}`;
        return '';
      },
    },
    {
      name: '不认识',
      call: (inst) => inst.onUnknown(),
      check: ({ inst }) => (inst.data.studiedCount === 2 ? '' : `studiedCount=${inst.data.studiedCount}`),
    },
    { name: '返回首页', call: (inst) => inst.goBack() },
  ],
});

run('学习页·拼写', 'pages/study/study', {
  seed: 30,
  options: { mode: 'spelling' },
  steps: [
    { name: '输入拼写', call: (inst) => inst.onSpellingInput(ev({}, { value: 'abandon' })), check: ({ inst }) => (inst.data.spellingInput === 'abandon' ? '' : '没接收输入') },
    {
      name: '拼对确认',
      call: (inst) => { inst.data.spellingInput = inst.data.currentWord.word; inst.checkSpelling(); },
      check: ({ inst }) => {
        if (inst.data.currentIndex !== 1) return `没有自动进入下一题（currentIndex=${inst.data.currentIndex}）`;
        if (inst.data.spellingResult !== null) return `spellingResult=${inst.data.spellingResult}`;
        return '';
      },
    },
    { name: '拼错确认', call: (inst) => { inst.data.spellingInput = 'zzz'; inst.checkSpelling(); }, check: ({ inst }) => (inst.data.spellingResult === 'wrong' ? '' : '答错没有标记 wrong') },
    { name: '答错后继续', call: (inst) => inst.onSpellingContinue() },
  ],
});

run('学习页·听音', 'pages/study/study', {
  seed: 30,
  options: { mode: 'listening' },
  steps: [
    { name: '播放发音', call: (inst) => inst.playAudio() },
    { name: '显示答案', call: (inst) => inst.onListeningShowAnswer(), check: ({ inst }) => (inst.data.showAnswer === true ? '' : 'showAnswer 没置位') },
    { name: '认识', call: (inst) => inst.onListeningCorrect(), check: ({ inst }) => (inst.data.currentIndex === 1 ? '' : `没有进入下一题（currentIndex=${inst.data.currentIndex}）`) },
    { name: '不认识', call: (inst) => inst.onListeningWrong(), check: ({ inst }) => (inst.data.spellingResult === 'wrong' ? '' : '没有标记 wrong') },
    { name: '继续下一个', call: (inst) => inst.onListeningContinue() },
  ],
});

run('学习页·首页进新词模式', 'pages/study/study', {
  seed: 30,
  options: {},
  before: (ctx) => {
    const settings = { ...store.get('settings'), pendingStudyMode: 'new' };
    store.set('settings', settings);
  },
  steps: [
    {
      name: 'onShow 接管待处理模式',
      call: (inst) => inst.onShow(),
      check: ({ inst, store }) => {
        if (inst.data.mode !== 'flashcard') return `mode=${inst.data.mode}（应为 flashcard，否则界面空白）`;
        if (store.get('settings').pendingStudyMode) return '一次性标记没有清掉';
        if (!inst.data.studyWords.length) return '新词模式没有装载单词';
        if (inst.data.studyWords.some((w) => w.status !== 0)) return '装载了非新词';
        return '';
      },
    },
  ],
});

// ---- wordlist
run('词库页', 'pages/wordlist/wordlist', {
  seed: 30,
  steps: [
    {
      name: '搜索 abandon',
      call: (inst) => inst.onSearch(ev({}, { value: 'abandon' })),
      check: ({ inst }) => {
        const list = inst.data.words;
        if (!list.length) return '搜索后 0 条';
        const bad = list.filter((w) => !(w.word + w.meaning).toLowerCase().includes('abandon'));
        return bad.length ? `${bad.length} 条不含关键词` : '';
      },
    },
    {
      name: '清空搜索',
      call: (inst) => inst.onClearSearch(),
      check: ({ inst }) => (inst.data.words.length === 30 ? '' : `恢复到 ${inst.data.words.length} 条，应为 30`),
    },
    {
      name: '展开单词',
      call: (inst) => inst.onWordTap(ev({ word: { id: inst.data.words[0].id }, expanded: false })),
      check: ({ inst }) => (inst.data.words[0].expanded === true ? '' : '第一条没有展开'),
    },
    {
      name: '筛选已掌握',
      call: (inst) => inst.onFilterChange(ev({ type: 'mastered' })),
      check: ({ inst }) => (inst.data.words.length === 0 ? '' : `已掌握应为 0 条，实际 ${inst.data.words.length}`),
    },
    {
      name: '切回全部',
      call: (inst) => inst.onFilterChange(ev({ type: 'all' })),
      check: ({ inst }) => (inst.data.words.length === 30 ? '' : `应为 30 条，实际 ${inst.data.words.length}`),
    },
    {
      name: '删除单词',
      call: (inst) => inst.onDeleteWord(ev({ id: inst.data.words[0].id })),
      check: ({ store }) => (store.get('words').length === 29 ? '' : `删除后剩 ${store.get('words').length} 条`),
    },
    { name: '添加单词入口', call: (inst) => inst.onAddWord() },
  ],
});

// ---- review
run('复习页', 'pages/review/review', {
  seed: 30,
  before: (ctx) => {
    const words = store.get('words');
    words.forEach((w, i) => {
      w.status = 1;
      w.reviewCount = 2;
      w.nextReviewDate = '2020-01-01';
    });
    store.set('words', words);
    ctx.inst.loadReviewWords();
  },
  steps: [
    { name: '显示答案', call: (inst) => inst.onShowAnswer(), check: ({ inst }) => (inst.data.showAnswer === true ? '' : 'showAnswer 没置位') },
    { name: '播放发音', call: (inst) => inst.playAudio() },
    {
      name: '记住了',
      call: (inst) => inst.onRemember(),
      check: ({ inst, store }) => {
        if (inst.data.reviewCount !== 1) return `reviewCount=${inst.data.reviewCount}`;
        const first = store.get('words')[0];
        return first.reviewCount === 3 ? '' : `存储里 reviewCount=${first.reviewCount}，应为 3`;
      },
    },
    { name: '忘了', call: (inst) => inst.onForget(), check: ({ inst }) => (inst.data.reviewCount === 2 ? '' : `reviewCount=${inst.data.reviewCount}`) },
    {
      name: '退出复习',
      call: (inst) => inst.goBack(),
      check: ({ store }) => {
        const today = require(path.join(ROOT, 'utils/memory.js')).getTodayStr();
        const day = (store.get('stats').dailyStats || {})[today] || {};
        return (day.studied || 0) === 0 ? '' : `还没卸载就记了 studied=${day.studied}`;
      },
    },
    {
      name: '卸载页面',
      call: (inst) => inst.onUnload(),
      check: ({ store }) => {
        const today = require(path.join(ROOT, 'utils/memory.js')).getTodayStr();
        const day = (store.get('stats').dailyStats || {})[today] || {};
        return (day.studied || 0) === 2 ? '' : `卸载后 studied=${day.studied || 0}，应为 2（只记一次）`;
      },
    },
  ],
});

// ---- stats
run('统计页', 'pages/stats/stats', {
  seed: 30,
  steps: [
    {
      name: '重新加载统计',
      call: (inst) => inst.loadStats(),
      check: ({ inst }) => {
        if (inst.data.weekData.length !== 7) return `weekData ${inst.data.weekData.length} 天`;
        if (inst.data.statusData.length !== 3) return `statusData ${inst.data.statusData.length} 项`;
        if (inst.data.totalStudyTime !== '1小时30分钟') return `累计时长显示 ${inst.data.totalStudyTime}`;
        return '';
      },
    },
  ],
});

// ---- profile
run('我的页', 'pages/profile/profile', {
  seed: 30,
  steps: [
    { name: '改每日目标', call: (inst) => inst.onDailyGoalChange(ev({}, { value: '35' })), check: ({ store }) => (store.get('settings').dailyGoal === 35 ? '' : `dailyGoal=${store.get('settings').dailyGoal}`) },
    { name: '关自动播放', call: (inst) => inst.onSwitchChange(ev({ field: 'autoPlay' }, { value: false })), check: ({ store }) => (store.get('settings').autoPlay === false ? '' : '开关没写进存储') },
    { name: '切学习模式', call: (inst) => inst.onModeChange(ev({ mode: 'spelling' })), check: ({ store }) => (store.get('settings').studyMode === 'spelling' ? '' : '模式没写进存储') },
    { name: '重置数据', call: (inst) => inst.onResetData(), check: ({ store }) => {
        const words = (store.get('words') || []).length;
        const stats = store.get('stats') || {};
        if (words !== 188) return `重置后词库 ${words} 条，应为重新初始化的 188 条`;
        if (stats.totalLearned !== 0) return `重置后 totalLearned=${stats.totalLearned}`;
        return '';
      } },
    { name: '关于', call: (inst) => inst.onAbout() },
    { name: '去登录', call: (inst) => inst.goLogin() },
    { name: '退出登录', call: (inst) => inst.onLogout(), check: ({ store }) => (store.get('is_logged_in') === false ? '' : '退出后仍是登录态') },
  ],
});

// ---- addword
run('添加单词页', 'pages/addword/addword', {
  seed: 30,
  steps: [
    { name: '输入单词', call: (inst) => inst.onNewWordInput(ev({ field: 'word' }, { value: 'foo' })), check: ({ inst }) => (inst.data.newWord.word === 'foo' ? '' : '输入没落到 newWord.word') },
    { name: '空表单提交', call: (inst) => inst.onAddWord(), check: ({ store }) => (store.get('words').length === 30 ? '' : '空表单写入了词库') },
    { name: '填齐提交', call: (inst) => { inst.data.newWord = { word: 'foo', meaning: '测试' }; inst.onAddWord(); }, check: ({ store }) => (store.get('words').length === 31 ? '' : `词库 ${store.get('words').length} 条，应为 31`) },
    { name: '取消', call: (inst) => inst.onCancelAdd() },
  ],
});

// ---- components
run('底部 tabBar', 'components/tab-bar/tab-bar', {
  steps: [0, 1, 2, 3, 4].map((i) => ({
    name: '点击第 ' + (i + 1) + ' 个 tab',
    call: (inst) => inst.onTabTap(ev({ index: String(i) })),
  })),
});
run('自定义导航栏', 'components/navigation-bar/navigation-bar', {
  steps: [
    { name: '返回（栈里只有一页）', call: (inst) => inst.back() },
  ],
});

// ---------------------------------------------------------------- 输出
const badStatic = staticRows.filter((r) => !r.ok);
const badNav = navRows.filter((r) => !r.ok);
const failed = results.filter((r) => r.failures.length);
const warned = results.filter((r) => !r.failures.length && r.warnings.length);

console.log('== 静态：WXML 绑定的处理函数 ==');
console.log(`共 ${staticRows.length} 处绑定，${badStatic.length} 处找不到方法`);
for (const r of badStatic) console.log(`  FAIL ${r.file} <${r.tag}> ${r.attr}="${r.handler}"：${r.why}`);

console.log('\n== 导航目标 ==');
for (const r of navRows) console.log(`  ${r.ok ? 'PASS' : 'FAIL'} ${r.file} ${r.api} ${r.url}${r.why ? '  // ' + r.why : ''}`);

console.log('\n== 运行时：按钮/输入逐项触发 ==');
for (const r of results) {
  const total = r.steps.length;
  const noEffect = r.steps.filter((s) => !s.effect && !s.error).length;
  const errored = r.steps.filter((s) => s.error).length;
  console.log(`\n[${r.failures.length ? 'FAIL' : noEffect ? 'WARN' : 'PASS'}] ${r.name}（${total} 步，断言 ${r.asserts.length}，无副作用 ${noEffect}，抛错 ${errored}）`);
  for (const s of r.steps) {
    const bits = [];
    if (s.error) bits.push('抛错:' + s.error);
    if (s.nav.length) bits.push('跳转:' + s.nav.join(','));
    if (s.toast.length) bits.push('Toast:' + s.toast.join(','));
    if (s.modal.length) bits.push('弹窗:' + s.modal.join(','));
    if (s.storage.length) bits.push('写存储:' + s.storage.join(','));
    if (s.dataChanged) bits.push('setData ' + s.changed + ' 处');
    if (!s.effect && !s.error) bits.push('★ 无任何副作用');
    console.log(`   ${s.error || (!s.effect) ? '✗' : '✓'} ${s.name}  ${bits.join(' | ')}`);
  }
  for (const f of r.failures) console.log('   FAIL ' + f);
}

const summary = {
  staticBindings: staticRows.length,
  staticMissing: badStatic.length,
  navInvalid: badNav.length,
  pagesRun: results.length,
  pagesWithFailure: failed.length,
  pagesWithNoEffect: warned.length,
};
console.log('\n== 汇总 ==');
console.log(JSON.stringify(summary));
process.exit(badStatic.length || badNav.length || failed.length ? 1 : 0);
