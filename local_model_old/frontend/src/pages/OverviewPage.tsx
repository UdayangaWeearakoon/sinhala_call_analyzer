import { useState, useEffect } from 'react'
import { useOverview, useCalls, useTopCategories } from '../hooks/useApi'
import { KpiCards } from '../components/KpiCards'
import { SentimentDonut } from '../components/SentimentDonut'
import { SentimentTrend } from '../components/SentimentTrend'
import { TopCategories } from '../components/TopCategories'
import { RecentCalls } from '../components/RecentCalls'
import { IngestCallForm } from '../components/IngestCallForm'
import { Loader2, AlertCircle } from 'lucide-react'

export function OverviewPage() {
  const { data: overview, isPending: loadingOverview, error: overviewError } = useOverview()
  const { data: callsData, isPending: loadingCalls, error: callsError } = useCalls({ page: 1, page_size: 5 })
  const { data: topCategories, isPending: loadingCategories } = useTopCategories(10)

  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (loadingOverview || loadingCalls || loadingCategories) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        <p className="text-gray-500 text-sm">Loading...</p>
      </div>
    )
  }

  if (overviewError || callsError) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="w-10 h-10 text-red-500" />
        <p className="text-red-600 font-medium">Failed to load data</p>
        <p className="text-gray-500 text-sm text-center">
          {overviewError?.message || callsError?.message}
        </p>
        <p className="text-gray-400 text-xs">Check that backend is running on port 8002</p>
      </div>
    )
  }

  if (!overview || !callsData || !topCategories) {
    return (
      <div className="glass-card flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="w-10 h-10 text-amber-500" />
        <p className="text-gray-600">No data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
        <p className="text-gray-500 mt-1">Sinhala Call Analytics — Real-time insights</p>
      </div>

      <IngestCallForm />

      <KpiCards
        totalCallsToday={overview.total_calls_today}
        totalCallsYesterday={overview.total_calls_yesterday}
        totalCallsThisMonth={overview.total_calls_this_month}
        positivePercentage={overview.positive_percentage}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SentimentTrend data={overview.sentiment_trend} />
        <div className="flex flex-col gap-6">
          <SentimentDonut data={overview.sentiment_distribution} />
          <TopCategories data={topCategories} />
        </div>
      </div>

      <RecentCalls calls={callsData.calls} />
    </div>
  )
}
