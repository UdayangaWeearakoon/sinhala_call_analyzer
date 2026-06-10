import { PhoneCall, Clock, Calendar } from 'lucide-react'

interface KpiCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  color: string
}

function KpiCard({ title, value, subtitle, icon, color }: KpiCardProps) {
  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-3xl font-bold mt-2 text-gray-900">{value}</p>
          {subtitle && <p className="text-sm mt-1 text-gray-500">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}

interface KpiCardsProps {
  totalCallsToday: number
  totalCallsYesterday: number
  totalCallsThisMonth: number
  positivePercentage: number
}

export function KpiCards({ totalCallsToday, totalCallsYesterday, totalCallsThisMonth, positivePercentage }: KpiCardsProps) {
  const vsYesterday = totalCallsYesterday > 0
    ? `${((totalCallsToday - totalCallsYesterday) / totalCallsYesterday * 100).toFixed(0)}% vs yesterday`
    : 'vs yesterday'

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <KpiCard
        title="Calls Today"
        value={totalCallsToday}
        subtitle={vsYesterday}
        icon={<PhoneCall className="w-6 h-6 text-blue-600" />}
        color="bg-blue-50"
      />
      <KpiCard
        title="Calls This Month"
        value={totalCallsThisMonth}
        subtitle="total volume"
        icon={<Calendar className="w-6 h-6 text-purple-600" />}
        color="bg-purple-50"
      />
      <KpiCard
        title="Positive Sentiment"
        value={`${positivePercentage}%`}
        subtitle="customer satisfaction"
        icon={<Clock className="w-6 h-6 text-amber-600" />}
        color="bg-amber-50"
      />
    </div>
  )
}
