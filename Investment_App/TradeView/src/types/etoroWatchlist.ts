// src/types/etoroWatchlist.ts

export interface WatchlistItem {
  item_id:   number
  item_type: string   // "Instrument"
  item_rank: number
}

export interface Watchlist {
  watchlist_id:             string
  name:                     string
  gcid:                     number | null
  watchlist_type:           string   // "Static" | "Dynamic"
  total_items:              number
  is_default:               boolean
  is_user_selected_default: boolean
  rank:                     number
  dynamic_url:              string | null
  items:                    WatchlistItem[]
  related_assets:           number[]
}

export interface WatchlistsMeta {
  page_number:                  number
  items_per_page:               number
  max_items_in_watchlist_limit: number
  max_watchlists_limit:         number
}

export interface WatchlistsResponse {
  watchlists:   Watchlist[]
  meta:         WatchlistsMeta | null
  is_succeeded: boolean
  total:        number
}

export interface WatchlistsParams {
  items_per_page?:    number
  ensure_builtin?:    boolean
  add_related_assets?: boolean
}
