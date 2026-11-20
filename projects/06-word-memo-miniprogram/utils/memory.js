// 艾宾浩斯记忆曲线复习间隔（天）
const REVIEW_INTERVALS = [1, 2, 4, 7, 15, 30, 60];

// 单词状态
const WORD_STATUS = {
  NEW: 0,        // 新词
  LEARNING: 1,   // 学习中
  MASTERED: 2    // 已掌握
};

function pad2(n) {
  return n < 10 ? '0' + n : '' + n;
}

/**
 * 把 Date 格式化成 YYYY-MM-DD。
 *
 * 这里必须用本地时间：原来用 toISOString()，在 UTC+8 下每天 0:00–8:00 都会被算成前一天，
 * 导致「今日已学」「连续天数」「待复习」在早上全部错位。
 */
function toDateStr(date) {
  return date.getFullYear() + '-' + pad2(date.getMonth() + 1) + '-' + pad2(date.getDate());
}

/** 解析 YYYY-MM-DD 为本地零点。new Date('YYYY-MM-DD') 会按 UTC 解析，不能用。 */
function parseDateStr(value) {
  const parts = String(value).split('-').map(Number);
  return new Date(parts[0] || 1970, (parts[1] || 1) - 1, parts[2] || 1);
}

// 获取下一个复习日期
function getNextReviewDate(lastReviewDate, reviewCount) {
  const interval = REVIEW_INTERVALS[Math.min(reviewCount, REVIEW_INTERVALS.length - 1)];
  const date = parseDateStr(lastReviewDate);
  date.setDate(date.getDate() + interval);
  return toDateStr(date);
}

// 检查是否需要复习
function needsReview(word) {
  if (word.status === WORD_STATUS.NEW) return true;
  if (word.status === WORD_STATUS.LEARNING) return true;
  if (!word.nextReviewDate) return true;
  return word.nextReviewDate <= getTodayStr();
}

// 计算记忆评分（0-5）
function calculateMemoryScore(responseTime, isCorrect) {
  if (!isCorrect) return 0;
  if (responseTime < 1000) return 5;
  if (responseTime < 2000) return 4;
  if (responseTime < 3000) return 3;
  if (responseTime < 5000) return 2;
  return 1;
}

// 格式化日期
function formatDate(dateStr) {
  const date = parseDateStr(dateStr);
  return (date.getMonth() + 1) + '月' + date.getDate() + '日';
}

// 获取今天的日期字符串（本地时区）
function getTodayStr() {
  return toDateStr(new Date());
}

// 生成唯一ID
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

module.exports = {
  REVIEW_INTERVALS,
  WORD_STATUS,
  getNextReviewDate,
  needsReview,
  calculateMemoryScore,
  formatDate,
  getTodayStr,
  toDateStr,
  generateId
};
