// pages/wordlist/wordlist.js
const Storage = require('../../utils/storage.js');
const { wordLists } = require('../../utils/words.js');
const { WORD_STATUS } = require('../../utils/memory.js');

Page({
  data: {
    words: [],
    searchKeyword: '',
    filterType: 'all', // all, new, learning, mastered
    currentList: 'cet4',
    wordLists: Object.keys(wordLists)
  },

  onLoad() {
    Storage.initData();
    this.loadWords();
  },

  onShow() {
    this.loadWords();
  },

  loadWords() {
    const allWords = Storage.getWords();
    const filteredWords = this.filterWords(allWords);
    
    const allCount = allWords.length;
    const newCount = allWords.filter(w => w.status === WORD_STATUS.NEW).length;
    const learningCount = allWords.filter(w => w.status === WORD_STATUS.LEARNING).length;
    const masteredCount = allWords.filter(w => w.status === WORD_STATUS.MASTERED).length;
    
    this.setData({ 
      words: filteredWords,
      allCount,
      newCount,
      learningCount,
      masteredCount
    });
  },

  filterWords(words) {
    const { searchKeyword, filterType } = this.data;
    let filtered = words;

    // 搜索过滤
    if (searchKeyword) {
      const kw = searchKeyword.toLowerCase();
      filtered = filtered.filter(w =>
        w.word.toLowerCase().includes(kw) ||
        w.meaning.includes(kw)
      );
    }

    // 状态过滤
    if (filterType !== 'all') {
      filtered = filtered.filter(w => {
        if (filterType === 'new') return w.status === WORD_STATUS.NEW;
        if (filterType === 'learning') return w.status === WORD_STATUS.LEARNING;
        if (filterType === 'mastered') return w.status === WORD_STATUS.MASTERED;
        return true;
      });
    }

    return filtered;
  },

  onSearch(e) {
    this.setData({ searchKeyword: e.detail.value });
    this.loadWords();
  },

  onFilterChange(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({ filterType: type });
    this.loadWords();
  },

  // 清空搜索
  onClearSearch() {
    this.setData({ searchKeyword: '' });
    this.loadWords();
  },

  onWordTap(e) {
    const { word, expanded } = e.currentTarget.dataset;
    this.setData({
      [`words[${this.data.words.findIndex(w => w.id === word.id)}].expanded`]: !expanded
    });
  },

  onAddWord() {
    wx.navigateTo({ url: '/pages/addword/addword' });
  },

  onDeleteWord(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个单词吗？',
      success: (res) => {
        if (res.confirm) {
          Storage.deleteWord(id);
          this.loadWords();
        }
      }
    });
  },

  getStatusText(status) {
    const map = {
      [WORD_STATUS.NEW]: '新词',
      [WORD_STATUS.LEARNING]: '学习中',
      [WORD_STATUS.MASTERED]: '已掌握'
    };
    return map[status] || '新词';
  },

  getStatusClass(status) {
    const map = {
      [WORD_STATUS.NEW]: 'status-new',
      [WORD_STATUS.LEARNING]: 'status-learning',
      [WORD_STATUS.MASTERED]: 'status-mastered'
    };
    return map[status] || 'status-new';
  }
})