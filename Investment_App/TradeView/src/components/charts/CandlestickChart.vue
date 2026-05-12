<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settingsStore'
import { formatShortDate } from '@/utils/formatters'
import type { Candle } from '@/types/market'
import type { EChartsOption } from 'echarts'

interface Props {
  candles: Candle[]
  symbol?: string
  height?: string
  showVolume?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  showVolume: true,
})

const settings = useSettingsStore()

const option = computed((): EChartsOption => {
  const isDark = settings.theme === 'dark'
  const textColor   = isDark ? '#94a3b8' : '#64748b'
  const gridColor   = isDark ? '#1e2340' : '#e2e8f0'
  const labelColor  = isDark ? '#e2e8f0' : '#1e293b'
  const bgColor     = isDark ? '#141827' : '#ffffff'
  const borderColor = isDark ? '#1e2340' : '#e2e8f0'
  const upColor     = '#22c55e'
  const downColor   = '#ef4444'

  const dates    = props.candles.map((c) => formatShortDate(c.timestamp))
  const ohlcData = props.candles.map((c) => [c.open, c.close, c.low, c.high])
  const volumes  = props.candles.map((c) => c.volume)

  const grids = props.showVolume
    ? [{ left: '2%', right: '2%', top: '2%', bottom: '28%', containLabel: true },
       { left: '2%', right: '2%', top: '75%', bottom: '6%', containLabel: true }]
    : [{ left: '2%', right: '2%', top: '2%', bottom: '8%', containLabel: true }]

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: bgColor,
      borderColor,
      textStyle: { color: labelColor, fontSize: 11 },
    },
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      { type: 'slider',  xAxisIndex: [0, 1], start: 50, end: 100, height: 18, bottom: 0, textStyle: { color: textColor, fontSize: 10 } },
    ],
    grid: grids,
    xAxis: [
      {
        type: 'category', data: dates, boundaryGap: true,
        axisLine: { lineStyle: { color: gridColor } },
        axisLabel: { color: textColor, fontSize: 10 },
        splitLine: { show: false },
      },
      ...(props.showVolume
        ? [{ type: 'category' as const, data: dates, gridIndex: 1, axisLabel: { show: false }, axisLine: { lineStyle: { color: gridColor } }, splitLine: { show: false } }]
        : []),
    ],
    yAxis: [
      {
        scale: true,
        axisLabel: { color: textColor, fontSize: 10 },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: gridColor, type: 'dashed' } },
      },
      ...(props.showVolume
        ? [{ scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { color: textColor, fontSize: 10 }, axisLine: { show: false }, splitLine: { show: false } }]
        : []),
    ],
    series: [
      {
        name: props.symbol ?? 'Price',
        type: 'candlestick',
        data: ohlcData,
        itemStyle: {
          color: upColor,
          color0: downColor,
          borderColor: upColor,
          borderColor0: downColor,
        },
      },
      ...(props.showVolume
        ? [{
            name: 'Volume',
            type: 'bar' as const,
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes,
            itemStyle: {
              color: (params: { dataIndex: number }) => {
                const c = props.candles[params.dataIndex]
                return c.close >= c.open ? upColor + '80' : downColor + '80'
              },
            },
          }]
        : []),
    ],
  }
})
</script>

<template>
  <VChart :option="option" :style="{ height, width: '100%' }" :theme="settings.theme" autoresize />
</template>
