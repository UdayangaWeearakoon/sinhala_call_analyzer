import { useState, type ChangeEvent, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ingestCall } from '../api'
import type { CallResponse } from '../types'
import { Loader2, CheckCircle, AlertCircle, ChevronDown, ChevronUp, Upload } from 'lucide-react'

export function IngestCallForm() {
  const queryClient = useQueryClient()
  const [transcript, setTranscript] = useState('')
  const [fileName, setFileName] = useState<string | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
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

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!transcript.trim()) return
    mutation.mutate({ transcript: transcript.trim() })
  }

  const processTextFile = (file: File) => {
    if (!file.type.startsWith('text/') && !file.name.endsWith('.txt')) {
      setFileError('Only plain text files are supported.')
      return
    }

    setFileError(null)
    setFileName(file.name)

    const reader = new FileReader()
    reader.onload = () => {
      setTranscript((reader.result as string) || '')
    }
    reader.onerror = () => {
      setFileError('Unable to read the selected file. Please try another file.')
    }
    reader.readAsText(file, 'UTF-8')
  }

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      processTextFile(file)
    }
    e.target.value = ''
  }

  return (
    <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Ingest New Call</h3>
      <p className="text-sm text-slate-500 mb-5">
        Paste a Sinhala call transcript below or upload a transcript file directly.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="relative mb-4">
          <input
            id="call-file-upload"
            type="file"
            accept=".txt,text/plain"
            className="sr-only"
            onChange={handleFileChange}
          />

          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Enter Sinhala transcript or add transcript file..."
            className="w-full min-h-[220px] rounded-3xl border border-gray-200 bg-slate-50 px-6 py-5 pr-36 text-sm text-slate-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 transition duration-150 resize-none"
          />

          <label
            htmlFor="call-file-upload"
            className="absolute left-4 bottom-4 inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:shadow-md hover:text-blue-700 cursor-pointer"
          >
            <Upload className="h-4 w-4" />
            Upload
          </label>
        </div>

        {fileName && (
          <div className="mb-4 rounded-2xl border border-gray-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Loaded file: <span className="font-medium text-slate-900">{fileName}</span>
          </div>
        )}

        {fileError && (
          <div className="mb-4 text-sm text-red-600">{fileError}</div>
        )}

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <button
            type="submit"
            disabled={mutation.isPending || !transcript.trim()}
            className="inline-flex items-center justify-center rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
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
            onClick={() => {
              setTranscript('')
              setFileName(null)
              setFileError(null)
              setResult(null)
            }}
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
