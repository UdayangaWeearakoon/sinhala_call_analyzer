import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { OverviewPage } from './pages/OverviewPage'
import { useState } from 'react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function ErrorBoundary({ children }: { children: React.ReactNode }) {
  const [hasError, setHasError] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  if (hasError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-lg w-full">
          <h2 className="text-xl font-bold text-red-600 mb-4">Something went wrong</h2>
          <pre className="bg-gray-100 p-4 rounded text-sm text-gray-800 overflow-auto max-h-64">
            {error?.message}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Reload
          </button>
        </div>
      </div>
    )
  }

  return (
    <div onError={(e) => { setHasError(true); setError(e.error as Error) }}>
      {children}
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white border-b border-gray-200 shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-sm">SC</span>
                  </div>
                  <h1 className="text-xl font-bold text-gray-900">Sinhala Call Analytics</h1>
                </div>
                <nav className="flex items-center gap-4">
                  <button className="px-3 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg">
                    Overview
                  </button>
                  <button className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
                    Sentiment
                  </button>
                  <button className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
                    Categories
                  </button>
                  <button className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
                    Call Log
                  </button>
                </nav>
              </div>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <OverviewPage />
          </main>
        </div>
      </ErrorBoundary>
    </QueryClientProvider>
  )
}

export default App
