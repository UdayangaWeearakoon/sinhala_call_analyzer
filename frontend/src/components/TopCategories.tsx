import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts'
import type { CategoryCount } from '../types'

interface TopCategoriesProps {
  data: CategoryCount[]
}

export function TopCategories({ data }: TopCategoriesProps) {
  const sorted = [...data]
    .filter((d) => d.category !== 'string')
    .sort((a, b) => b.count - a.count)
    .slice(0, 8)

  const COLORS = [
    '#6366f1',
    '#8b5cf6',
    '#a78bfa',
    '#3b82f6',
    '#2563eb',
    '#1d4ed8',
    '#7c3aed',
    '#4f46e5',
  ]

  if (sorted.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Categories This Month</h3>
        <div className="flex items-center justify-center h-72 text-gray-400">No category data available</div>
      </div>
    )
  }

  const chartHeight = sorted.length * 40 + 60

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Categories This Month</h3>
      <div style={{ width: '100%', height: `${Math.max(chartHeight, 288)}px` }}>
        <BarChart
          width={600}
          height={Math.max(chartHeight, 288)}
          data={sorted}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis type="number" tick={{ fontSize: 12 }} />
          <YAxis dataKey="category" type="category" tick={{ fontSize: 11 }} width={100} />
          <Tooltip />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {sorted.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </div>
    </div>
  )
}
