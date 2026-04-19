/**
 * Stat card for title-pattern / cluster summaries — matches glass panels on tool pages.
 */
export default function ViralPatternCard({ icon, label, value, subtitle }) {
  return (
    <div className="flex flex-col gap-1 rounded-2xl border border-white/[0.08] bg-white/[0.05] p-5 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
      {icon ? <div className="mb-1 text-xl opacity-90">{icon}</div> : null}
      <div className="text-2xl font-bold leading-tight tracking-tight text-white/95">{value}</div>
      <div className="text-sm font-medium text-white/50">{label}</div>
      {subtitle ? <div className="mt-0.5 text-xs text-white/40">{subtitle}</div> : null}
    </div>
  )
}
