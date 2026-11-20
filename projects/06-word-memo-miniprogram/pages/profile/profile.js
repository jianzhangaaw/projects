// pages/profile/profile.js
const Storage = require('../../utils/storage.js');
const User = require('../../utils/user.js');
const { WORD_STATUS } = require('../../utils/memory.js');

Page({
  data: {
    settings: {
      dailyGoal: 20,
      autoPlay: true,
      showPhonetic: true,
      studyMode: 'flashcard'
    },
    studyModes: [
      { value: 'flashcard', label: '闪卡模式', icon: '🃏' },
      { value: 'spelling', label: '拼写模式', icon: '✏️' },
      { value: 'listening', label: '听音模式', icon: '🔊' }
    ],
    user: {},
    isLoggedIn: false
  },

  onShow() {
    Storage.initData();
    User.init();
    this.loadSettings();
    this.loadUserInfo();
  },

  loadUserInfo() {
    const user = User.getUser() || {};
    const stats = Storage.getStats();
    const words = Storage.getWords();

    // 原来这三个数字读的是 user.totalWords / user.studyDays / user.masteredWords，
    // 而更新它们的方法从没被调用过，所以永远显示 0。现在直接从学习数据算。
    this.setData({
      user: {
        ...user,
        totalWords: stats.totalLearned || 0,
        masteredWords: words.filter(w => w.status === WORD_STATUS.MASTERED).length,
        studyDays: Object.keys(stats.dailyStats || {}).length
      },
      isLoggedIn: User.isLoggedIn()
    });
  },

  loadSettings() {
    const settings = Storage.getSettings();
    this.setData({ settings });
  },

  onDailyGoalChange(e) {
    const dailyGoal = parseInt(e.detail.value) || 20;
    this.updateSettings({ dailyGoal });
  },

  onSwitchChange(e) {
    const field = e.currentTarget.dataset.field;
    this.updateSettings({ [field]: e.detail.value });
  },

  onModeChange(e) {
    const studyMode = e.currentTarget.dataset.mode;
    this.updateSettings({ studyMode });
  },

  updateSettings(updates) {
    Storage.updateSettings(updates);
    this.loadSettings();
    wx.showToast({ title: '设置已保存', icon: 'success' });
  },

  onResetData() {
    wx.showModal({
      title: '确认重置',
      content: '确定要重置所有学习数据吗？此操作不可恢复！',
      success: (res) => {
        if (res.confirm) {
          wx.clearStorageSync();
          Storage.initData();
          this.loadSettings();
          wx.showToast({ title: '数据已重置', icon: 'success' });
        }
      }
    });
  },

  onAbout() {
    wx.showModal({
      title: '关于',
      content: '单词背诵助手 v1.0\n\n基于艾宾浩斯记忆曲线设计，科学高效背单词。',
      showCancel: false
    });
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/login' });
  },

  onLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          User.logout();
          this.loadUserInfo();
          wx.showToast({ title: '已退出登录', icon: 'success' });
          setTimeout(() => {
            wx.reLaunch({ url: '/pages/login/login' });
          }, 1500);
        }
      }
    });
  }
})