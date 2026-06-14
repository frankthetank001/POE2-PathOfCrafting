import { useEffect, useMemo, useState } from 'react'
import { buildsApi } from '@/services/builds-api'
import type { CraftableItem } from '@/types/crafting'
import type { FinishSuggestion, SuggestedMod, SimilarItem } from '@/types/builds'
import './FinishAdvisorPanel.css'

interface Props {
  item: CraftableItem
}

function pct(v: number | null | undefined): string {
  return v != null ? `${Math.round(v * 100)}%` : ''
}

// Suggested mods come back value-templated ('+# to maximum Energy Shield'); fill the '#' with a
// representative good-roll value when we have one, otherwise show the template.
function fill(m: SuggestedMod): string {
  if (m.value == null) return m.stat_text
  return m.stat_text.replace('#', String(Math.round(m.value)))
}

function originClass(origin: string): string {
  if (origin === 'crafted') return 'fa-origin-crafted'
  if (origin === 'desecrated') return 'fa-origin-desecrated'
  return 'fa-origin-explicit'
}

function ModRow({ m }: { m: SuggestedMod }) {
  return (
    <li className={`fa-mod ${originClass(m.origin)}`}>
      <span className="fa-mod-text">{fill(m)}</span>
      <span className="fa-mod-meta">
        {m.neighbour_count > 0 && (
          <span className="fa-chip fa-chip-neigh" title="similar meta items running this mod">
            {m.neighbour_count}× similar
          </span>
        )}
        {m.slot_usage_pct != null && m.slot_usage_pct > 0 && (
          <span className="fa-chip" title="share of this slot's rares running it">
            {pct(m.slot_usage_pct)} slot
          </span>
        )}
        {m.tier != null && <span className="fa-chip fa-chip-tier">T{m.tier}</span>}
      </span>
    </li>
  )
}

function ModList({ title, hint, mods }: { title: string; hint?: string; mods: SuggestedMod[] }) {
  if (mods.length === 0) return null
  return (
    <div className="fa-modlist">
      <div className="fa-modlist-title" title={hint}>{title}</div>
      <ul className="fa-mods">
        {mods.map((m, i) => (
          <ModRow key={`${m.mod_group || m.stat_text}-${i}`} m={m} />
        ))}
      </ul>
    </div>
  )
}

function SimilarRow({ s }: { s: SimilarItem }) {
  return (
    <li className="fa-similar">
      <div className="fa-similar-head">
        <span className="fa-similar-base">{s.base_type}</span>
        {s.approx_energy_shield != null && (
          <span className="fa-similar-es" title="approximate Energy Shield (for ordering)">
            ~{s.approx_energy_shield} ES
          </span>
        )}
        {s.corrupted && <span className="fa-similar-corrupt">corrupted</span>}
      </div>
      {s.missing_mods.length > 0 && (
        <div className="fa-similar-missing">
          <span className="fa-similar-missing-label">runs that you lack:</span>{' '}
          {s.missing_mods.slice(0, 5).map((t, i) => (
            <span key={i} className="fa-missing-chip">{t}</span>
          ))}
        </div>
      )}
    </li>
  )
}

export function FinishAdvisorPanel({ item }: Props) {
  const [data, setData] = useState<FinishSuggestion | null>(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [showSimilar, setShowSimilar] = useState(false)

  // A stable signature so we only refetch when the item's identity/mods actually change.
  const sig = useMemo(
    () =>
      JSON.stringify({
        b: item.base_name,
        c: item.base_category,
        r: item.rarity,
        p: item.prefix_mods.map((m) => [m.stat_text, m.is_crafted, m.is_desecrated]),
        s: item.suffix_mods.map((m) => [m.stat_text, m.is_crafted, m.is_desecrated]),
      }),
    [item]
  )

  useEffect(() => {
    if (item.rarity !== 'Rare') {
      setData(null)
      return
    }
    let cancelled = false
    const t = setTimeout(async () => {
      setLoading(true)
      setErr(null)
      try {
        const res = await buildsApi.finishSuggestions(item)
        if (!cancelled) setData(res)
      } catch (e) {
        const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        if (!cancelled) setErr(detail || 'Suggestions unavailable')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, 350)
    return () => {
      cancelled = true
      clearTimeout(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sig])

  // The advisor is about finishing a Rare - it doesn't apply to white/magic/unique items.
  if (item.rarity !== 'Rare') return null
  if (err) {
    return (
      <div className="finish-advisor finish-advisor-muted">
        <div className="fa-header"><span className="fa-title">Finish this item</span></div>
        <div className="fa-empty">{err}</div>
      </div>
    )
  }
  if (!data) {
    return (
      <div className="finish-advisor finish-advisor-muted">
        <div className="fa-header"><span className="fa-title">Finish this item</span></div>
        <div className="fa-empty">{loading ? 'Analysing the meta…' : ''}</div>
      </div>
    )
  }

  const noSuggestions =
    data.suggested_prefixes.length === 0 &&
    data.suggested_suffixes.length === 0 &&
    data.suggested_crafted.length === 0 &&
    data.suggested_desecrated.length === 0

  return (
    <div className="finish-advisor">
      <div className="fa-header">
        <span className="fa-title">Finish this item</span>
        {loading && <span className="fa-spinner" aria-hidden />}
        {data.verdict === 'complete' ? (
          <span className="fa-badge fa-badge-complete">Complete</span>
        ) : (
          <span className="fa-badge">
            {data.open_prefixes}P · {data.open_suffixes}S open
          </span>
        )}
      </div>

      {data.message && <div className="fa-message">{data.message}</div>}

      {data.verdict !== 'complete' && !noSuggestions && (
        <>
          <div className="fa-columns">
            <ModList
              title={`Add a prefix${data.open_prefixes ? ` (${data.open_prefixes} open)` : ''}`}
              hint="Top prefixes the meta's similar items run that yours is missing"
              mods={data.suggested_prefixes}
            />
            <ModList
              title={`Add a suffix${data.open_suffixes ? ` (${data.open_suffixes} open)` : ''}`}
              hint="Top suffixes the meta's similar items run that yours is missing"
              mods={data.suggested_suffixes}
            />
          </div>

          {data.crafted_slot_open && data.suggested_crafted.length > 0 && (
            <ModList
              title="Crafted mod (essence/alloy · max 1)"
              hint="Popular crafted (teal) mods for this slot - you may keep one"
              mods={data.suggested_crafted}
            />
          )}
          {data.desecrated_slot_open && data.suggested_desecrated.length > 0 && (
            <ModList
              title="Desecrated mod (bone · max 1)"
              hint="Popular desecrated (green) mods for this slot - you may keep one"
              mods={data.suggested_desecrated}
            />
          )}
        </>
      )}

      {data.similar_count > 0 && (
        <div className="fa-similar-section">
          <button className="fa-similar-toggle" onClick={() => setShowSimilar((v) => !v)}>
            {showSimilar ? '▾' : '▸'} {data.similar_count} similar meta items
            {data.similar_basis ? ` · ${data.similar_basis}` : ''}
          </button>
          {showSimilar && (
            <ul className="fa-similar-list">
              {data.similar_items.map((s, i) => (
                <SimilarRow key={i} s={s} />
              ))}
            </ul>
          )}
        </div>
      )}

      {data.note && <div className="fa-note">{data.note}</div>}
    </div>
  )
}

export default FinishAdvisorPanel
