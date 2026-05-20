import { createRouter, createWebHistory } from 'vue-router'
import Home from '../pages/Home.vue'
import StockList from '../pages/StockList.vue'
import StockDetail from '../pages/StockDetail.vue'
import Backtest from '../pages/Backtest.vue'
import Predict from '../pages/Predict.vue'
import Train from '../pages/Train.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/stock', name: 'StockList', component: StockList },
  { path: '/stock/:code', name: 'StockDetail', component: StockDetail },
  { path: '/backtest', name: 'Backtest', component: Backtest },
  { path: '/predict', name: 'Predict', component: Predict },
  { path: '/train', name: 'Train', component: Train }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
