import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import LandingFixedVideo from '../components/LandingFixedVideo.jsx'
import {
  IconSearchIdea,
  IconBreakoutTrend,
  IconTitleLines,
  IconStepLightbulb,
  IconStepGlobe,
  IconStepDecision,
} from '../components/scrollSegmentIcons.jsx'

function SegmentBadge({ Icon }) {
  return (
    <div className="mb-7 flex justify-center">
      <div
        className="flex h-[76px] w-[76px] items-center justify-center rounded-[22px] border border-white/[0.16] bg-[linear-gradient(180deg,rgba(255,255,255,0.11),rgba(255,255,255,0.035))] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.14)]"
        aria-hidden
      >
        <Icon />
      </div>
    </div>
  )
}

const MODE_LINKS = [
  { label: 'Idea Validator', to: '/validate' },
  { label: 'Breakout Finder', to: '/breakout' },
  { label: 'Title Patterns', to: '/title-patterns' },
]

const sectionShell =
  'border-t border-white/[0.06] px-5 py-20 sm:px-8 sm:py-28'

function LandingScrollProgressBar({ progress }) {
  const pct = Math.min(100, Math.max(0, Math.round(progress * 100)))
  return (
    <div className="fixed bottom-6 left-0 right-0 z-40 flex justify-center px-6 sm:bottom-7 sm:px-10">
      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Page scroll progress"
        className="pointer-events-auto h-2 w-full max-w-xl cursor-pointer overflow-hidden rounded-full border border-white/[0.14] bg-black/55 shadow-[inset_0_1px_3px_rgba(0,0,0,0.55)] backdrop-blur-md sm:max-w-2xl"
        onClick={(e) => {
          const el = e.currentTarget
          const rect = el.getBoundingClientRect()
          const ratio = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width))
          const doc = document.documentElement
          const max = Math.max(1, doc.scrollHeight - window.innerHeight)
          window.scrollTo({ top: ratio * max, behavior: 'smooth' })
        }}
      >
        <div
          className="pointer-events-none h-full rounded-full bg-gradient-to-r from-white via-white to-white/80 shadow-[0_0_16px_rgba(255,255,255,0.45)]"
          style={{ width: `${progress * 100}%` }}
        />
      </div>
    </div>
  )
}

export default function Landing() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  const [scrollProgress, setScrollProgress] = useState(0)
  const rafRef = useRef(null)

  const updateScrollProgress = useCallback(() => {
    const doc = document.documentElement
    const max = Math.max(1, doc.scrollHeight - window.innerHeight)
    const p = Math.min(1, Math.max(0, window.scrollY / max))
    setScrollProgress((prev) => (Math.abs(prev - p) > 0.001 ? p : prev))
  }, [])

  useEffect(() => {
    const onScroll = () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = requestAnimationFrame(updateScrollProgress)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    updateScrollProgress()
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [updateScrollProgress])

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) return
    navigate(`/validate?query=${encodeURIComponent(trimmed)}`)
  }

  return (
    <LandingFixedVideo>
      <LandingScrollProgressBar progress={scrollProgress} />

      {/* Hero — real document height, normal scroll */}
      <section className="mx-auto flex min-h-[88svh] max-w-3xl flex-col items-center justify-center px-5 pb-16 pt-28 text-center sm:px-8 sm:pt-32">
        <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.35em] text-white/60">
          TrendLift
        </p>
        <h1 className="max-w-2xl text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl sm:leading-[1.05] md:text-6xl">
          Before you record,
          <br />
          <span className="bg-gradient-to-r from-white via-white to-white/75 bg-clip-text text-transparent">
            know if it&apos;s worth the effort.
          </span>
        </h1>
        <p className="mx-auto mt-6 max-w-md text-base leading-relaxed text-white/75 sm:text-lg">
          One continuous page — scroll through every mode and step while the rocket tracks your
          position on the page.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mx-auto mt-12 flex w-full max-w-xl flex-col gap-3 sm:mt-14 sm:flex-row sm:items-stretch"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Your video idea — e.g. AI study tools"
            className="min-h-[48px] flex-1 rounded-full border border-white/10 bg-white/[0.08] px-5 py-3 text-[15px] text-white shadow-[0_0_0_1px_rgba(255,255,255,0.04)] backdrop-blur-md placeholder:text-white/35 focus:border-white/25 focus:outline-none focus:ring-1 focus:ring-white/20"
          />
          <button
            type="submit"
            className="min-h-[48px] shrink-0 rounded-full bg-white px-8 py-3 text-[15px] font-semibold text-[#0a0a0b] transition hover:bg-white/90 active:scale-[0.99]"
          >
            Validate
          </button>
        </form>
      </section>

      <section className={`${sectionShell} scroll-mt-20`}>
        <div className="mx-auto max-w-3xl text-center">
          <SegmentBadge Icon={IconSearchIdea} />
          <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.3em] text-white/45">
            Mode · Idea Validator
          </p>
          <h2 className="mx-auto max-w-xl text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            Don&apos;t guess if a topic is already crowded.
          </h2>
          <p className="mx-auto mt-5 max-w-md text-[15px] leading-relaxed text-white/55">
            Enter an idea and we surface how much room there is — so you skip the angles that are
            statistically already full.
          </p>
          <Link
            to="/validate"
            className="mt-10 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.06] px-6 py-2.5 text-[14px] font-medium text-white backdrop-blur-sm transition hover:border-white/35 hover:bg-white/[0.1]"
          >
            Open Idea Validator
            <span aria-hidden className="text-white/60">
              →
            </span>
          </Link>
        </div>
      </section>

      <section className={`${sectionShell} scroll-mt-20`}>
        <div className="mx-auto max-w-3xl text-center">
          <SegmentBadge Icon={IconBreakoutTrend} />
          <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.3em] text-white/45">
            Mode · Breakout Finder
          </p>
          <h2 className="mx-auto max-w-xl text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            Find pockets where smaller creators broke out.
          </h2>
          <p className="mx-auto mt-5 max-w-md text-[15px] leading-relaxed text-white/55">
            We highlight niches where smaller channels have historically had traction — so you aim
            where momentum is realistic, not only where giants live.
          </p>
          <Link
            to="/breakout"
            className="mt-10 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.06] px-6 py-2.5 text-[14px] font-medium text-white backdrop-blur-sm transition hover:border-white/35 hover:bg-white/[0.1]"
          >
            Open Breakout Finder
            <span aria-hidden className="text-white/60">
              →
            </span>
          </Link>
        </div>
      </section>

      <section className={`${sectionShell} scroll-mt-20`}>
        <div className="mx-auto max-w-3xl text-center">
          <SegmentBadge Icon={IconTitleLines} />
          <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.3em] text-white/45">
            Mode · Title Patterns
          </p>
          <h2 className="mx-auto max-w-xl text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            See how winning titles are actually phrased.
          </h2>
          <p className="mx-auto mt-5 max-w-md text-[15px] leading-relaxed text-white/55">
            Patterns from trending videos — how hooks are worded, where numbers appear, and what
            structure repeats — without copying anyone verbatim.
          </p>
          <Link
            to="/title-patterns"
            className="mt-10 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.06] px-6 py-2.5 text-[14px] font-medium text-white backdrop-blur-sm transition hover:border-white/35 hover:bg-white/[0.1]"
          >
            Open Title Patterns
            <span aria-hidden className="text-white/60">
              →
            </span>
          </Link>
        </div>
      </section>

      <section className={`${sectionShell} scroll-mt-20`}>
        <div className="mx-auto max-w-3xl text-center">
          <SegmentBadge Icon={IconStepLightbulb} />
          <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.3em] text-white/45">
            How it works · Step 1 of 3
          </p>
          <h2 className="mx-auto max-w-xl text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            Start with your idea — any angle, niche, or working title.
          </h2>
          <p className="mx-auto mt-5 max-w-md text-[15px] leading-relaxed text-white/55">
            You bring the spark. We don&apos;t need a polished pitch — a rough topic is enough to
            match against the dataset.
          </p>
        </div>
      </section>

      <section className={`${sectionShell} scroll-mt-20`}>
        <div className="mx-auto max-w-3xl text-center">
          <SegmentBadge Icon={IconStepGlobe} />
          <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.3em] text-white/45">
            How it works · Step 2 of 3
          </p>
          <h2 className="mx-auto max-w-xl text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            We compare it to what&apos;s actually trending.
          </h2>
          <p className="mx-auto mt-5 max-w-md text-[15px] leading-relaxed text-white/55">
            Your concept is checked against YouTube trend signals across eleven countries — not a
            generic “keyword score,” but movement in the real feed.
          </p>
        </div>
      </section>

      <section className={`${sectionShell} scroll-mt-20`}>
        <div className="mx-auto max-w-3xl text-center">
          <SegmentBadge Icon={IconStepDecision} />
          <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.3em] text-white/45">
            How it works · Step 3 of 3
          </p>
          <h2 className="mx-auto max-w-xl text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            Walk away with a clearer go / no-go.
          </h2>
          <p className="mx-auto mt-5 max-w-md text-[15px] leading-relaxed text-white/55">
            Use the readout to decide whether to invest a weekend in the video, pivot the angle, or
            shelve it — based on signals, not vibes.
          </p>
        </div>
      </section>

      <section className={`${sectionShell} scroll-mt-20 pb-32`}>
        <div className="mx-auto max-w-3xl text-center">
          <p className="mx-auto mb-6 max-w-md text-lg font-normal leading-relaxed text-white/80 sm:text-xl">
            TrendLift doesn&apos;t promise virality.
            <br />
            <span className="text-white/55">It reduces wasted effort.</span>
          </p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-[13px] font-medium text-white/40">
            {MODE_LINKS.map(({ label, to }) => (
              <Link key={to} to={to} className="transition hover:text-white/70">
                {label}
              </Link>
            ))}
          </div>
        </div>
      </section>
    </LandingFixedVideo>
  )
}
