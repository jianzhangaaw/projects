const User = require('../../utils/user.js');
const Storage = require('../../utils/storage.js');

Page({
  data: {
    nickname: '',
    avatar: '',
    loading: false
  },

  onLoad() {
    setTimeout(() => {
      User.init();
      Storage.initData();
    }, 100);
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value });
  },

  onChooseAvatar(e) {
    const { avatarUrl } = e.detail;
    this.setData({ avatar: avatarUrl });
  },

  /**
   * 微信授权登录。
   *
   * 原来这里调 wx.getUserProfile 拿真实头像昵称，但微信自 2022 年起回收了这个能力
   * （返回的是「微信用户」+ 默认灰色头像），而且 API 本身已标记废弃。
   * 现在头像走 wxml 里的 <button open-type="chooseAvatar">，昵称走输入框，
   * 这个按钮只保留「提交当前填写的信息」的语义。
   */
  onWechatLogin() {
    if (!this.data.nickname) {
      wx.showToast({ title: '请先填写昵称', icon: 'none' });
      return;
    }
    this.completeLogin({
      nickname: this.data.nickname,
      avatar: this.data.avatar || ''
    });
  },

  onPhoneLogin() {
    if (!this.data.nickname) {
      wx.showToast({ title: '请输入昵称', icon: 'none' });
      return;
    }

    this.setData({ loading: true });

    this.completeLogin({
      nickname: this.data.nickname,
      avatar: this.data.avatar || ''
    });
  },

  completeLogin(userInfo) {
    User.login(userInfo);
    this.setData({ loading: false });

    wx.showToast({ title: '登录成功', icon: 'success' });

    setTimeout(() => {
      wx.switchTab({ url: '/pages/index/index' });
    }, 1500);
  },

  onSkipLogin() {
    wx.switchTab({ url: '/pages/index/index' });
  }
})
