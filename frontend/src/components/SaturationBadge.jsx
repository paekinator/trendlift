const STYLES = {
  'Under-served':
    'border border-emerald-500/30 bg-emerald-500/15 text-emerald-200',
  Moderate: 'border border-amber-500/25 bg-amber-500/12 text-amber-200',
  Crowded: 'border border-rose-500/30 bg-rose-500/15 text-rose-200',
}

export default function SaturationBadge({ saturation }) {
  if (!saturation) return null
  const cls =
    STYLES[saturation] ?? 'border border-white/[0.1] bg-white/[0.06] text-white/60'
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}
    >
      {saturation}
    </span>
  )
}
