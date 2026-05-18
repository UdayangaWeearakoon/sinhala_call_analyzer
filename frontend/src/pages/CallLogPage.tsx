import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCalls, useTopCategories } from '../hooks/useApi'
import { format } from 'date-fns'
import { Search, ChevronLeft, ChevronRight, RotateCcw, Loader2, AlertCircle, AlertTriangle } from 'lucide-react'
import type { CallFilters } from '../types'

const sentimentOptions = ['', 'Positive', 'Neutral', 'Negative', 'Very Negative']

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
      <div className="w-14 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 tabular-nums">{pct}%</span>
    </div>
  )
}

export function CallLogPage() {
  const navigate = useNavigate()

  const [filters, setFilters] = useState<CallFilters>({ page: 1, page_size: 10 })
  const [searchTerm, setSearchTerm] = useState('')

  const { data: topCategories } = useTopCategories(50)

  const queryFilters = { ...filters }
  if (searchTerm.trim()) {
    queryFilters.category = searchTerm.trim()
  }

  const { data, isPending, error } = useCalls(queryFilters)

  const totalPages = data ? Math.max(1, Math.ceil(data.total / (filters.page_size || 20))) : 1

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Call Log</h2>
        <p className="text-gray-500 mt-1">Search and filter all analyzed calls</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Category</label>
            <select
              value={filters.category || ''}
              onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value || undefined, page: 1 }))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="">All Categories</option>
              {topCategories?.map((c) => (
                <option key={c.category} value={c.category}>{c.category} ({c.count})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Sentiment</label>
            <select
              value={filters.sentiment || ''}
              onChange={(e) => setFilters((f) => ({ ...f, sentiment: e.target.value || undefined, page: 1 }))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              {sentimentOptions.map((s) => (
                <option key={s} value={s}>{s || 'All Sentiments'}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Date From</label>
            <input
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value || undefined, page: 1 }))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Date To</label>
            <input
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value || undefined, page: 1 }))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-end gap-2">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Quick Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Category name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => { setFilters({ page: 1, page_size: 10 }); setSearchTerm('') }}
              className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
            >
              <RotateCcw className="w-4 h-4" /> Clear Filter
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        {isPending ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-64 gap-3">
            <AlertCircle className="w-8 h-8 text-red-500" />
            <p className="text-red-600 text-sm">{error.message}</p>
          </div>
        ) : !data || data.calls.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 gap-3">
            <Search className="w-8 h-8 text-gray-300" />
            <p className="text-gray-500 text-sm">No calls match your filters</p>
            <button
              onClick={() => { setFilters({ page: 1, page_size: 10 }); setSearchTerm('') }}
              className="text-indigo-600 text-sm hover:underline"
            >
              Clear all filters
            </button>
          </div>
        ) : (
          <>
            <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Showing <span className="font-medium text-gray-700">{data.calls.length}</span> of{' '}
                <span className="font-medium text-gray-700">{data.total}</span> calls
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Transcript</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Category</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Sentiment</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Cat. Confidence</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Sent. Confidence</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Phone</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {data.calls.map((call) => (
                    <tr
                      key={call.id}
                      className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => navigate(`/calls/${call.id}`)}
                    >
                      <td className="py-3 px-4 max-w-xs truncate text-gray-700">
                        <span className="flex items-center gap-1.5">
                          {call.category_confidence < 0.7 || call.sentiment_confidence < 0.7 ? (
                            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" title="Low confidence prediction" />
                          ) : null}
                          <span className="truncate">
                            {call.transcript.substring(0, 60)}
                            {call.transcript.length > 60 ? '...' : ''}
                          </span>
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
                      <td className="py-3 px-4 text-gray-500 text-xs">
                        {call.customer_phone || '—'}
                      </td>
                      <td className="py-3 px-4 text-gray-500 whitespace-nowrap text-xs">
                        {format(new Date(call.timestamp), 'MMM dd HH:mm')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Page {data.page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <button
                  disabled={data.page <= 1}
                  onClick={() => setFilters((f) => ({ ...f, page: (f.page || 1) - 1 }))}
                  className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors flex items-center gap-1"
                >
                  <ChevronLeft className="w-4 h-4" /> Previous
                </button>
                <button
                  disabled={data.page >= totalPages}
                  onClick={() => setFilters((f) => ({ ...f, page: (f.page || 1) + 1 }))}
                  className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors flex items-center gap-1"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}