import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

// ECharts — register only the charts and components we use (tree-shaking)
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart, CandlestickChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent,
  ToolboxComponent,
  MarkLineComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  BarChart, LineChart, PieChart, CandlestickChart,
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  DataZoomComponent, ToolboxComponent, MarkLineComponent,
])

import router from './router'
import App from './App.vue'
import '@/styles/main.css'

// ─── Bootstrap ────────────────────────────────────────────────────────────────

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

const app = createApp(App)

app.use(pinia)
app.use(router)
app.component('VChart', VChart)

app.mount('#app')
