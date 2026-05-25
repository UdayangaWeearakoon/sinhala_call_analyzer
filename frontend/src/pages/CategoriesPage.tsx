import { useMemo, useState } from 'react'
import { useCalls, useTopCategories } from '../hooks/useApi'
import { AlertCircle, ArrowRight, BarChart3, Grid3X3, Loader2, Search, Tags } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function formatPercent(value: number) {
  return `${Math.round(value)}%`
}

function CategoryBadge({ index }: { index: number }) {
  const colors = [
    'bg-indigo-100 text-indigo-700',
    'bg-sky-100 text-sky-700',
    'bg-emerald-100 text-emerald-700',
    'bg-amber-100 text-amber-700',
    'bg-rose-100 text-rose-700',
    'bg-violet-100 text-violet-700',
  ]

  return (
    <span className={`inline-flex h-10 w-10 items-center justify-center rounded-lg ${colors[index % colors.length]}`}>
      <Tags className="h-5 w-5" />
    </span>
  )
}

export function CategoriesPage() {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>()

  const { data: categories, isPending, error } = useTopCategories(50)
  const { data: relatedCalls, isPending: loadingCalls } = useCalls({
    page: 1,
    page_size: 6,
    category: selectedCategory,
  })

  const cleanCategories = useMemo(() => {
    return (categories || [])
      .filter((category) => category.category && category.category !== 'string')
      .sort((a, b) => b.count - a.count)
  }, [categories])

  const totalCalls = cleanCategories.reduce((sum, item) => sum + item.count, 0)
  const filteredCategories = cleanCategories.filter((item) =>
    item.category.toLowerCase().includes(searchTerm.trim().toLowerCase()),
  )
  const topCategory = cleanCategories[0]

  if (isPending) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        <p className="text-gray-500 text-sm">Loading categories...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="w-10 h-10 text-red-500" />
        <p className="text-red-600 font-medium">Failed to load categories</p>
        <p className="text-gray-500 text-sm">{error.message}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Categories Catalogue</h2>
          <p className="text-gray-500 mt-1">Browse analyzed call categories and open matching call records</p>
        </div>
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search categories..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Total Categories</p>
            <Grid3X3 className="h-5 w-5 text-indigo-500" />
          </div>
          <p className="mt-3 text-3xl font-bold text-gray-900">{cleanCategories.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Categorized Calls</p>
            <BarChart3 className="h-5 w-5 text-sky-500" />
          </div>
          <p className="mt-3 text-3xl font-bold text-gray-900">{totalCalls}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Top Category</p>
            <Tags className="h-5 w-5 text-emerald-500" />
          </div>
          <p className="mt-3 truncate text-2xl font-bold text-gray-900">{topCategory?.category || '-'}</p>
        </div>
      </div>

      {cleanCategories.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-12 text-center">
          <Tags className="mx-auto h-10 w-10 text-gray-300" />
          <p className="mt-3 text-sm text-gray-500">No category data available</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredCategories.map((item, index) => {
              const percentage = totalCalls ? (item.count / totalCalls) * 100 : 0
              const isSelected = selectedCategory === item.category

              return (
                <button
                  key={item.category}
                  type="button"
                  onClick={() => setSelectedCategory(item.category)}
                  className={`bg-white rounded-xl border p-5 text-left shadow-sm transition-colors hover:border-indigo-200 hover:bg-indigo-50/30 ${
                    isSelected ? 'border-indigo-300 ring-2 ring-indigo-100' : 'border-gray-100'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <CategoryBadge index={index} />
                    <span className="text-xs font-semibold text-gray-400">#{index + 1}</span>
                  </div>
                  <h3 className="mt-4 text-base font-semibold text-gray-900">{item.category}</h3>
                  <div className="mt-4 flex items-center justify-between text-sm">
                    <span className="font-medium text-gray-700">{item.count} calls</span>
                    <span className="text-gray-500">{formatPercent(percentage)}</span>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100">
                    <div className="h-full rounded-full bg-indigo-500" style={{ width: `${Math.max(percentage, 4)}%` }} />
                  </div>
                </button>
              )
            })}
          </div>

          <aside className="bg-white rounded-xl border border-gray-100 shadow-sm">
            <div className="border-b border-gray-100 p-5">
              <p className="text-sm font-medium text-gray-500">Selected Category</p>
              <h3 className="mt-1 text-lg font-semibold text-gray-900">{selectedCategory || 'Choose a category'}</h3>
            </div>

            {!selectedCategory ? (
              <div className="p-5 text-sm text-gray-500">
                Select a category card to preview the most recent matching calls.
              </div>
            ) : loadingCalls ? (
              <div className="flex h-48 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
              </div>
            ) : !relatedCalls || relatedCalls.calls.length === 0 ? (
              <div className="p-5 text-sm text-gray-500">No calls found for this category.</div>
            ) : (
              <div className="divide-y divide-gray-100">
                {relatedCalls.calls.map((call) => (
                  <button
                    key={call.id}
                    type="button"
                    onClick={() => navigate(`/calls/${call.id}`)}
                    className="w-full p-5 text-left transition-colors hover:bg-gray-50"
                  >
                    <p className="line-clamp-2 text-sm text-gray-700">{call.transcript}</p>
                    <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                      <span>{call.sentiment}</span>
                      <ArrowRight className="h-4 w-4" />
                    </div>
                  </button>
                ))}
                <div className="p-5">
                  <button
                    type="button"
                    onClick={() => navigate(`/calls?category=${encodeURIComponent(selectedCategory)}`)}
                    className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
                  >
                    View all matching calls
                  </button>
                </div>
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  )
}
