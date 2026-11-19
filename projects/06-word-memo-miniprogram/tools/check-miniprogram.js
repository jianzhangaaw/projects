/**
 * 小程序静态校验 + 记忆算法单测。
 * 不依赖微信开发者工具，检查的是「代码结构是否自洽」和「核心调度算法是否正确」。
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

// require() 的相对路径是按脚本所在目录解析的，所以 ROOT 必须先转成绝对路径。
const ROOT = path.resolve(process.argv[2] || path.join(__dirname, '..'));
let pass = 0, fail = 0;
const problems = [];

function ok(name) { pass++; console.log('  PASS  ' + name); }
function bad(name, detail) { fail++; problems.push(name + ': ' + detail); console.log('  FAIL  ' + name + '  -> ' + detail); }

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

console.log('小程序静态校验  ' + ROOT);
console.log('');

// 1. app.json 与页面文件
const app = readJson(path.join(ROOT, 'app.json'));
ok('app.json 可解析，pages=' + app.pages.length);

for (const page of app.pages) {
  const base = path.join(ROOT, page);
  for (const ext of ['.js', '.wxml', '.json']) {
    if (fs.existsSync(base + ext)) ok('页面文件存在 ' + page + ext);
    else bad('页面文件缺失', page + ext);
  }
}

// 2. tabBar 引用的页面必须在 pages 里
if (app.tabBar && app.tabBar.list) {
  for (const item of app.tabBar.list) {
    if (app.pages.includes(item.pagePath)) ok('tabBar 指向已注册页面 ' + item.pagePath);
    else bad('tabBar 指向未注册页面', item.pagePath);
  }
}

// 3. 所有 json 可解析
function walk(dir, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (e.name !== 'node_modules') walk(p, out); }
    else out.push(p);
  }
  return out;
}
const all = walk(ROOT, []);
let jsonOk = 0, jsonBad = 0;
for (const p of all.filter(x => x.endsWith('.json'))) {
  try { readJson(p); jsonOk++; } catch (e) { jsonBad++; bad('JSON 解析失败', p + ' ' + e.message); }
}
if (jsonBad === 0) ok('全部 ' + jsonOk + ' 个 JSON 文件可解析');

// 4. JS 语法（node --check 只做语法检查，不执行 wx API）
let jsOk = 0, jsBad = 0;
for (const p of all.filter(x => x.endsWith('.js'))) {
  try {
    execFileSync(process.execPath, ['--check', p], { stdio: 'pipe' });
    jsOk++;
  } catch (e) {
    jsBad++;
    bad('JS 语法错误', p + ' ' + (e.stderr ? e.stderr.toString().split('\n')[0] : e.message));
  }
}
if (jsBad === 0) ok('全部 ' + jsOk + ' 个 JS 文件语法通过');

// 5. WXML 标签配对（自闭合与内置标签白名单）
const VOID = new Set(['image', 'input', 'icon', 'progress', 'checkbox', 'radio', 'slider', 'switch', 'textarea', 'import', 'include', 'wxs']);
let wxmlOk = 0, wxmlBad = 0;
for (const p of all.filter(x => x.endsWith('.wxml'))) {
  const src = fs.readFileSync(p, 'utf8').replace(/<!--[\s\S]*?-->/g, '');
  const stack = [];
  const re = /<\/?([a-zA-Z][\w-]*)((?:[^>"']|"[^"]*"|'[^']*')*?)(\/?)>/g;
  let m, broken = null;
  while ((m = re.exec(src))) {
    const [whole, tag, , selfClose] = m;
    if (whole.startsWith('</')) {
      // WXML 允许把 image / input 这类内置标签写成 <image></image>，
      // 它们本来就不入栈，遇到显式闭合直接跳过。
      if (VOID.has(tag)) continue;
      const top = stack.pop();
      if (top !== tag) { broken = '闭合标签 ' + tag + ' 与开标签 ' + top + ' 不匹配'; break; }
    } else if (!selfClose && !VOID.has(tag)) {
      stack.push(tag);
    }
  }
  if (!broken && stack.length) broken = '未闭合: ' + stack.join(',');
  if (broken) { wxmlBad++; bad('WXML 结构', p + ' ' + broken); }
  else wxmlOk++;
}
if (wxmlBad === 0) ok('全部 ' + wxmlOk + ' 个 WXML 标签配对正确');

// 6. 记忆算法单测
console.log('');
console.log('记忆算法单测');
const memory = require(path.join(ROOT, 'utils', 'memory.js'));
const INTERVALS = memory.REVIEW_INTERVALS;

function eq(name, actual, expected) {
  if (JSON.stringify(actual) === JSON.stringify(expected)) ok(name);
  else bad(name, '期望 ' + JSON.stringify(expected) + ' 实际 ' + JSON.stringify(actual));
}

eq('复习间隔是 7 档递增', INTERVALS, [1, 2, 4, 7, 15, 30, 60]);

const base = '2026-01-01';
eq('第 0 次复习 -> 次日', memory.getNextReviewDate(base, 0), '2026-01-02');
eq('第 1 次复习 -> +2 天', memory.getNextReviewDate(base, 1), '2026-01-03');
eq('第 2 次复习 -> +4 天', memory.getNextReviewDate(base, 2), '2026-01-05');
eq('第 6 次复习 -> +60 天', memory.getNextReviewDate(base, 6), '2026-03-02');
eq('超出档位不越界（封顶 60 天）', memory.getNextReviewDate(base, 99), '2026-03-02');

// needsReview：新词必复习
eq('新词需要复习', memory.needsReview({ status: memory.WORD_STATUS.NEW }), true);
eq('学习中需要复习', memory.needsReview({ status: memory.WORD_STATUS.LEARNING }), true);
const past = new Date(); past.setDate(past.getDate() - 1);
eq('已到期需要复习', memory.needsReview({ status: memory.WORD_STATUS.MASTERED, nextReviewDate: past.toISOString().split('T')[0] }), true);
const future = new Date(); future.setDate(future.getDate() + 3);
eq('未到期不需要复习', memory.needsReview({ status: memory.WORD_STATUS.MASTERED, nextReviewDate: future.toISOString().split('T')[0] }), false);

eq('答错得 0 分', memory.calculateMemoryScore(500, false), 0);
eq('1 秒内答对得 5 分', memory.calculateMemoryScore(500, true), 5);
eq('2 秒内答对得 4 分', memory.calculateMemoryScore(1500, true), 4);
eq('5 秒外答对得 1 分', memory.calculateMemoryScore(8000, true), 1);

// 7. 词库
console.log('');
const words = require(path.join(ROOT, 'utils', 'words.js'));
const list = words.cet4Words || words;
ok('词库加载成功，共 ' + list.length + ' 个词');
const malformed = list.filter(w => !w.word || !w.meaning);
if (malformed.length === 0) ok('每个词都有 word 与 meaning 字段');
else bad('词条字段缺失', malformed.length + ' 条');

console.log('');
console.log('结果: ' + pass + ' 通过, ' + fail + ' 失败');
if (fail) { console.log(problems.join('\n')); process.exit(1); }
