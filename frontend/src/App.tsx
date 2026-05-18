import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { OverviewPage } from './pages/OverviewPage'
import { CallDetailPage } from './pages/CallDetailPage'
import { CallLogPage } from './pages/CallLogPage'
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

function NavLink({ to, label }: { to: string; label: string }) {
  const location = useLocation()
  const active = location.pathname === to || (to === '/' && location.pathname === '/')
  return (
    <Link
      to={to}
      className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
        active
          ? 'text-indigo-600 bg-indigo-50'
          : 'text-gray-500 hover:text-gray-700'
      }`}
    >
      {label}
    </Link>
  )
}

function Header() {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">SC</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900">Sinhala Call Analytics</h1>
          </Link>
          <nav className="flex items-center gap-4">
            <NavLink to="/" label="Overview" />
            <NavLink to="/sentiment" label="Sentiment" />
            <NavLink to="/categories" label="Categories" />
            <NavLink to="/calls" label="Call Log" />
          </nav>
        </div>
      </div>
    </header>
  )
}

function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/calls" element={<CallLogPage />} />
          <Route path="/calls/:id" element={<CallDetailPage />} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <BrowserRouter>
          <Layout />
        </BrowserRouter>
      </ErrorBoundary>
    </QueryClientProvider>
  )
}

export default App
