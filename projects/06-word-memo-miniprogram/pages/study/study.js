// pages/study/study.js
const Storage = require('../../utils/storage.js');
const { WORD_STATUS, getNextReviewDate, getTodayStr, needsReview } = require('../../utils/memory.js');

Page({
  data: {
    mode: 'flashcard', // flashcard, spelling, listening, add
    studyWords: [],
    currentIndex: 0,
    currentWord: null,
    showAnswer: false,
    studiedCount: 0,
    learnedCount: 0,
    startTime: null,

    // 添加单词表单
    newWord: {
      word: '',
      phonetic: '',
      meaning: '',
      example: '',
      exampleCn: ''
    },

    // 拼写模式
    spellingInput: '',
    spellingResult: null,

    // 听音模式
    isPlaying: false
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

    const Storage = require('../../utils/storage.js');
    Storage.initData();

    const mode = options.mode || 'flashcard';
    this.setData({ mode });

    if (mode === 'add') {
      // 添加单词模式
    } else if (mode === 'new') {
      this.loadNewWords();
    } else {
      this.loadStudyWords();
    }
  },

  onUnload() {
    if (this.audioContext) {
      this.audioContext.destroy();
      this.audioContext = null;
    }
    this.recordStudyTime();
  },

  recordStudyTime() {
    const duration = Math.round((Date.now() - this.data.startTime) / 1000);
    if (duration > 5 && this.data.studiedCount > 0) {
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
    const { currentWord, spellingInput } = this.data;
    const isCorrect = spellingInput.toLowerCase() === currentWord.word.toLowerCase();
    this.setData({
      spellingResult: isCorrect ? 'correct' : 'wrong',
      showAnswer: !isCorrect // 答错时显示答案
    });

    if (isCorrect) {
      this.markWord(true);
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

  // 添加单词
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

    // 重置表单
    this.setData({
      newWord: { word: '', phonetic: '', meaning: '', example: '', exampleCn: '' },
      mode: 'flashcard'
    });
    this.loadStudyWords();
  },

  onCancelAdd() {
    this.setData({ mode: 'flashcard' });
    this.loadStudyWords();
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