import { PieChart, Pie, Cell } from 'recharts'

const COLORS: Record<string, string> = {
  Positive: '#10b981',
  Neutral: '#94a3b8',
  Negative: '#f43f5e',
}

const GLOW_COLORS: Record<string, string> = {
  Positive: 'rgba(16,185,129,0.25)',
  Neutral: 'rgba(148,163,184,0.2)',
  Negative: 'rgba(244,63,94,0.25)',
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
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Split</h3>
        <div className="flex items-center justify-center h-72 text-gray-400">No sentiment data available</div>
      </div>
    )
  }

  const getPercentage = (value: number) => ((value / total) * 100).toFixed(1)

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Split</h3>
      <div className="relative flex justify-center">
        <div className="relative" style={{ width: 200, height: 170 }}>
          <PieChart width={200} height={170}>
            <defs>
              {chartData.map((entry) => (
                <filter key={`glow-${entry.name}`} id={`glow-${entry.name}`}>
                  <feDropShadow dx={0} dy={0} stdDeviation={4} floodColor={GLOW_COLORS[entry.name]} />
                </filter>
              ))}
            </defs>
            <Pie
              data={chartData}
              cx={100}
              cy={85}
              innerRadius={58}
              outerRadius={73}
              paddingAngle={3}
              dataKey="value"
              strokeWidth={0}
            >
              {chartData.map((entry) => (
                <Cell
                  key={`cell-${entry.name}`}
                  fill={COLORS[entry.name]}
                  filter={`url(#glow-${entry.name})`}
                />
              ))}
            </Pie>
          </PieChart>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none" style={{ top: 0, left: 0, right: 0, bottom: 0, paddingTop: 10 }}>
            {chartData.map(({ name, value }) => (
              <div key={name} className="flex items-baseline gap-1 leading-tight">
                <span className="text-lg font-bold tracking-tight" style={{ color: COLORS[name] }}>
                  {getPercentage(value)}%
                </span>
                {/* <span className="text-[11px] font-medium text-gray-500">{name}</span>  */}
                {/* Commented out the above label to reduce clutter, can be re-enabled if needed */}
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="flex justify-center gap-6 mt-3">
        {chartData.map(({ name, value }) => (
          <div key={name} className="flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: COLORS[name] }}
            />
            <span className="text-xs font-medium text-gray-600">{name}</span>
            <span className="text-xs text-gray-400">{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
