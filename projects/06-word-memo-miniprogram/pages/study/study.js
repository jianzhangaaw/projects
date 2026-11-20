// pages/study/study.js
const Storage = require('../../utils/storage.js');
const { WORD_STATUS, getNextReviewDate, getTodayStr, needsReview } = require('../../utils/memory.js');

Page({
  data: {
    mode: 'flashcard', // flashcard, spelling, listening
    studyWords: [],
    currentIndex: 0,
    currentWord: null,
    showAnswer: false,
    studiedCount: 0,
    learnedCount: 0,
    startTime: null,

    // 拼写模式
    spellingInput: '',
    spellingResult: null,

    // 听音模式
    isPlaying: false,

    // 设置项：显示音标
    showPhonetic: true,

    // 进度条百分比（原来 WXML 引用了这个字段，JS 里从没赋值，宽度一直按 100% 渲染）
    progressPercent: 0
  },

  audioContext: null,

  // 懒加载音频上下文
  getAudioContext() {
    if (!this.audioContext) {
      this.audioContext = wx.createInnerAudioContext();
    }
    return this.audioContext;
  },

  onLoad(options) {
    this.setData({ startTime: Date.now() });

    Storage.initData();
    const settings = Storage.getSettings();

    // 「我的 → 学习模式」里的选择是默认模式；带 mode 参数时以参数为准
    const mode = options.mode || settings.studyMode || 'flashcard';
    this.setData({ mode, showPhonetic: settings.showPhonetic !== false });

    this.loadByMode(mode);
  },

  onShow() {
    const settings = Storage.getSettings();
    this.setData({ showPhonetic: settings.showPhonetic !== false });

    // 首页的「学习新词」是 switchTab 过来的，不能带 query，用一条一次性标记传模式
    const pending = settings.pendingStudyMode;
    if (pending) {
      Storage.updateSettings({ pendingStudyMode: '' });
      this.setData({
        mode: pending,
        currentIndex: 0,
        showAnswer: false,
        spellingInput: '',
        spellingResult: null,
        studiedCount: 0,
        learnedCount: 0,
        startTime: Date.now()
      });
      this.loadByMode(pending);
    }
  },

  loadByMode(mode) {
    if (mode === 'new') {
      // 'new' 只是选题范围，不是界面模式：WXML 的三套界面按 flashcard/spelling/listening 分支，
      // 直接留着 mode='new' 会一个 block 都不匹配，页面空白。
      this.setData({ mode: 'flashcard' });
      this.loadNewWords();
    } else {
      this.loadStudyWords();
    }
  },

  updateProgress(index) {
    const total = this.data.studyWords.length;
    this.setData({ progressPercent: total ? Math.round((index + 1) / total * 100) : 0 });
  },

  onUnload() {
    if (this._advanceTimer) {
      clearTimeout(this._advanceTimer);
      this._advanceTimer = null;
    }
    if (this.audioContext) {
      this.audioContext.destroy();
      this.audioContext = null;
    }
    this.recordStudyTime();
  },

  recordStudyTime() {
    if (this._studyRecorded) return; // 退出按钮和 onUnload 都会调，只记一次
    const duration = Math.round((Date.now() - this.data.startTime) / 1000);
    if (duration > 5 && this.data.studiedCount > 0) {
      this._studyRecorded = true;
      Storage.recordStudy(this.data.studiedCount, this.data.learnedCount, duration);
    }
  },

  loadNewWords() {
    const words = Storage.getWords().filter(w => w.status === WORD_STATUS.NEW);
    const settings = Storage.getSettings();
    const dailyGoal = settings.dailyGoal || 20;
    const studyWords = words.slice(0, dailyGoal);

    this.setData({
      studyWords,
      currentIndex: 0,
      currentWord: studyWords[0] || null,
      showAnswer: false
    });
    this.updateProgress(0);
    this.autoPlayIfEnabled();
  },

  loadStudyWords() {
    const words = Storage.getWords();
    const settings = Storage.getSettings();
    const dailyGoal = settings.dailyGoal || 20;

    const needReviewWords = words.filter(w => w.status !== WORD_STATUS.NEW && needsReview(w));
    const newWords = words.filter(w => w.status === WORD_STATUS.NEW);

    const studyWords = [...needReviewWords, ...newWords].slice(0, dailyGoal);

    this.setData({
      studyWords,
      currentIndex: 0,
      currentWord: studyWords[0] || null,
      showAnswer: false
    });
    this.updateProgress(0);
    this.autoPlayIfEnabled();
  },

  // 「自动播放发音」开关打开时，进入新词就播一次
  autoPlayIfEnabled() {
    const settings = Storage.getSettings();
    if (settings.autoPlay === false || !this.data.currentWord) return;
    setTimeout(() => {
      if (this.data.currentWord) this.playAudio();
    }, 250);
  },

  onShowAnswer() {
    this.setData({ showAnswer: true });
  },

  onKnow() {
    this.markWord(true);
  },

  onUnknown() {
    this.markWord(false);
  },

  markWord(known) {
    const word = this.data.currentWord;
    if (!word) return;

    let updates = {};
    let learnedIncrement = 0;

    if (known) {
      const newReviewCount = word.reviewCount + 1;
      let newStatus = word.status;

      if (word.status === WORD_STATUS.NEW) {
        newStatus = WORD_STATUS.LEARNING;
        learnedIncrement = 1;
      } else if (word.status === WORD_STATUS.LEARNING && newReviewCount >= 5) {
        newStatus = WORD_STATUS.MASTERED;
      }

      updates = {
        status: newStatus,
        reviewCount: newReviewCount,
        nextReviewDate: getNextReviewDate(getTodayStr(), newReviewCount)
      };
    } else {
      updates = {
        status: WORD_STATUS.LEARNING,
        reviewCount: 0,
        nextReviewDate: getTodayStr()
      };
    }

    Storage.updateWord(word.id, updates);

    this.setData({
      studiedCount: this.data.studiedCount + 1,
      learnedCount: this.data.learnedCount + learnedIncrement
    });

    this.goNext();
  },

  // 拼写模式
  onSpellingInput(e) {
    this.setData({ spellingInput: e.detail.value });
  },

  checkSpelling() {
    if (this.data.spellingResult) return; // 已经判过，避免连点重复计分
    const { currentWord, spellingInput } = this.data;
    if (!currentWord) return;

    const isCorrect = String(spellingInput).trim().toLowerCase() === currentWord.word.toLowerCase();
    this.setData({
      spellingResult: isCorrect ? 'correct' : 'wrong',
      showAnswer: !isCorrect // 答错时显示答案
    });

    if (isCorrect) {
      // 原来这里直接 markWord(true)，goNext 会立刻把 'correct' 覆盖掉，
      // 「回答正确」永远看不到。现在停留 700ms 再进入下一题。
      this._advanceTimer = setTimeout(() => {
        this._advanceTimer = null;
        this.markWord(true);
      }, 700);
    }
  },

  // 拼写模式答错后继续
  onSpellingContinue() {
    this.markWord(false);
  },

  // 听音模式 - 播放单词发音（使用有道TTS）
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

  // 听音模式显示答案
  onListeningShowAnswer() {
    this.setData({ showAnswer: true });
  },

  onListeningCorrect() {
    this.markWord(true);
    this.setData({ spellingResult: null, showAnswer: false });
  },

  onListeningWrong() {
    this.setData({ spellingResult: 'wrong', showAnswer: true });
  },

  // 听音模式答错后继续
  onListeningContinue() {
    this.markWord(false);
    this.setData({ spellingResult: null, showAnswer: false });
  },

  goNext() {
    const nextIndex = this.data.currentIndex + 1;
    if (nextIndex < this.data.studyWords.length) {
      this.setData({
        currentIndex: nextIndex,
        currentWord: this.data.studyWords[nextIndex],
        showAnswer: false,
        spellingInput: '',
        spellingResult: null
      });
      this.updateProgress(nextIndex);
      this.autoPlayIfEnabled();
    } else {
      this.showComplete();
    }
  },

  showComplete() {
    wx.showModal({
      title: '学习完成',
      content: `本次学习了 ${this.data.studiedCount} 个单词，其中新学 ${this.data.learnedCount} 个`,
      showCancel: false,
      success: () => {
        wx.navigateBack();
      }
    });
  },

  goBack() {
    this.recordStudyTime();
    wx.navigateBack();
  }
})
