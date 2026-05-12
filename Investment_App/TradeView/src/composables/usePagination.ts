import { computed, type Ref } from 'vue'

interface UsePaginationOptions {
  total: Ref<number>
  page: Ref<number>
  pageSize: Ref<number>
  maxPages?: number
}

/**
 * Provides computed pagination metadata and page-range generation
 * for use with the Pagination component.
 */
export function usePagination({ total, page, pageSize, maxPages = 7 }: UsePaginationOptions) {
  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

  const hasPrev = computed(() => page.value > 1)
  const hasNext = computed(() => page.value < totalPages.value)

  const startItem = computed(() => Math.min((page.value - 1) * pageSize.value + 1, total.value))
  const endItem   = computed(() => Math.min(page.value * pageSize.value, total.value))

  /** Page numbers array with ellipsis markers (0 = ellipsis) */
  const pages = computed<number[]>(() => {
    const tp = totalPages.value
    if (tp <= maxPages) return Array.from({ length: tp }, (_, i) => i + 1)

    const half = Math.floor(maxPages / 2)
    let start = Math.max(2, page.value - half)
    let end   = Math.min(tp - 1, page.value + half)

    if (page.value <= half + 1) {
      start = 2
      end   = maxPages - 2
    } else if (page.value >= tp - half) {
      start = tp - maxPages + 3
      end   = tp - 1
    }

    const result: number[] = [1]
    if (start > 2)  result.push(0) // left ellipsis
    for (let i = start; i <= end; i++) result.push(i)
    if (end < tp - 1) result.push(0) // right ellipsis
    result.push(tp)
    return result
  })

  return { totalPages, hasPrev, hasNext, startItem, endItem, pages }
}
