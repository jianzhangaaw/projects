// index.js
const Storage = require('../../utils/storage.js');

Page({
  data: {
    todayLearned: 0,
    todayGoal: 20,
    consecutiveDays: 0,
    reviewCount: 0,
    newCount: 0,
    totalWords: 0,
    progressPercent: 0,
    showGreeting: '早上好'
  },

  onShow() {
    setTimeout(() => {
      const Storage = require('../../utils/storage.js');
      Storage.initData();
      this.refreshData();
      this.setGreeting();
    }, 100);
  },

  setGreeting() {
    const hour = new Date().getHours();
    let greet = '早上好';
    if (hour >= 12 && hour < 18) greet = '下午好';
    else if (hour >= 18) greet = '晚上好';
    this.setData({ showGreeting: greet });
  },

  refreshData() {
    // 按需加载模块
    const Storage = require('../../utils/storage.js');
    const { needsReview, getTodayStr, WORD_STATUS } = require('../../utils/memory.js');
    
    const stats = Storage.getStats();
    const settings = Storage.getSettings();
    const words = Storage.getWords();
    const today = getTodayStr();

    // 今日已学
    const todayStats = (stats.dailyStats && stats.dailyStats[today]) || { learned: 0 };
    const todayLearned = todayStats.learned;

    // 待复习单词数
    const reviewCount = words.filter(w => needsReview(w) && w.status !== 0).length;
    // 新词数
    const newCount = words.filter(w => w.status === 0).length;

    const totalWords = words.filter(w => w.status === WORD_STATUS.MASTERED).length;
    const dailyGoal = settings.dailyGoal || 20;
    const progressPercent = Math.min(100, Math.round((todayLearned / dailyGoal) * 100));

    this.setData({
      todayLearned,
      todayGoal: dailyGoal,
      consecutiveDays: stats.consecutiveDays || 0,
      reviewCount,
      newCount,
      totalWords,
      progressPercent
    });
  },

  goStudy() {
    wx.switchTab({ url: '/pages/study/study' });
  },

  goReview() {
    wx.navigateTo({ url: '/pages/review/review' });
  },

  goNewWords() {
    // study 是 tabBar 页，wx.navigateTo 会静默失败；switchTab 又不能带 query，
    // 所以用一条一次性设置把「只看新词」传给学习页（study.onShow 读取后清掉）。
    Storage.updateSettings({ pendingStudyMode: 'new' });
    wx.switchTab({ url: '/pages/study/study' });
  },

  goWordList() {
    wx.switchTab({ url: '/pages/wordlist/wordlist' });
  }
})