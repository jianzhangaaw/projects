// app.js
const Storage = require('./utils/storage.js');
const User = require('./utils/user.js');

App({
  onLaunch() {
    setTimeout(() => {
      try {
        Storage.initData();
      } catch (e) {
        console.error('数据初始化失败', e);
      }
    }, 100);

    setTimeout(() => {
      try {
        User.init();
      } catch (e) {
        console.error('用户初始化失败', e);
      }
    }, 200);
  }
})