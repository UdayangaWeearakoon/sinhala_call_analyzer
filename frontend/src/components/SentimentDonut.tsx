import { PieChart, Pie, Cell, Legend, Tooltip } from 'recharts'

const COLORS: Record<string, string> = {
  Positive: '#22c55e',
  Neutral: '#94a3b8',
  Negative: '#ef4444',
  'Very Negative': '#991b1b',
}

interface SentimentDonutProps {
  data: Record<string, number>
}

export function SentimentDonut({ data }: SentimentDonutProps) {
  const chartData = Object.entries(data ?? {})
    .filter(([name]) => name !== 'string' && COLORS[name])
    .map(([name, value]) => ({ name, value }))
    .filter((d) => d.value > 0)

  const total = chartData.reduce((sum, d) => sum + d.value, 0)

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Split</h3>
        <div className="flex items-center justify-center h-72 text-gray-400">No sentiment data available</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Split</h3>
      <div className="flex justify-center">
        <PieChart width={320} height={280}>
          <Pie
            data={chartData}
            cx={160}
            cy={140}
            innerRadius={60}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[entry.name] || '#6366f1'} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => [`${value} (${((value / total) * 100).toFixed(1)}%)`, 'Count']}
          />
          <Legend layout="horizontal" verticalAlign="bottom" align="center" />
        </PieChart>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        {chartData.map(({ name, value }) => (
          <div key={name}>
            <p className="text-sm font-medium text-gray-500">{name}</p>
            <p className="text-lg font-bold" style={{ color: COLORS[name] || '#6366f1' }}>
              {((value / total) * 100).toFixed(1)}%
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
