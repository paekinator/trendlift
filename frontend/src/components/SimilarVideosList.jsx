import EmptyState from './EmptyState.jsx'

const TIER_BADGE = {
  breakout: 'border border-emerald-500/35 bg-emerald-500/15 text-emerald-200',
  emerging: 'border border-sky-500/35 bg-sky-500/15 text-sky-200',
  established: 'border border-white/[0.1] bg-white/[0.06] text-white/65',
  dominant: 'border border-rose-500/35 bg-rose-500/15 text-rose-200',
}

function truncate(str, len = 60) {
  if (!str) return '—'
  return str.length > len ? str.slice(0, len) + '…' : str
}

export default function SimilarVideosList({ videos = [] }) {
  if (!videos.length) {
    return <EmptyState message="No similar videos found for this topic." />
  }

  const sorted = [...videos].sort((a, b) => (b.views ?? 0) - (a.views ?? 0))

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/[0.08]">
            <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Title
            </th>
            <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Channel
            </th>
            <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Country
            </th>
            <th className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Tier
            </th>
            <th className="px-3 py-2 text-right text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Trend&nbsp;Days
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((v, i) => {
            const tierCls = TIER_BADGE[v.channel_tier] ?? TIER_BADGE.established
            return (
              <tr
                key={i}
                className="border-b border-white/[0.06] transition-colors hover:bg-white/[0.04]"
              >
                <td className="max-w-[220px] px-3 py-2.5 text-white/90">
                  <span title={v.title}>{truncate(v.title)}</span>
                </td>
                <td className="whitespace-nowrap px-3 py-2.5 text-white/50">
                  {truncate(v.channel_title, 24)}
                </td>
                <td className="px-3 py-2.5 text-white/50">{v.country ?? '—'}</td>
                <td className="px-3 py-2.5">
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${tierCls}`}>
                    {v.channel_tier ?? '—'}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right text-white/50">
                  {v.trend_delay_days != null ? `${v.trend_delay_days}d` : '—'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
