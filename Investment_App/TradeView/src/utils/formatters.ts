import { format, formatDistanceToNow, parseISO } from 'date-fns'

// ─── Number Formatters ────────────────────────────────────────────────────────

/** Format a price with appropriate decimal places and currency symbol */
export function formatPrice(value: number, currency = 'USD', compact = false): string {
  if (value === null || value === undefined || isNaN(value)) return '—'

  const decimals = value >= 1000 ? 2 : value >= 1 ? 4 : 6

  if (compact && value >= 1_000_000_000) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 2 }).format(value / 1_000_000_000) + 'B'
  }
  if (compact && value >= 1_000_000) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 2 }).format(value / 1_000_000) + 'M'
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: decimals,
  }).format(value)
}

/** Format a percentage change with + / − prefix */
export function formatChange(value: number, showSign = true): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  const sign = showSign && value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

/** Format a large number with K / M / B suffixes */
export function formatVolume(value: number): string {
  if (!value) return '—'
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return String(value)
}

/** Format an integer with locale thousands separators */
export function formatNumber(value: number): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-US').format(value)
}

// ─── Date Formatters ──────────────────────────────────────────────────────────

/** Format ISO string to "MMM d, yyyy HH:mm" */
export function formatDate(iso: string | undefined | null): string {
  if (!iso) return '—'
  try {
    return format(parseISO(iso), 'MMM d, yyyy HH:mm')
  } catch {
    return iso
  }
}

/** Relative time — "3 minutes ago" */
export function timeAgo(iso: string | undefined | null): string {
  if (!iso) return '—'
  try {
    return formatDistanceToNow(parseISO(iso), { addSuffix: true })
  } catch {
    return iso
  }
}

/** Format ISO to short date "MMM d" */
export function formatShortDate(iso: string): string {
  try {
    return format(parseISO(iso), 'MMM d')
  } catch {
    return iso
  }
}

/** Format a monetary value (portfolio $ amounts) — always 2 decimal places */
export function formatCurrency(value: number, currency = 'INR'): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

/** Format a percentage with sign (e.g. +12.34%) */
export function formatPercent(value: number): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

// ─── Color Helpers ────────────────────────────────────────────────────────────

/** Tailwind text color class for a positive/negative change */
export function changeColor(value: number): string {
  if (value > 0) return 'text-profit'
  if (value < 0) return 'text-loss'
  return 'text-gray-400'
}

/** Arrow indicator for a change direction */
export function changeArrow(value: number): string {
  if (value > 0) return '▲'
  if (value < 0) return '▼'
  return '—'
}

// ─── String Helpers ───────────────────────────────────────────────────────────

/** Truncate a string to a maximum length */
export function truncate(str: string, maxLen = 30): string {
  if (!str) return ''
  return str.length > maxLen ? str.slice(0, maxLen - 1) + '…' : str
}

/** Convert camelCase or UPPER_SNAKE to human-readable label */
export function humanize(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^\w/, (c) => c.toUpperCase())
}
