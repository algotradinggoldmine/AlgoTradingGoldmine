import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  // base: '/AlgoTradingGoldmine/',
  title: "算法交易掘金 (Algo Trading Goldmine)",
  description: "探索算法交易的无限可能，尽在 Algo Trading Goldmine！我们致力于打造一个分享、学习和交流的平台，讨论量化交易策略、自动化交易系统开发、金融数据分析等话题。与志同道合的交易者一起成长，共同在算法交易的金矿中淘金！",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: '主页', link: '/' },
      { text: '交易策略', link: '/strategies-index' }
    ],

    sidebar: [
      {
        text: '交易策略',
        items: [
          { text: '外汇短期价格确认的移动平均线交叉策略', link: '/strategies/forex_ma_crossover_v1.00.00/forex_ma_crossover_v1.00.00' },
          // { text: 'Runtime API Examples', link: '/api-examples' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/algotradinggoldmine/AlgoTradingGoldmine' }
    ]
  }
})
