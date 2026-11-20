const { generateId, getTodayStr } = require('./memory.js');

/**
 * 存储管理模块
 */
class Storage {
  // 懒加载词库，避免启动时加载大量数据
  static _cet4Words = null;
  static getCet4Words() {
    if (!this._cet4Words) {
      const { cet4Words } = require('./words.js');
      this._cet4Words = cet4Words;
    }
    return this._cet4Words;
  }

  // 初始化数据
  static initData() {
    const settings = wx.getStorageSync('settings');
    if (!settings) {
      wx.setStorageSync('settings', {
        dailyGoal: 20,
        currentList: 'cet4',
        autoPlay: true,
        showPhonetic: true,
        studyMode: 'flashcard'
      });
    }

    const stats = wx.getStorageSync('stats');
    if (!stats) {
      wx.setStorageSync('stats', {
        totalLearned: 0,
        totalMastered: 0,
        consecutiveDays: 0,
        lastStudyDate: null,
        dailyStats: {},
        totalStudyTime: 0
      });
    }

    const words = wx.getStorageSync('words');
    if (!words || words.length === 0) {
      // 同步播种：原来是 setTimeout(300) 异步写入，首页只等 100ms 就刷新，
      // 冷启动首屏会显示 0 个新词。188 条数据生成不到 10ms，没必要异步。
      const initialWords = this.getCet4Words().map(w => ({
        ...w,
        id: generateId(),
        status: 0,
        reviewCount: 0,
        nextReviewDate: getTodayStr(),
        addedDate: getTodayStr()
      }));
      wx.setStorageSync('words', initialWords);
    }
  }

  // 获取所有单词
  static getWords() {
    return wx.getStorageSync('words') || [];
  }

  // 更新单词
  static updateWord(id, updates) {
    const words = this.getWords();
    const index = words.findIndex(w => w.id === id);
    if (index >= 0) {
      words[index] = { ...words[index], ...updates };
      wx.setStorageSync('words', words);
      return words[index];
    }
    return null;
  }

  // 获取设置
  static getSettings() {
    return wx.getStorageSync('settings') || {};
  }

  // 更新设置
  static updateSettings(updates) {
    const settings = this.getSettings();
    const newSettings = { ...settings, ...updates };
    wx.setStorageSync('settings', newSettings);
    return newSettings;
  }

  // 获取统计
  static getStats() {
    return wx.getStorageSync('stats') || {};
  }

  // 更新统计
  static updateStats(updates) {
    const stats = this.getStats();
    const newStats = { ...stats, ...updates };
    wx.setStorageSync('stats', newStats);
    return newStats;
  }

  // 记录学习
  static recordStudy(studiedCount, learnedCount, duration) {
    const stats = this.getStats();
    const today = getTodayStr();
    const dailyStats = stats.dailyStats || {};

    if (!dailyStats[today]) {
      dailyStats[today] = { studied: 0, learned: 0, duration: 0 };
    }
    dailyStats[today].studied += studiedCount;
    dailyStats[today].learned += learnedCount;
    dailyStats[today].duration += duration;

    // 计算连续天数
    let consecutiveDays = stats.consecutiveDays || 0;
    if (stats.lastStudyDate === today) {
      // 今天已记录
    } else if (stats.lastStudyDate) {
      const last = new Date(stats.lastStudyDate);
      const now = new Date(today);
      const diffDays = Math.floor((now - last) / (1000 * 60 * 60 * 24));
      if (diffDays === 1) {
        consecutiveDays += 1;
      } else {
        consecutiveDays = 1;
      }
    } else {
      consecutiveDays = 1;
    }

    const newStats = {
      ...stats,
      totalLearned: (stats.totalLearned || 0) + learnedCount,
      consecutiveDays,
      lastStudyDate: today,
      dailyStats,
      totalStudyTime: (stats.totalStudyTime || 0) + duration
    };
    wx.setStorageSync('stats', newStats);
    return newStats;
  }

  // 添加自定义单词
  static addCustomWord(word) {
    const words = this.getWords();
    const newWord = {
      ...word,
      id: generateId(),
      status: 0,
      reviewCount: 0,
      nextReviewDate: getTodayStr(),
      addedDate: getTodayStr(),
      isCustom: true
    };
    words.push(newWord);
    wx.setStorageSync('words', words);
    return newWord;
  }

  // 删除单词
  static deleteWord(id) {
    const words = this.getWords().filter(w => w.id !== id);
    wx.setStorageSync('words', words);
  }
}

module.exports = Storage;