import { useRef, useEffect, useCallback } from 'react'

/**
 * Full-viewport fixed rocket video behind landing content.
 * `currentTime` tracks overall page scroll (no fake segment heights or content transforms).
 */
export default function LandingFixedVideo({ videoSrc = '/rocket.mp4', children }) {
  const videoRef = useRef(null)
  const reduceMotionRef = useRef(false)
  const rafRef = useRef(null)

  const tick = useCallback(() => {
    const video = videoRef.current
    if (reduceMotionRef.current || !video || Number.isNaN(video.duration) || video.duration === 0)
      return

    const doc = document.documentElement
    const scrollable = Math.max(1, doc.scrollHeight - window.innerHeight)
    const progress = Math.min(1, Math.max(0, window.scrollY / scrollable))
    const targetTime = progress * video.duration
    if (Math.abs(video.currentTime - targetTime) > 0.03) {
      video.currentTime = targetTime
    }
  }, [])

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    reduceMotionRef.current = mq.matches
    const onMq = () => {
      reduceMotionRef.current = mq.matches
      const video = videoRef.current
      if (mq.matches && video?.duration) {
        video.pause()
        video.currentTime = 0
      }
      tick()
    }
    mq.addEventListener('change', onMq)

    const onScroll = () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = requestAnimationFrame(tick)
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    tick()

    return () => {
      mq.removeEventListener('change', onMq)
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [tick])

  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    const onReady = () => tick()
    video.addEventListener('loadedmetadata', onReady)
    video.addEventListener('canplay', onReady)
    return () => {
      video.removeEventListener('loadedmetadata', onReady)
      video.removeEventListener('canplay', onReady)
    }
  }, [tick])

  return (
    <main className="relative bg-[#070708] text-white">
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden>
        <video
          ref={videoRef}
          className="absolute inset-0 h-full w-full object-cover"
          style={{ transform: 'translateZ(0)' }}
          src={videoSrc}
          muted
          playsInline
          preload="auto"
          tabIndex={-1}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/75 via-black/35 to-black/90" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_95%_75%_at_50%_35%,transparent_15%,rgba(0,0,0,0.7)_100%)]" />
      </div>

      <div className="relative z-10">{children}</div>
    </main>
  )
}
