import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import type { Call } from '../types'

interface RecentCallsProps {
  calls: Call[]
}

const sentimentColors: Record<string, string> = {
  Positive: 'bg-green-100 text-green-800',
  Neutral: 'bg-gray-100 text-gray-800',
  Negative: 'bg-red-100 text-red-800',
  'Very Negative': 'bg-red-200 text-red-900',
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = (value * 100).toFixed(0)
  const color =
    value >= 0.8 ? 'bg-green-500' :
    value >= 0.6 ? 'bg-amber-500' :
    'bg-red-500'

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 tabular-nums">{pct}%</span>
    </div>
  )
}

export function RecentCalls({ calls }: RecentCallsProps) {
  const navigate = useNavigate()

  if (!calls || calls.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Calls</h3>
        <div className="flex items-center justify-center h-40 text-gray-400">No calls found</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Calls</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-medium text-gray-500">Transcript</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Category</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Sentiment</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Cat. Confidence</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Sent. Confidence</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Time</th>
            </tr>
          </thead>
          <tbody>
            {calls.map((call) => (
              <tr key={call.id} className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/calls/${call.id}`)}>
                <td className="py-3 px-4 max-w-xs truncate text-gray-700 flex items-center gap-1.5">
                  {call.category_confidence < 0.7 || call.sentiment_confidence < 0.7 ? (
                    <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" title="Low confidence prediction" />
                  ) : null}
                  <span className="truncate">
                    {call.transcript.substring(0, 60)}
                    {call.transcript.length > 60 ? '...' : ''}
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-700">{call.category}</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${sentimentColors[call.sentiment] || 'bg-gray-100 text-gray-800'}`}>
                    {call.sentiment}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <ConfidenceBar value={call.category_confidence} />
                </td>
                <td className="py-3 px-4">
                  <ConfidenceBar value={call.sentiment_confidence} />
                </td>
                <td className="py-3 px-4 text-gray-500 whitespace-nowrap">
                  {format(new Date(call.timestamp), 'MMM dd HH:mm')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
