Component({
  properties: {
    selected: {
      type: Number,
      value: 0
    }
  },

  data: {
    tabList: [
      { text: '首页', path: '/pages/index/index', icon: 'home', activeIcon: 'home-fill' },
      { text: '词库', path: '/pages/wordlist/wordlist', icon: 'book', activeIcon: 'book-fill' },
      { text: '学习', path: '/pages/study/study', icon: 'study', activeIcon: 'study-fill' },
      { text: '统计', path: '/pages/stats/stats', icon: 'chart', activeIcon: 'chart-fill' },
      { text: '我的', path: '/pages/profile/profile', icon: 'user', activeIcon: 'user-fill' }
    ]
  },

  methods: {
    onTabTap(e) {
      const index = e.currentTarget.dataset.index;
      const path = this.data.tabList[index].path;
      wx.switchTab({ url: path });
    }
  }
})