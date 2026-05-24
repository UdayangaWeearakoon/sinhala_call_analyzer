export interface CallResponse {
  id: string
  transcript: string
  source_file_name: string | null
  category: string
  sentiment: string
  category_confidence: number
  sentiment_confidence: number
  timestamp: string
  call_duration: number | null
  customer_phone: string | null
  resolved: boolean
  resolution_time: number | null
  notes: string | null
}

export interface CallIngestRequest {
  transcript: string
  source_file_name?: string | null
  call_duration?: number | null
  customer_phone?: string | null
  resolved?: boolean
  notes?: string | null
}

export interface Call {
  id: string
  transcript: string
  source_file_name: string | null
  category: string
  sentiment: string
  category_confidence: number
  sentiment_confidence: number
  timestamp: string
  call_duration: number | null
  customer_phone: string | null
  resolved: boolean
  resolution_time: number | null
  notes: string | null
}

export interface CallListResponse {
  calls: Call[]
  total: number
  page: number
  page_size: number
}

export interface OverviewStats {
  total_calls_today: number
  total_calls_yesterday: number
  total_calls_this_month: number
  resolution_rate: number
  positive_percentage: number
  negative_percentage: number
  neutral_percentage: number
  category_distribution: Record<string, number>
  sentiment_distribution: Record<string, number>
  sentiment_trend: SentimentTrendEntry[]
}

export interface SentimentTrendEntry {
  date: string
  [key: string]: string | number
}

export interface CategoryCount {
  category: string
  count: number
}

export interface CallFilters {
  page?: number
  page_size?: number
  date_from?: string
  date_to?: string
  category?: string
  sentiment?: string
}
