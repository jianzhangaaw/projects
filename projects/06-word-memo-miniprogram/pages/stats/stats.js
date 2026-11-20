// pages/stats/stats.js
const Storage = require('../../utils/storage.js');
const { WORD_STATUS, getTodayStr, formatDate, toDateStr } = require('../../utils/memory.js');

Page({
  data: {
    totalLearned: 0,
    totalMastered: 0,
    consecutiveDays: 0,
    totalStudyTime: 0,
    todayLearned: 0,
    todayDate: '',
    weekData: [],
    maxDayLearned: 1,
    statusData: []
  },

  onShow() {
    Storage.initData();
    this.loadStats();
  },

  loadStats() {
    const stats = Storage.getStats();
    const words = Storage.getWords();

    const today = getTodayStr();
    const todayStats = (stats.dailyStats && stats.dailyStats[today]) || { learned: 0, studied: 0 };
    const todayLearned = todayStats.learned;

    // 统计各状态单词数
    const newCount = words.filter(w => w.status === WORD_STATUS.NEW).length;
    const learningCount = words.filter(w => w.status === WORD_STATUS.LEARNING).length;
    const masteredCount = words.filter(w => w.status === WORD_STATUS.MASTERED).length;

    // 近7天数据
    const weekData = this.getWeekData(stats.dailyStats || {});
    const maxDayLearned = Math.max(...weekData.map(d => d.learned), 1);

    // 学习时长格式化
    const totalStudyTime = this.formatDuration(stats.totalStudyTime || 0);

    // 日期格式化
    const date = new Date();
    const todayDate = `${date.getMonth() + 1}月${date.getDate()}日`;

    // 计算百分比
    const totalWords = words.length || 1;

    this.setData({
      totalLearned: stats.totalLearned || 0,
      totalMastered: masteredCount,
      consecutiveDays: stats.consecutiveDays || 0,
      totalStudyTime,
      todayLearned,
      todayDate,
      weekData,
      maxDayLearned,
      statusData: [
        { name: '新词', value: newCount, color: '#FF9800', percent: Math.round(newCount / totalWords * 100) },
        { name: '学习中', value: learningCount, color: '#2196F3', percent: Math.round(learningCount / totalWords * 100) },
        { name: '已掌握', value: masteredCount, color: '#4CAF50', percent: Math.round(masteredCount / totalWords * 100) }
      ]
    });
  },

  getWeekData(dailyStats) {
    const data = [];
    const today = new Date();

    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = toDateStr(date);
      const dayStats = dailyStats[dateStr] || { learned: 0 };

      data.push({
        date: formatDate(dateStr),
        learned: dayStats.learned || 0,
        isToday: i === 0
      });
    }

    return data;
  },

  formatDuration(seconds) {
    if (seconds < 60) return `${seconds}秒`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`;
    const hours = Math.floor(seconds / 3600);
    const mins = Math.round((seconds % 3600) / 60);
    return `${hours}小时${mins}分钟`;
  }
})