import { useState, useEffect, useCallback } from 'react'
import { getBreakoutNiches, getCategories } from '../api/client.js'
import NicheTable from '../components/NicheTable.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'

export default function Breakout() {
  const [categories, setCategories] = useState([])
  const [category, setCategory] = useState('')
  const [minScore, setMinScore] = useState(0)
  const [limit] = useState(15)
  const [niches, setNiches] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    getCategories()
      .then(d => setCategories(d.categories ?? []))
      .catch(() => {})
  }, [])

  const fetchNiches = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getBreakoutNiches(category, minScore, limit)
      setNiches(data.niches ?? [])
    } catch (err) {
      setError(err.message)
      setNiches([])
    } finally {
      setLoading(false)
    }
  }, [category, minScore, limit])

  useEffect(() => {
    const timer = setTimeout(fetchNiches, 300)
    return () => clearTimeout(timer)
  }, [fetchNiches])

  return (
    <main className="relative z-10 mx-auto w-full max-w-6xl flex-1 px-5 py-10 sm:px-8 sm:py-12">
      <div className="mb-8">
        <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.28em] text-white/40">
          Tools · Breakout Finder
        </p>
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Breakout Finder
        </h1>
        <p className="mb-4 text-sm text-white/55">
          Niches where smaller creators have historically had more room.
        </p>
        <p className="max-w-2xl rounded-2xl border border-white/[0.08] bg-white/[0.04] px-5 py-4 text-xs leading-relaxed text-white/55 backdrop-blur-md">
          <span className="font-semibold text-white/90">Breakout Score</span> measures how concentrated
          a niche is among established channels. A high score means the topic is spread across many
          creators — which means more room for you. A low score means a few dominant channels own the space.
        </p>
      </div>

      <div className="mb-8 flex flex-col gap-6 sm:flex-row sm:items-end">
        <div className="flex flex-col gap-1.5">
          <label className="text-[11px] font-medium uppercase tracking-[0.18em] text-white/45">
            Category
          </label>
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="min-h-[44px] min-w-[200px] appearance-none rounded-full border border-white/10 bg-white/[0.06] bg-[length:12px_12px] bg-[position:right_14px_center] bg-no-repeat px-4 py-2 pr-10 text-sm text-white backdrop-blur-md focus:border-white/25 focus:outline-none focus:ring-1 focus:ring-white/15"
            style={{
              backgroundImage:
                "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-opacity='0.45' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\")",
            }}
          >
            <option value="">All Categories</option>
            {categories.map(c => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="flex max-w-md flex-1 flex-col gap-1.5">
          <label className="text-[11px] font-medium uppercase tracking-[0.18em] text-white/45">
            Minimum Breakout Score:{' '}
            <span className="font-semibold tabular-nums text-white">{minScore}</span>
          </label>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={minScore}
            onChange={e => setMinScore(Number(e.target.value))}
            className="h-2 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-white"
          />
          <div className="flex justify-between text-[11px] text-white/40">
            <span>0</span>
            <span>50</span>
            <span>100</span>
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Finding breakout niches…" />
      ) : error ? (
        <div className="rounded-2xl border border-red-500/25 bg-red-950/35 p-4 text-sm text-red-200/95 backdrop-blur-md">
          {error}
        </div>
      ) : (
        <>
          <div className="mb-3 text-[11px] font-medium uppercase tracking-[0.2em] text-white/40">
            {niches.length} {niches.length === 1 ? 'niche' : 'niches'} found
          </div>
          <NicheTable niches={niches} />
        </>
      )}
    </main>
  )
}
