export type HistoryEntry = {
  id: string
  category: string
  label: string
  inputs: Record<string, string | number>
  results: Record<string, number | string>
  timestamp: number
}
