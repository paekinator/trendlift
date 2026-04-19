import SaturationBadge from './SaturationBadge.jsx'
import EmptyState from './EmptyState.jsx'

function scoreColor(score) {
  if (score >= 65) return '#22c55e'
  if (score >= 35) return '#f59e0b'
  return '#ef4444'
}

function truncateTerms(terms = [], maxLen = 48) {
  const joined = terms.join(' · ')
  return joined.length > maxLen ? joined.slice(0, maxLen) + '…' : joined
}

export default function NicheTable({ niches = [] }) {
  if (!niches.length) {
    return (
      <EmptyState message="No niches match your filters. Try a lower minimum score or select All Categories." />
    )
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-md">
      <table className="w-full text-sm">
        <thead className="border-b border-white/[0.08] bg-black/30">
          <tr>
            <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Niche
            </th>
            <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Category
            </th>
            <th className="w-40 px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Breakout Score
            </th>
            <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Channels
            </th>
            <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Access
            </th>
            <th className="px-4 py-3 text-center text-[11px] font-semibold uppercase tracking-[0.16em] text-white/45">
              Global
            </th>
          </tr>
        </thead>
        <tbody>
          {niches.map((n, i) => {
            const color = scoreColor(n.breakout_score)
            return (
              <tr
                key={n.cluster_id ?? i}
                className="cursor-default border-t border-white/[0.06] transition-colors hover:bg-white/[0.04]"
              >
                <td className="max-w-[200px] px-4 py-3 text-white/90">
                  <span title={(n.top_terms ?? []).join(' · ')}>{truncateTerms(n.top_terms)}</span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-white/50">
                  {n.dominant_category ?? '—'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${n.breakout_score ?? 0}%`,
                          backgroundColor: color,
                        }}
                      />
                    </div>
                    <span className="w-6 text-right text-xs font-bold tabular-nums" style={{ color }}>
                      {n.breakout_score ?? 0}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right text-white/50">{n.unique_channels ?? '—'}</td>
                <td className="px-4 py-3">
                  <SaturationBadge saturation={n.saturation} />
                </td>
                <td className="px-4 py-3 text-center">
                  {n.country_arbitrage ? (
                    <span className="text-base text-emerald-400" title="Trends across English + non-English markets">
                      ✓
                    </span>
                  ) : (
                    <span className="text-white/25">—</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
