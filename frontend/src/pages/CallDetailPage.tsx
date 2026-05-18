import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchCallById } from '../api'
import { format } from 'date-fns'
import { ArrowLeft, Phone, Clock, CheckCircle, XCircle, User, FileText } from 'lucide-react'

const sentimentColors: Record<string, string> = {
  Positive: 'bg-green-100 text-green-800',
  Neutral: 'bg-gray-100 text-gray-800',
  Negative: 'bg-red-100 text-red-800',
  'Very Negative': 'bg-red-200 text-red-900',
}

function ConfidenceGauge({ label, value }: { label: string; value: number }) {
  const pct = (value * 100).toFixed(1)
  const color =
    value >= 0.8 ? 'text-green-600' :
    value >= 0.6 ? 'text-amber-600' :
    'text-red-600'
  const barColor =
    value >= 0.8 ? 'bg-green-500' :
    value >= 0.6 ? 'bg-amber-500' :
    'bg-red-500'

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
      <p className="text-sm text-gray-500 mb-2">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{pct}%</p>
      <div className="mt-3 h-2.5 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export function CallDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: call, isPending, error } = useQuery({
    queryKey: ['call', id],
    queryFn: () => fetchCallById(id!),
    enabled: !!id,
  })

  if (isPending) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (error || !call) {
    return (
      <div className="max-w-3xl mx-auto mt-12 p-8">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="bg-white rounded-xl border border-gray-100 p-8 text-center shadow-sm">
          <p className="text-red-600 font-medium">Failed to load call details</p>
          <p className="text-gray-500 text-sm mt-2">{error?.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </button>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Call Analysis</h2>
            <p className="text-sm text-gray-500 mt-1">
              {format(new Date(call.timestamp), 'MMM dd, yyyy HH:mm')}
            </p>
          </div>
          <span className={`px-3 py-1.5 rounded-full text-sm font-medium ${sentimentColors[call.sentiment] || 'bg-gray-100 text-gray-800'}`}>
            {call.sentiment}
          </span>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4" /> Transcript
            </h3>
            <div className="bg-gray-50 rounded-lg p-4 text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
              {call.transcript}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
              AI Predictions
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <ConfidenceGauge label={`Category — ${call.category}`} value={call.category_confidence} />
              <ConfidenceGauge label={`Sentiment — ${call.sentiment}`} value={call.sentiment_confidence} />
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Call Metadata
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                  <Phone className="w-3.5 h-3.5" /> Phone
                </div>
                <p className="text-sm font-medium text-gray-900">
                  {call.customer_phone || '—'}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                  <Clock className="w-3.5 h-3.5" /> Duration
                </div>
                <p className="text-sm font-medium text-gray-900">
                  {call.call_duration ? `${call.call_duration}s` : '—'}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                  {call.resolved ? <CheckCircle className="w-3.5 h-3.5 text-green-500" /> : <XCircle className="w-3.5 h-3.5 text-red-400" />} Resolved
                </div>
                <p className={`text-sm font-medium ${call.resolved ? 'text-green-600' : 'text-red-500'}`}>
                  {call.resolved ? 'Yes' : 'No'}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                  <User className="w-3.5 h-3.5" /> Category
                </div>
                <p className="text-sm font-medium text-gray-900">{call.category}</p>
              </div>
            </div>
          </div>

          {call.notes && (
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Notes</h3>
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700">
                {call.notes}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}