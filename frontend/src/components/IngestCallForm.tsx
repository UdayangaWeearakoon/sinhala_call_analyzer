import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ingestCall } from '../api'
import type { CallResponse } from '../types'
import { Loader2, CheckCircle, AlertCircle, ChevronDown, ChevronUp, FileText, Upload } from 'lucide-react'

export function IngestCallForm() {
  const queryClient = useQueryClient()
  const [transcript, setTranscript] = useState('')
  const [selectedFileName, setSelectedFileName] = useState('')
  const [fileError, setFileError] = useState('')
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
    mutation.mutate({
      transcript: transcript.trim(),
      source_file_name: selectedFileName || null,
    })
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    setFileError('')
    setResult(null)

    if (!file) {
      setSelectedFileName('')
      return
    }

    const isTextFile = file.type === 'text/plain' || file.name.toLowerCase().endsWith('.txt')
    if (!isTextFile) {
      setSelectedFileName('')
      setTranscript('')
      setFileError('Please upload a .txt text file.')
      e.target.value = ''
      return
    }

    try {
      const text = await file.text()
      if (!text.trim()) {
        setSelectedFileName('')
        setTranscript('')
        setFileError('The uploaded file does not contain any text.')
        e.target.value = ''
        return
      }

      setSelectedFileName(file.name)
      setTranscript(text)
    } catch {
      setSelectedFileName('')
      setTranscript('')
      setFileError('Could not read this text file. Please try another file.')
      e.target.value = ''
    }
  }

  const clearForm = () => {
    setTranscript('')
    setSelectedFileName('')
    setFileError('')
    setResult(null)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Ingest New Call</h3>
      <p className="text-sm text-gray-500 mb-4">Upload a Sinhala call transcript text file, then run ML inference and save to the database.</p>

      <form onSubmit={handleSubmit}>
        <label className="mb-4 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 px-4 py-6 text-center transition-colors hover:border-indigo-400 hover:bg-indigo-50">
          <Upload className="mb-2 h-6 w-6 text-indigo-600" />
          <span className="text-sm font-medium text-gray-900">Upload Sinhala transcript file</span>
          <span className="mt-1 text-xs text-gray-500">Only .txt files are supported</span>
          <input
            type="file"
            accept=".txt,text/plain"
            onChange={handleFileChange}
            className="sr-only"
          />
        </label>

        {selectedFileName && (
          <div className="mb-3 flex items-center gap-2 rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-sm text-indigo-800">
            <FileText className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">{selectedFileName}</span>
            <span className="ml-auto text-xs text-indigo-600">{transcript.trim().length} characters extracted</span>
          </div>
        )}

        {fileError && (
          <div className="mb-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <span>{fileError}</span>
          </div>
        )}

        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder="Extracted Sinhala transcript will appear here..."
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
            onClick={clearForm}
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
