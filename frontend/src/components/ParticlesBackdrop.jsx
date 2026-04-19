/**
 * Looping fullscreen particles video for tool pages (not shown on the landing route).
 */
export default function ParticlesBackdrop() {
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden>
      <video
        className="absolute inset-0 h-full w-full object-cover"
        src="/particles-bg.mp4"
        muted
        playsInline
        autoPlay
        loop
        preload="auto"
      />
      <div className="absolute inset-0 bg-[#070708]/78" />
      <div className="absolute inset-0 bg-gradient-to-b from-black/65 via-[#070708]/40 to-black/90" />
      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_100%_80%_at_50%_20%,transparent_0%,rgba(7,7,8,0.85)_75%)]"
        aria-hidden
      />
    </div>
  )
}
