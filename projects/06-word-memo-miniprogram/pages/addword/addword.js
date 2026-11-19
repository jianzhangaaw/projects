const Storage = require('../../utils/storage.js');

Page({
  data: {
    newWord: {
      word: '',
      phonetic: '',
      meaning: '',
      example: '',
      exampleCn: ''
    }
  },

  onLoad() {
    Storage.initData();
  },

  onNewWordInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({
      [`newWord.${field}`]: e.detail.value
    });
  },

  onAddWord() {
    const { newWord } = this.data;
    if (!newWord.word || !newWord.meaning) {
      wx.showToast({ title: '请填写必填项', icon: 'none' });
      return;
    }

    Storage.addCustomWord(newWord);
    wx.showToast({ title: '添加成功', icon: 'success' });

    setTimeout(() => {
      wx.navigateBack();
    }, 1500);
  },

  onCancelAdd() {
    wx.navigateBack();
  }
})