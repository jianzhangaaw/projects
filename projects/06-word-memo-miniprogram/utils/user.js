const { generateId } = require('./memory.js');

class User {
  static USER_KEY = 'user_info';
  static LOGIN_KEY = 'is_logged_in';

  static init() {
    const user = wx.getStorageSync(this.USER_KEY);
    if (!user) {
      this.createDefaultUser();
    }
  }

  static createDefaultUser() {
    const defaultUser = {
      id: generateId(),
      nickname: '未登录',
      avatar: '',
      phone: '',
      studyDays: 0,
      totalWords: 0,
      createTime: new Date().toISOString()
    };
    wx.setStorageSync(this.USER_KEY, defaultUser);
    wx.setStorageSync(this.LOGIN_KEY, false);
  }

  static getUser() {
    return wx.getStorageSync(this.USER_KEY) || null;
  }

  static updateUser(updates) {
    const user = this.getUser();
    if (!user) return null;
    const newUser = { ...user, ...updates };
    wx.setStorageSync(this.USER_KEY, newUser);
    return newUser;
  }

  static isLoggedIn() {
    return wx.getStorageSync(this.LOGIN_KEY) || false;
  }

  static login(userInfo) {
    const user = this.getUser();
    const newUser = {
      ...user,
      ...userInfo,
      lastLoginTime: new Date().toISOString()
    };
    wx.setStorageSync(this.USER_KEY, newUser);
    wx.setStorageSync(this.LOGIN_KEY, true);
    return newUser;
  }

  static logout() {
    wx.setStorageSync(this.LOGIN_KEY, false);
    this.createDefaultUser();
  }
}

module.exports = User;