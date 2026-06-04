import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { buildsApi } from '@/services/builds-api'
import type { BuildSummary, BuildsListResponse } from '@/types/builds'
import PopularBuilds from './PopularBuilds'
import './BuildsBrowser.css'

type Tab = 'builds' | 'meta'

const PAGE_SIZE = 60

function fmtDps(dps: number): string {
  if (dps >= 1_000_000) return `${(dps / 1_000_000).toFixed(dps >= 10_000_000 ? 0 : 1)}M`
  if (dps >= 1_000) return `${(dps / 1_000).toFixed(dps >= 100_000 ? 0 : 1)}k`
  return String(dps)
}

function fmtNum(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)
}

function BuildCard({ b }: { b: BuildSummary }) {
  return (
    <Link to={`/builds/${encodeURIComponent(b.id)}`} className="build-card">
      <div className="build-card-head">
        <span className="build-char">{b.character}</span>
        <span className="build-level">Lv {b.level}</span>
      </div>
      <div className="build-class">
        <span className="build-ascendancy">{b.ascendancy || b.base_class || 'Unknown'}</span>
        {b.base_class && b.ascendancy && <span className="build-baseclass">{b.base_class}</span>}
      </div>
      {b.main_skill && (
        <div className="build-skill">
          <span className="build-skill-name">{b.main_skill.name}</span>
          {b.main_skill.dps > 0 && <span className="build-skill-dps">{fmtDps(b.main_skill.dps)} dps</span>}
        </div>
      )}
      <div className="build-defense">
        {b.life > 0 && <span className="def def-life">{fmtNum(b.life)} life</span>}
        {b.energy_shield > 0 && <span className="def def-es">{fmtNum(b.energy_shield)} ES</span>}
        {b.ehp > 0 && <span className="def def-ehp">{fmtNum(b.ehp)} EHP</span>}
      </div>
      {b.notable_uniques.length > 0 && (
        <div className="build-uniques">
          {b.notable_uniques.map((u) => (
            <span key={u} className="unique-chip">{u}</span>
          ))}
        </div>
      )}
    </Link>
  )
}

function BuildsTab() {
  const [data, setData] = useState<BuildsListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [ascendancy, setAscendancy] = useState('')
  const [skill, setSkill] = useState('')
  const [q, setQ] = useState('')
  const [page, setPage] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    buildsApi
      .listBuilds({ ascendancy, skill, q, limit: PAGE_SIZE, offset: page * PAGE_SIZE })
      .then((d) => !cancelled && setData(d))
      .catch((err) => {
        if (cancelled) return
        const status = err?.response?.status
        setError(
          status === 503
            ? 'The builds sample has not been published yet.'
            : 'Failed to load builds.'
        )
        console.error(err)
      })
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [ascendancy, skill, q, page])

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0
  const ascendancies = data?.ascendancies ?? []
  const skills = data?.skills ?? []

  const resetTo = (fn: () => void) => {
    setPage(0)
    fn()
  }

  return (
    <>
      {data?.meta && (
        <p className="bb-subtitle">
          Browsing <strong>{data.meta.sample_size}</strong> real builds from{' '}
          <strong>{data.meta.league}</strong>
          {data.meta.scraped_at && (
            <> · snapshot {new Date(data.meta.scraped_at).toLocaleDateString()}</>
          )}
        </p>
      )}

      <div className="bb-filters">
        <input
          className="bb-search"
          type="text"
          placeholder="Search character, skill, unique…"
          value={q}
          onChange={(e) => resetTo(() => setQ(e.target.value))}
        />
        <select
          className="bb-select"
          value={ascendancy}
          onChange={(e) => resetTo(() => setAscendancy(e.target.value))}
        >
          <option value="">All ascendancies</option>
          {ascendancies.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <select
          className="bb-select"
          value={skill}
          onChange={(e) => resetTo(() => setSkill(e.target.value))}
        >
          <option value="">All skills</option>
          {skills.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        {(ascendancy || skill || q) && (
          <button
            className="bb-clear"
            onClick={() => resetTo(() => { setAscendancy(''); setSkill(''); setQ('') })}
          >
            Clear
          </button>
        )}
      </div>

      {loading && <div className="bb-state">Loading builds…</div>}
      {error && <div className="bb-state bb-error">{error}</div>}

      {!loading && !error && data && (
        <>
          {data.builds.length === 0 ? (
            <div className="bb-state">No builds match these filters.</div>
          ) : (
            <div className="builds-grid">
              {data.builds.map((b) => (
                <BuildCard key={b.id} b={b} />
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="bb-pagination">
              <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                ← Prev
              </button>
              <span>Page {page + 1} of {totalPages}</span>
              <button disabled={page + 1 >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </>
  )
}

function BuildsBrowser() {
  const [tab, setTab] = useState<Tab>('builds')

  const tabs = useMemo(
    () => [
      { id: 'builds' as Tab, label: 'Builds' },
      { id: 'meta' as Tab, label: 'Meta · usage' },
    ],
    []
  )

  return (
    <div className="builds-browser">
      <div className="bb-header">
        <h1>Popular Builds</h1>
        <div className="bb-tabs">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`bb-tab ${tab === t.id ? 'bb-tab-active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'builds' ? <BuildsTab /> : <PopularBuilds embedded />}
    </div>
  )
}

export default BuildsBrowser
