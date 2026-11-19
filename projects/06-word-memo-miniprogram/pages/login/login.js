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

  onWechatLogin() {
    this.setData({ loading: true });

    wx.getUserProfile({
      desc: '用于完善用户资料',
      success: (res) => {
        const userInfo = {
          nickname: res.userInfo.nickName,
          avatar: res.userInfo.avatarUrl
        };
        this.completeLogin(userInfo);
      },
      fail: (err) => {
        console.error('获取用户信息失败', err);
        wx.showToast({ title: '授权失败', icon: 'none' });
        this.setData({ loading: false });
      }
    });
  },

  onPhoneLogin() {
    if (!this.data.nickname) {
      wx.showToast({ title: '请输入昵称', icon: 'none' });
      return;
    }

    this.setData({ loading: true });

    wx.getUserProfile({
      desc: '用于完善用户资料',
      success: (res) => {
        const userInfo = {
          nickname: this.data.nickname,
          avatar: res.userInfo.avatarUrl
        };
        this.completeLogin(userInfo);
      },
      fail: (err) => {
        const userInfo = {
          nickname: this.data.nickname,
          avatar: this.data.avatar || ''
        };
        this.completeLogin(userInfo);
      }
    });
  },

  completeLogin(userInfo) {
    const user = User.login(userInfo);
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