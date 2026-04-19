import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { validateIdea } from '../api/client.js'
import ScoreRing from '../components/ScoreRing.jsx'
import SaturationBadge from '../components/SaturationBadge.jsx'
import ScoreBreakdownBars from '../components/ScoreBreakdownBars.jsx'
import SimilarVideosList from '../components/SimilarVideosList.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'

function ClockIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
    </svg>
  )
}

function pct(v) {
  return `${Math.round((v ?? 0) * 100)}%`
}

export default function Validator() {
  const [searchParams] = useSearchParams()
  const navigate       = useNavigate()
  const urlQuery       = searchParams.get('query') ?? ''

  const [input,   setInput]   = useState(urlQuery)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [noMatch, setNoMatch] = useState(null)   // soft "no results" message
  const [error,   setError]   = useState(null)

  const submit = useCallback(async (q) => {
    const trimmed = q.trim()
    if (!trimmed) return
    setLoading(true)
    setResults(null)
    setNoMatch(null)
    setError(null)
    try {
      const data = await validateIdea(trimmed)
      if (data.cluster_id === -1 || data.error) {
        setNoMatch(data.error ?? 'No closely matching content found. Try a broader topic.')
      } else {
        setResults(data)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Auto-submit when the URL query param is set
  useEffect(() => {
    if (urlQuery) {
      setInput(urlQuery)
      submit(urlQuery)
    }
  }, [urlQuery, submit])

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed) return
    navigate(`/validate?query=${encodeURIComponent(trimmed)}`, { replace: true })
    submit(trimmed)
  }

  const patterns = results?.title_patterns ?? {}
  const topWords = Object.entries(patterns.top_first_words ?? {}).slice(0, 8)

  return (
    <main className="relative z-10 mx-auto w-full max-w-6xl flex-1 px-5 py-10 sm:px-8 sm:py-12">
      {/* ── Search bar ── */}
      <div className="mb-10">
        <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.28em] text-white/40">
          Tools · Idea Validator
        </p>
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Idea Validator
        </h1>
        <p className="mb-8 max-w-2xl text-sm leading-relaxed text-white/55">
          Enter your video topic to see how competitive the space is and how similar content performs.
        </p>
        <form onSubmit={handleSubmit} className="flex max-w-2xl flex-col gap-3 sm:flex-row sm:items-stretch">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="e.g. beginner workout routine, AI productivity tools"
            className="min-h-[46px] flex-1 rounded-full border border-white/10 bg-white/[0.06] px-5 py-2.5 text-[15px] text-white shadow-[0_0_0_1px_rgba(255,255,255,0.04)] backdrop-blur-md placeholder:text-white/35 focus:border-white/25 focus:outline-none focus:ring-1 focus:ring-white/20"
          />
          <button
            type="submit"
            disabled={loading}
            className="min-h-[46px] shrink-0 rounded-full bg-white px-7 py-2.5 text-[14px] font-semibold text-[#0a0a0b] transition hover:bg-white/90 disabled:opacity-45"
          >
            Analyze
          </button>
        </form>
      </div>

      {/* ── States ── */}
      {loading && <LoadingSpinner message="Analyzing trending patterns…" />}

      {error && (
        <div className="rounded-2xl border border-red-500/25 bg-red-950/35 p-4 text-sm text-red-200/95 backdrop-blur-md">
          {error}
        </div>
      )}

      {noMatch && (
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-8 text-center backdrop-blur-md">
          <div className="mb-3 text-2xl opacity-40 grayscale">🔍</div>
          <p className="text-sm text-white/55">{noMatch}</p>
        </div>
      )}

      {/* ── Results ── */}
      {results && (
        <div className="space-y-6">
          {/* Two-column layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left column */}
            <div className="space-y-4">
              {/* Score + saturation */}
              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-6 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
                <div className="flex items-center gap-6">
                  <ScoreRing score={results.opportunity_score} size={110} />
                  <div className="flex-1 min-w-0">
                    <div className="mb-1 text-[11px] font-medium uppercase tracking-[0.2em] text-white/45">
                      Opportunity Score
                    </div>
                    <div className="flex items-center gap-2 mb-3">
                      <SaturationBadge saturation={results.saturation} />
                    </div>
                    <p className="text-xs leading-relaxed text-white/50">
                      Based on{' '}
                      <span className="font-medium text-white/90">
                        {results.similar_videos?.length ?? 0} similar trending videos
                      </span>{' '}
                      across 11 countries.
                    </p>
                  </div>
                </div>
              </div>

              {/* Score breakdown */}
              <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-5 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
                <h3 className="mb-4 text-sm font-semibold tracking-tight text-white">Score Breakdown</h3>
                <ScoreBreakdownBars components={results.score_components} />
              </div>

              {/* Timing card */}
              {results.timing && (
                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-5 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
                  <h3 className="mb-3 text-sm font-semibold tracking-tight text-white">Trend Timing</h3>
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 text-white/45">
                      <ClockIcon />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white/90">
                        {results.timing.interpretation}
                      </p>
                      <p className="mt-0.5 text-xs text-white/45">
                        Avg trend delay: {results.timing.avg_trend_delay_days} days
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right column — similar videos */}
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-5 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
              <h3 className="mb-4 text-sm font-semibold tracking-tight text-white">
                Similar Trending Videos
              </h3>
              <SimilarVideosList videos={results.similar_videos ?? []} />
            </div>
          </div>

          {/* ── Title patterns (full width) ── */}
          {patterns && (
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-6 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
              <h3 className="mb-5 text-sm font-semibold tracking-tight text-white">
                Title patterns in this space
              </h3>

              {/* 3 stat cards */}
              <div className="mb-5 grid grid-cols-3 gap-3">
                {[
                  { label: 'Avg word count',    value: patterns.median_word_count ?? '—' },
                  { label: 'Titles use "?"',    value: pct(patterns.question_rate) },
                  { label: 'Titles use ":"',    value: pct(patterns.colon_rate) },
                ].map(card => (
                  <div
                    key={card.label}
                    className="rounded-xl border border-white/[0.06] bg-black/30 p-3 text-center"
                  >
                    <div className="text-xl font-bold text-white">{card.value}</div>
                    <div className="mt-0.5 text-xs text-white/45">{card.label}</div>
                  </div>
                ))}
              </div>

              {/* Top first words */}
              {topWords.length > 0 && (
                <div className="mb-5">
                  <div className="mb-2 text-[11px] font-medium uppercase tracking-[0.18em] text-white/45">
                    Common opening words
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {topWords.map(([word, count]) => (
                      <span
                        key={word}
                        className="inline-flex items-center gap-1 rounded-full border border-white/[0.08] bg-white/[0.06] px-3 py-1 text-xs text-white/90"
                      >
                        <span className="font-medium">{word}</span>
                        <span className="text-white/45">×{count}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Example titles */}
              {(patterns.example_titles ?? []).length > 0 && (
                <div>
                  <div className="mb-2 text-[11px] font-medium uppercase tracking-[0.18em] text-white/45">
                    Titles that trended in this space
                  </div>
                  <ul className="space-y-1.5">
                    {patterns.example_titles.map((t, i) => (
                      <li key={i} className="text-sm italic text-white/50">
                        "{t}"
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Cluster top terms */}
              {(results.cluster_top_terms ?? []).length > 0 && (
                <div className="mt-4 border-t border-white/[0.08] pt-4">
                  <div className="mb-2 text-[11px] font-medium uppercase tracking-[0.18em] text-white/45">
                    Topic keywords in this cluster
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {results.cluster_top_terms.map(t => (
                      <span
                        key={t}
                        className="rounded-md border border-white/[0.08] bg-black/35 px-2 py-0.5 text-xs text-white/55"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </main>
  )
}
