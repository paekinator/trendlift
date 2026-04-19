import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
})

/**
 * Validate a video idea against the trending dataset.
 * GET /api/validate?query=...&country=...
 */
export async function validateIdea(query, country = 'all') {
  try {
    const { data } = await api.get('/api/validate', {
      params: { query, country },
    })
    return data
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Failed to validate idea'
    throw new Error(msg)
  }
}

/**
 * Fetch breakout niches, optionally filtered by category and min score.
 * GET /api/breakout?category=...&min_score=...&limit=...
 */
export async function getBreakoutNiches(category = '', minScore = 0, limit = 15) {
  try {
    const params = { min_score: minScore, limit }
    if (category) params.category = category
    const { data } = await api.get('/api/breakout', { params })
    return data
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Failed to fetch breakout niches'
    throw new Error(msg)
  }
}

/**
 * Fetch title pattern analysis for a given query topic.
 * GET /api/title-patterns?query=...
 */
export async function getTitlePatterns(query) {
  try {
    const { data } = await api.get('/api/title-patterns', { params: { query } })
    return data
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Failed to fetch title patterns'
    throw new Error(msg)
  }
}

/**
 * Fetch all available YouTube categories.
 * GET /api/categories
 */
export async function getCategories() {
  try {
    const { data } = await api.get('/api/categories')
    return data
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Failed to fetch categories'
    throw new Error(msg)
  }
}
