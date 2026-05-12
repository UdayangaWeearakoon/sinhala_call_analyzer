import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { format, parseISO, isValid } from 'date-fns'
import type { SentimentTrendEntry } from '../types'

const COLORS: Record<string, string> = {
  Positive: '#22c55e',
  Neutral: '#94a3b8',
  Negative: '#ef4444',
  'Very Negative': '#991b1b',
}

interface SentimentTrendProps {
  data: SentimentTrendEntry[]
}

export function SentimentTrend({ data }: SentimentTrendProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Trend (Last 30 Days)</h3>
        <div className="flex items-center justify-center h-72 text-gray-400">No trend data available</div>
      </div>
    )
  }

  const formatted = data
    .filter((entry) => {
      const d = parseISO(entry.date)
      return isValid(d)
    })
    .map((entry) => ({
      date: format(parseISO(entry.date), 'MMM dd'),
      Positive: entry.Positive ?? 0,
      Neutral: entry.Neutral ?? 0,
      Negative: entry.Negative ?? 0,
      'Very Negative': entry['Very Negative'] ?? 0,
    }))

  if (formatted.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Trend (Last 30 Days)</h3>
        <div className="flex items-center justify-center h-72 text-gray-400">No valid trend data available</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Trend (Last 30 Days)</h3>
      <div className="flex justify-center">
        <LineChart width={580} height={280} data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          {Object.keys(COLORS).map((key) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={COLORS[key]}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </div>
    </div>
  )
}
