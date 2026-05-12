import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ingestCall } from '../api'
import type { CallResponse } from '../types'
import { Loader2, CheckCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'

export function IngestCallForm() {
  const queryClient = useQueryClient()
  const [transcript, setTranscript] = useState('')
  const [result, setResult] = useState<CallResponse | null>(null)
  const [expanded, setExpanded] = useState(false)

  const mutation = useMutation({
    mutationFn: ingestCall,
    onSuccess: (data) => {
      setResult(data)
      queryClient.invalidateQueries({ queryKey: ['overview'] })
      queryClient.invalidateQueries({ queryKey: ['calls'] })
      queryClient.invalidateQueries({ queryKey: ['top-categories'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!transcript.trim()) return
    mutation.mutate({ transcript: transcript.trim() })
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Ingest New Call</h3>
      <p className="text-sm text-gray-500 mb-4">Paste a Sinhala call transcript below to run ML inference and save to the database.</p>

      <form onSubmit={handleSubmit}>
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder="Enter Sinhala transcript here..."
          className="w-full border border-gray-300 rounded-lg p-3 text-sm min-h-32 resize-y focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          rows={6}
        />

        <div className="mt-3 flex gap-3">
          <button
            type="submit"
            disabled={mutation.isPending || !transcript.trim()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {mutation.isPending ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </span>
            ) : (
              'Analyze & Save'
            )}
          </button>

          <button
            type="button"
            onClick={() => { setTranscript(''); setResult(null); }}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
          >
            Clear
          </button>
        </div>
      </form>

      {mutation.error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Failed to ingest call</p>
            <p className="text-xs text-red-600 mt-1">{mutation.error.message}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-green-800">Successfully analyzed and saved (ID: {result.id})</p>

              <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Category</p>
                   <p className="font-semibold text-gray-900">{result.category}</p>
                   <p className="text-xs text-gray-500">{(result.category_confidence * 100).toFixed(1)}% confidence</p>
                </div>
                <div>
                  <p className="text-gray-500">Sentiment</p>
                  <p className={`font-semibold ${result.sentiment === 'Negative' || result.sentiment === 'Very Negative' ? 'text-red-700' : result.sentiment === 'Positive' ? 'text-green-700' : 'text-gray-700'}`}>
                    {result.sentiment}
                  </p>
                   <p className="text-xs text-gray-500">{(result.sentiment_confidence * 100).toFixed(1)}% confidence</p>
                </div>
              </div>

              <button
                onClick={() => setExpanded(!expanded)}
                className="mt-3 flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium"
              >
                {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {expanded ? 'Hide details' : 'Show all details'}
              </button>

              {expanded && (
                <div className="mt-3 pt-3 border-t border-green-200 text-xs text-gray-600 space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <p><span className="text-gray-500">Timestamp:</span> {new Date(result.timestamp).toLocaleString()}</p>
                    <p><span className="text-gray-500">Resolved:</span> {result.resolved ? 'Yes' : 'No'}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
