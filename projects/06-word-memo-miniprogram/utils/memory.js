// 艾宾浩斯记忆曲线复习间隔（天）
const REVIEW_INTERVALS = [1, 2, 4, 7, 15, 30, 60];

// 单词状态
const WORD_STATUS = {
  NEW: 0,        // 新词
  LEARNING: 1,   // 学习中
  MASTERED: 2    // 已掌握
};

// 获取下一个复习日期
function getNextReviewDate(lastReviewDate, reviewCount) {
  const interval = REVIEW_INTERVALS[Math.min(reviewCount, REVIEW_INTERVALS.length - 1)];
  const date = new Date(lastReviewDate);
  date.setDate(date.getDate() + interval);
  return date.toISOString().split('T')[0];
}

// 检查是否需要复习
function needsReview(word) {
  if (word.status === WORD_STATUS.NEW) return true;
  if (word.status === WORD_STATUS.LEARNING) return true;
  if (!word.nextReviewDate) return true;
  const today = new Date().toISOString().split('T')[0];
  return word.nextReviewDate <= today;
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
  const date = new Date(dateStr);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${month}月${day}日`;
}

// 获取今天的日期字符串
function getTodayStr() {
  return new Date().toISOString().split('T')[0];
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
  generateId
};