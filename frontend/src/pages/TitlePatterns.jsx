import { useState } from 'react'
import { getTitlePatterns } from '../api/client.js'
import ViralPatternCard from '../components/ViralPatternCard.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'

function pct(v) {
  return `${Math.round((v ?? 0) * 100)}%`
}

export default function TitlePatterns() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [noMatch, setNoMatch] = useState(null)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) return
    setLoading(true)
    setResults(null)
    setNoMatch(null)
    setError(null)
    try {
      const data = await getTitlePatterns(trimmed)
      if (data.cluster_id === -1 || data.error) {
        setNoMatch(data.error ?? 'No matching content found. Try a broader or different topic keyword.')
      } else {
        setResults(data)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const p = results?.patterns ?? {}
  const topWords = Object.entries(p.top_first_words ?? {})
  const terms = results?.cluster_top_terms ?? []

  return (
    <main className="relative z-10 mx-auto w-full max-w-4xl flex-1 px-5 py-10 sm:px-8 sm:py-12">
      <div className="mb-8">
        <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.28em] text-white/40">
          Tools · Title Patterns
        </p>
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Title Pattern Explorer
        </h1>
        <p className="mb-2 text-sm text-white/55">
          Patterns in titles that reached trending in this content space.
        </p>
        <p className="text-xs italic text-white/40">
          This shows what trending titles look like in this category — not a formula for success.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="mb-10 flex max-w-2xl flex-col gap-3 sm:flex-row sm:items-stretch">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="e.g. cooking tutorial, gaming highlights, tech review"
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

      {loading && <LoadingSpinner message="Analyzing title patterns…" />}

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

      {results && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <ViralPatternCard
              icon="📝"
              label="Median Word Count"
              value={p.median_word_count ?? '—'}
              subtitle="words per title"
            />
            <ViralPatternCard
              icon="❓"
              label="Uses a Question"
              value={pct(p.question_rate)}
              subtitle="of trending titles"
            />
            <ViralPatternCard
              icon="："
              label="Uses a Colon"
              value={pct(p.colon_rate)}
              subtitle="of trending titles"
            />
            <ViralPatternCard
              icon="🔢"
              label="Contains a Number"
              value={pct(p.number_rate)}
              subtitle="of trending titles"
            />
          </div>

          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-5 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
            <h3 className="mb-4 text-sm font-semibold tracking-tight text-white">Additional signals</h3>
            <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
              {[
                { label: 'Median char count', value: p.median_char_count ?? '—' },
                { label: 'Avg caps ratio', value: pct(p.median_caps_ratio) },
                { label: 'Uses exclamation', value: pct(p.exclamation_rate) },
              ].map(s => (
                <div key={s.label}>
                  <div className="mb-0.5 text-xs text-white/45">{s.label}</div>
                  <div className="font-semibold text-white/95">{s.value}</div>
                </div>
              ))}
            </div>
          </div>

          {topWords.length > 0 && (
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-5 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
              <h3 className="mb-3 text-sm font-semibold tracking-tight text-white">Common opening words</h3>
              <div className="flex flex-wrap gap-2">
                {topWords.map(([word, count]) => (
                  <span
                    key={word}
                    className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.06] px-3 py-1 text-sm text-white/90"
                  >
                    <span className="font-medium">{word}</span>
                    <span className="text-xs text-white/45">×{count}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {(p.example_titles ?? []).length > 0 && (
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-5 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
              <h3 className="mb-3 text-sm font-semibold tracking-tight text-white">
                Titles that trended in this space
              </h3>
              <ul className="space-y-2">
                {p.example_titles.map((title, i) => (
                  <li
                    key={i}
                    className="border-l-2 border-white/[0.12] pl-3 text-sm italic text-white/50"
                  >
                    &ldquo;{title}&rdquo;
                  </li>
                ))}
              </ul>
            </div>
          )}

          {terms.length > 0 && (
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.05] p-5 backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
              <h3 className="mb-3 text-sm font-semibold tracking-tight text-white">Topic context</h3>
              <div className="flex flex-wrap gap-2">
                {terms.map(t => (
                  <span
                    key={t}
                    className="rounded-md border border-white/[0.08] bg-black/35 px-2.5 py-1 text-xs text-white/55"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  )
}
