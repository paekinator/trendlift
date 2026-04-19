function scoreColor(score) {
  if (score >= 65) return '#22c55e'
  if (score >= 40) return '#f59e0b'
  return '#ef4444'
}

/**
 * Circular SVG ring displaying a 0–100 score.
 * The text is overlaid using absolute positioning inside a relative wrapper.
 */
export default function ScoreRing({ score, size = 120 }) {
  const strokeWidth = 10
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const safeScore = Math.max(0, Math.min(100, score ?? 0))
  const offset = circumference * (1 - safeScore / 100)
  const color = scoreColor(safeScore)

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      {/* Ring drawn rotated so fill starts at 12-o'clock */}
      <svg
        width={size}
        height={size}
        style={{ transform: 'rotate(-90deg)', position: 'absolute', top: 0, left: 0 }}
      >
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.12)"
          strokeWidth={strokeWidth}
        />
        {/* Fill */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      {/* Center text */}
      <div className="flex flex-col items-center justify-center z-10">
        <span className="font-bold leading-none text-white" style={{ fontSize: size * 0.22 }}>
          {safeScore}
        </span>
        <span className="mt-0.5 leading-none text-white/45" style={{ fontSize: size * 0.1 }}>
          / 100
        </span>
      </div>
    </div>
  )
}
