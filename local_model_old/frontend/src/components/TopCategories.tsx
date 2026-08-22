import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { CategoryCount } from '../types'

const GRADIENTS: Record<string, { from: string; to: string }> = {
  'Technical Support': { from: '#6366f1', to: '#4f46e5' },
  'Account Management': { from: '#a855f7', to: '#9333ea' },
}

interface TopCategoriesProps {
  data: CategoryCount[]
}

export function TopCategories({ data }: TopCategoriesProps) {
  const sorted = [...data]
    .filter((d) => d.category !== 'string')
    .sort((a, b) => b.count - a.count)
    .slice(0, 8)

  if (sorted.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Categories This Month</h3>
        <div className="flex items-center justify-center h-72 text-gray-400">No category data available</div>
      </div>
    )
  }

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Categories This Month</h3>
      <div style={{ width: '100%', height: 150 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={sorted}
            margin={{ top: 20, right: 20, left: 20, bottom: 8 }}
          >
            <defs>
              {sorted.map((d, i) => {
                const g = GRADIENTS[d.category] || { from: '#6366f1', to: '#4f46e5' }
                return (
                  <linearGradient key={`grad-${i}`} id={`bar-grad-${i}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={g.from} stopOpacity={1} />
                    <stop offset="100%" stopColor={g.to} stopOpacity={0.75} />
                  </linearGradient>
                )
              })}
            </defs>
            <XAxis
              dataKey="category"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                background: 'rgba(255,255,255,0.9)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(255,255,255,0.5)',
                borderRadius: '0.75rem',
                boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
              }}
              cursor={{ fill: 'rgba(0,0,0,0.04)' }}
            />
            <Bar
              dataKey="count"
              radius={[6, 6, 0, 0]}
              barSize={64}
              label={{
                position: 'top',
                fill: '#6b7280',
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              {sorted.map((_, index) => (
                <Cell key={`cell-${index}`} fill={`url(#bar-grad-${index})`} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
