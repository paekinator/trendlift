function barColor(value) {
  if (value >= 0.65) return '#22c55e'
  if (value >= 0.35) return '#f59e0b'
  return '#ef4444'
}

const BARS = [
  { key: 'channel_spread',    label: 'Channel Spread',      hint: 'Unique channels in this niche' },
  { key: 'engagement_quality', label: 'Engagement Quality',  hint: 'How actively audiences interact' },
  { key: 'cross_country',     label: 'Cross-Country Reach', hint: 'Countries this topic trends in' },
  { key: 'trend_speed',       label: 'Trend Speed',         hint: 'How quickly content reaches trending' },
]

export default function ScoreBreakdownBars({ components }) {
  if (!components) return null

  return (
    <div className="flex flex-col gap-3">
      {BARS.map(({ key, label, hint }) => {
        const raw = components[key] ?? 0
        const pct = Math.round(raw * 100)
        const color = barColor(raw)

        return (
          <div key={key}>
            <div className="flex justify-between items-center mb-1">
              <div>
                <span className="text-sm font-medium text-white/90">{label}</span>
                <span className="ml-2 hidden text-xs text-white/45 sm:inline">{hint}</span>
              </div>
              <span className="text-sm font-semibold" style={{ color }}>{pct}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${pct}%`, backgroundColor: color }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
