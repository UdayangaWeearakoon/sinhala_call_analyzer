import { AlertCircle, Loader2, MessageCircle, Smile, Meh, Frown } from 'lucide-react'
import { useOverview } from '../hooks/useApi'

function formatPercent(value: number) {
  return `${Math.round(value)}%`
}

function SentimentStatCard({
  label,
  value,
  count,
  tone,
  icon: Icon,
}: {
  label: string
  value: number
  count: number
  tone: string
  icon: typeof Smile
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500">{label}</p>
        <span className={`inline-flex h-10 w-10 items-center justify-center rounded-lg ${tone}`}>
          <Icon className="h-5 w-5" />
        </span>
      </div>
      <p className="mt-3 text-3xl font-bold text-gray-900">{formatPercent(value)}</p>
      <p className="mt-1 text-sm text-gray-500">{count} calls</p>
    </div>
  )
}

export function SentimentPage() {
  const { data: overview, isPending, error } = useOverview()

  if (isPending) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        <p className="text-gray-500 text-sm">Loading sentiment insights...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="w-10 h-10 text-red-500" />
        <p className="text-red-600 font-medium">Failed to load sentiment data</p>
        <p className="text-gray-500 text-sm">{error.message}</p>
      </div>
    )
  }

  if (!overview) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="w-10 h-10 text-amber-500" />
        <p className="text-gray-600">No sentiment data available</p>
      </div>
    )
  }

  const positiveCount = overview.sentiment_distribution.Positive || 0
  const neutralCount = overview.sentiment_distribution.Neutral || 0
  const negativeCount =
    (overview.sentiment_distribution.Negative || 0) +
    (overview.sentiment_distribution['Very Negative'] || 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Sentiment Analysis</h2>
          <p className="text-gray-500 mt-1">Track customer mood across analyzed Sinhala support calls</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm text-gray-600 shadow-sm">
          <MessageCircle className="h-4 w-4 text-indigo-500" />
          <span>{overview.total_calls_this_month} calls this month</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <SentimentStatCard
          label="Positive"
          value={overview.positive_percentage}
          count={positiveCount}
          tone="bg-emerald-100 text-emerald-700"
          icon={Smile}
        />
        <SentimentStatCard
          label="Neutral"
          value={overview.neutral_percentage}
          count={neutralCount}
          tone="bg-sky-100 text-sky-700"
          icon={Meh}
        />
        <SentimentStatCard
          label="Negative"
          value={overview.negative_percentage}
          count={negativeCount}
          tone="bg-rose-100 text-rose-700"
          icon={Frown}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900">Sentiment Split</h3>
          <p className="mt-2 text-sm text-gray-500">
            Add the sentiment donut chart component here in Part 2.
          </p>
        </section>
        <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900">Sentiment Trend</h3>
          <p className="mt-2 text-sm text-gray-500">
            Add the sentiment trend chart component here in Part 2.
          </p>
        </section>
      </div>

      <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900">Negative Call Review</h3>
        <p className="mt-2 text-sm text-gray-500">
          Add the filtered negative calls list here in Part 2.
        </p>
      </section>
    </div>
  )
}
