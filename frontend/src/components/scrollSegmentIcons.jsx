/** Minimal stroke icons for scroll story segments (24×24 viewBox) */

const stroke = {
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  fill: 'none',
}

export function IconSearchIdea(props) {
  return (
    <svg viewBox="0 0 24 24" width="28" height="28" aria-hidden {...props}>
      <circle {...stroke} cx="10.5" cy="10.5" r="6.5" />
      <path {...stroke} d="M15.5 15.5L21 21" />
      <path {...stroke} d="M8.2 9.5h4.6M10.5 7.2v4.6" />
    </svg>
  )
}

export function IconBreakoutTrend(props) {
  return (
    <svg viewBox="0 0 24 24" width="28" height="28" aria-hidden {...props}>
      <path {...stroke} d="M4 18V6M4 18h16" />
      <path {...stroke} d="M7 14.5l3-4 3.5 2.5L19.5 7" />
      <path {...stroke} d="M17.5 7H20v2.5" />
    </svg>
  )
}

export function IconTitleLines(props) {
  return (
    <svg viewBox="0 0 24 24" width="28" height="28" aria-hidden {...props}>
      <path {...stroke} d="M5 7.5h14M5 12.5h9.5M5 17.5h14" />
      <path {...stroke} d="M16.5 9.5l2.2 2.2-2.2 2.2" />
    </svg>
  )
}

export function IconStepLightbulb(props) {
  return (
    <svg viewBox="0 0 24 24" width="28" height="28" aria-hidden {...props}>
      <path
        {...stroke}
        d="M9.5 16.5c-1.2-1-2-2.5-2-4.2a5.5 5.5 0 1110.1 0c0 1.7-.8 3.2-2 4.2"
      />
      <path {...stroke} d="M10 16.5h4M9.5 19h5" />
      <path {...stroke} d="M12 6.5V4" opacity="0.45" />
    </svg>
  )
}

export function IconStepGlobe(props) {
  return (
    <svg viewBox="0 0 24 24" width="28" height="28" aria-hidden {...props}>
      <circle {...stroke} cx="12" cy="12" r="7.25" />
      <ellipse {...stroke} cx="12" cy="12" rx="3.5" ry="7.25" opacity="0.55" />
      <path {...stroke} d="M5 12h14M12 5s3 4 3 7-3 7-3 7" />
    </svg>
  )
}

export function IconStepDecision(props) {
  return (
    <svg viewBox="0 0 24 24" width="28" height="28" aria-hidden {...props}>
      <circle {...stroke} cx="12" cy="12" r="7.25" />
      <path {...stroke} d="M9 12l2 2 4.5-5" />
      <path {...stroke} d="M12 19v-1.5" opacity="0.45" />
    </svg>
  )
}
