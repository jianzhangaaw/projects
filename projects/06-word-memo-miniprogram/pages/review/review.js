// pages/review/review.js
const Storage = require('../../utils/storage.js');
const { needsReview, WORD_STATUS, getNextReviewDate, getTodayStr } = require('../../utils/memory.js');

Page({
  data: {
    reviewWords: [],
    currentIndex: 0,
    currentWord: null,
    showAnswer: false,
    reviewCount: 0,
    correctCount: 0,
    startTime: null,
    progressPercent: 0,
    isPlaying: false
  },

  onLoad() {
    Storage.initData();
    this.setData({ startTime: Date.now() });
    this.loadReviewWords();
  },

  onUnload() {
    this.recordReview();
  },

  recordReview() {
    if (this.data.reviewCount > 0) {
      const duration = Math.round((Date.now() - this.data.startTime) / 1000);
      Storage.recordStudy(this.data.reviewCount, 0, duration);
    }
  },

  loadReviewWords() {
    const allWords = Storage.getWords();
    const needReview = allWords.filter(w => needsReview(w));
    const reviewWords = needReview.filter(w => w.status !== WORD_STATUS.NEW);
    
    console.log('复习单词统计:', {
      total: allWords.length,
      needReview: needReview.length,
      reviewWords: reviewWords.length
    });

    const progressPercent = reviewWords.length > 0 ? 0 : 100;
    
    this.setData({
      reviewWords: reviewWords,
      currentIndex: 0,
      currentWord: reviewWords[0] || null,
      reviewCount: 0,
      correctCount: 0,
      progressPercent
    });
  },

  playAudio() {
    if (!this.data.currentWord) return;

    const word = this.data.currentWord.word;
    this.setData({ isPlaying: true });

    const audioUrl = `https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(word)}&type=1`;
    const ctx = this.getAudioContext();

    ctx.src = audioUrl;
    ctx.play();

    ctx.onEnded(() => {
      this.setData({ isPlaying: false });
    });

    ctx.onError((err) => {
      console.error('音频播放失败', err);
      wx.vibrateShort({ type: 'light' });
      wx.showToast({
        title: '发音: ' + word,
        icon: 'none',
        duration: 1500
      });
      this.setData({ isPlaying: false });
    });
  },

  getAudioContext() {
    if (!this.audioCtx) {
      this.audioCtx = wx.createInnerAudioContext();
    }
    return this.audioCtx;
  },

  onShowAnswer() {
    this.setData({ showAnswer: true });
  },

  onRemember() {
    this.markReview(true);
  },

  onForget() {
    this.markReview(false);
  },

  markReview(remember) {
    const word = this.data.currentWord;
    if (!word) return;

    let updates = {};
    if (remember) {
      // 记住了：更新复习时间
      const newReviewCount = word.reviewCount + 1;
      updates = {
        reviewCount: newReviewCount,
        nextReviewDate: getNextReviewDate(getTodayStr(), newReviewCount)
      };
    } else {
      // 忘了：重置复习次数
      updates = {
        reviewCount: 0,
        nextReviewDate: getTodayStr()
      };
    }

    Storage.updateWord(word.id, updates);

    this.setData({
      reviewCount: this.data.reviewCount + 1,
      correctCount: remember ? this.data.correctCount + 1 : this.data.correctCount
    });

    this.goNext();
  },

  goNext() {
    const nextIndex = this.data.currentIndex + 1;
    const progressPercent = nextIndex / this.data.reviewWords.length * 100;
    
    if (nextIndex < this.data.reviewWords.length) {
      this.setData({
        currentIndex: nextIndex,
        currentWord: this.data.reviewWords[nextIndex],
        showAnswer: false,
        progressPercent
      });
    } else {
      this.setData({ progressPercent: 100 });
      this.showComplete();
    }
  },

  showComplete() {
    const { reviewCount, correctCount } = this.data;
    const accuracy = reviewCount > 0 ? Math.round((correctCount / reviewCount) * 100) : 0;

    wx.showModal({
      title: '复习完成',
      content: `本次复习了 ${reviewCount} 个单词，正确率 ${accuracy}%`,
      showCancel: false,
      success: () => {
        wx.navigateBack();
      }
    });
  },

  goBack() {
    this.recordReview();
    wx.navigateBack();
  }
})