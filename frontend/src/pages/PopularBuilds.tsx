import { useEffect, useMemo, useState } from 'react'
import { buildsApi } from '@/services/builds-api'
import type {
  BuildsMeta,
  TrendingBase,
  BaseDetail,
  TrendingMod,
  BasePricing,
  PricingTargetMod,
  MarketInfo,
} from '@/types/builds'
import './PopularBuilds.css'

const ORIGIN_LABELS: Record<string, string> = {
  explicit: 'Explicit',
  implicit: 'Implicit',
  rune: 'Rune',
  crafted: 'Crafted',
  fractured: 'Fractured',
  desecrated: 'Desecrated',
  enchant: 'Enchant',
}

function pct(v: number): string {
  return `${Math.round(v * 100)}%`
}

function TierDistribution({ dist }: { dist: Record<string, number> }) {
  const entries = Object.entries(dist).sort((a, b) => Number(a[0]) - Number(b[0]))
  if (entries.length === 0) return null
  return (
    <span className="tier-dist">
      {entries.map(([tier, count]) => (
        <span key={tier} className="tier-chip" title={`Tier ${tier}: ${count} builds`}>
          T{tier}<span className="tier-count">×{count}</span>
        </span>
      ))}
    </span>
  )
}

const VERDICT_LABELS: Record<string, string> = {
  buy: 'Buy',
  craft_candidate: 'Craft candidate',
  available: 'Available',
  pricing_unavailable: 'Pricing unavailable',
  unknown: 'Unknown',
}

function fillMod(m: PricingTargetMod): string {
  return m.stat_text.replace('#', String(Math.round(m.value)))
}

function PriceLadderRow({
  label,
  hint,
  market,
  url,
  highlight,
}: {
  label: string
  hint: string
  market?: MarketInfo | null
  url?: string | null
  highlight?: boolean
}) {
  return (
    <div className={`ladder-row ${highlight ? 'ladder-row-hl' : ''}`}>
      <div className="ladder-main">
        <span className="ladder-label">{label}</span>
        <span className="ladder-hint">{hint}</span>
      </div>
      <div className="ladder-price">
        {market && (market.divine != null || market.chaos_floor != null) ? (
          <>
            {market.divine != null ? (
              <span className="price-tag">{market.divine} div</span>
            ) : (
              <span className="price-tag chaos">{market.chaos_floor} chaos</span>
            )}
            {market.num_listings != null && (
              <span className="ladder-liq">
                {market.num_listings} · {market.confidence}
              </span>
            )}
          </>
        ) : (
          <span className="ladder-na">price in browser</span>
        )}
        {url && (
          <a className="ladder-link" href={url} target="_blank" rel="noreferrer" title="Search on trade">
            ↗
          </a>
        )}
      </div>
    </div>
  )
}

function ModRow({ mod }: { mod: TrendingMod }) {
  return (
    <div className={`mod-row ${mod.resolved ? '' : 'mod-unresolved'}`}>
      <div className="mod-main">
        <span className={`mod-origin origin-${mod.mod_origin}`}>
          {ORIGIN_LABELS[mod.mod_origin] || mod.mod_origin}
        </span>
        <span className="mod-text">{mod.mod_template}</span>
      </div>
      <div className="mod-meta">
        <span className="mod-usage">{pct(mod.usage_pct)}</span>
        {mod.modal_tier != null && <span className="mod-tier">most common: T{mod.modal_tier}</span>}
        <TierDistribution dist={mod.tier_distribution} />
      </div>
    </div>
  )
}

function PopularBuilds({ embedded = false }: { embedded?: boolean }) {
  const [meta, setMeta] = useState<BuildsMeta | null>(null)
  const [bases, setBases] = useState<TrendingBase[]>([])
  const [slot, setSlot] = useState<string>('')
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<BaseDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pricing, setPricing] = useState<BasePricing | null>(null)
  const [pricingLoading, setPricingLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    Promise.all([buildsApi.getMeta(), buildsApi.getTrendingBases()])
      .then(([m, b]) => {
        if (cancelled) return
        setMeta(m)
        setBases(b)
      })
      .catch((err) => {
        if (cancelled) return
        const status = err?.response?.status
        setError(
          status === 503
            ? 'Build data is not available yet. The scraper artifact has not been configured.'
            : 'Failed to load build data.'
        )
        console.error(err)
      })
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [])

  const slots = useMemo(
    () => Array.from(new Set(bases.map((b) => b.slot))).sort(),
    [bases]
  )
  const visibleBases = useMemo(
    () => (slot ? bases.filter((b) => b.slot === slot) : bases),
    [bases, slot]
  )

  const selectBase = (name: string) => {
    setSelected(name)
    setDetail(null)
    setPricing(null)
    setDetailLoading(true)
    buildsApi
      .getBaseDetail(name)
      .then(setDetail)
      .catch((err) => console.error(err))
      .finally(() => setDetailLoading(false))
  }

  const checkPrice = () => {
    if (!selected) return
    setPricingLoading(true)
    buildsApi
      .priceBase(selected)
      .then(setPricing)
      .catch((err) => {
        console.error(err)
        setPricing(null)
      })
      .finally(() => setPricingLoading(false))
  }

  return (
    <div className="popular-builds">
      <div className="pb-header">
        {!embedded && <h1>Popular Builds</h1>}
        {meta && (
          <p className="pb-subtitle">
            What item bases and mods the meta uses in <strong>{meta.league}</strong> -
            from <strong>{meta.sample_size}</strong> tracked builds
            {meta.scraped_at && <> · snapshot {new Date(meta.scraped_at).toLocaleDateString()}</>}
          </p>
        )}
      </div>

      {loading && <div className="pb-state">Loading build data…</div>}
      {error && <div className="pb-state pb-error">{error}</div>}

      {!loading && !error && (
        <>
          <div className="pb-filters">
            <button
              className={`pb-chip ${slot === '' ? 'pb-chip-active' : ''}`}
              onClick={() => setSlot('')}
            >
              All slots
            </button>
            {slots.map((s) => (
              <button
                key={s}
                className={`pb-chip ${slot === s ? 'pb-chip-active' : ''}`}
                onClick={() => setSlot(s)}
              >
                {s.replace(/_/g, ' ')}
              </button>
            ))}
          </div>

          <div className="pb-layout">
            <div className="pb-bases">
              {visibleBases.map((b) => (
                <button
                  key={`${b.base_name}-${b.slot}`}
                  className={`base-card ${selected === b.base_name ? 'base-card-active' : ''}`}
                  onClick={() => selectBase(b.base_name)}
                >
                  <div className="base-card-top">
                    <span className="base-name">{b.base_name}</span>
                    <span className="base-usage">{pct(b.usage_pct)}</span>
                  </div>
                  <div className="base-card-bottom">
                    <span className="base-slot">{b.slot.replace(/_/g, ' ')}</span>
                    {b.rarity_mix.unique ? (
                      <span className="base-rarity rarity-unique">
                        {b.rarity_mix.unique} unique
                      </span>
                    ) : null}
                    {b.rarity_mix.rare ? (
                      <span className="base-rarity rarity-rare">{b.rarity_mix.rare} rare</span>
                    ) : null}
                    {!b.resolves_in_app && (
                      <span className="base-unresolved" title="Not matched to a craftable base">
                        ?
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>

            <div className="pb-detail">
              {!selected && <div className="pb-state">Select a base to see its popular mods.</div>}
              {selected && detailLoading && <div className="pb-state">Loading mods…</div>}
              {detail && (
                <>
                  <div className="detail-head">
                    <h2>{detail.base_name}</h2>
                    <span className="detail-sub">
                      {detail.category || detail.slot.replace(/_/g, ' ')} · used by {detail.usage_count} builds
                    </span>
                    {detail.common_skills.length > 0 && (
                      <span className="detail-skills">
                        Common skills: {detail.common_skills.join(', ')}
                      </span>
                    )}
                  </div>
                  <div className="pricing-panel">
                    {!pricing && !pricingLoading && (
                      <button className="price-btn" onClick={checkPrice}>
                        Check market price (buy vs craft)
                      </button>
                    )}
                    {pricingLoading && <span className="pb-muted">Pricing on the live market…</span>}
                    {pricing && (
                      <div className="pricing-result">
                        <div className={`verdict verdict-${pricing.verdict}`}>
                          {VERDICT_LABELS[pricing.verdict] || 'Unknown'}
                        </div>
                        {pricing.message && <span className="pricing-msg">{pricing.message}</span>}

                        <div className="buy-ladder">
                          <div className="ladder-title">
                            Buy vs craft{pricing.base_ilvl ? ` · base ilvl ${pricing.base_ilvl}+` : ''}
                          </div>
                          <PriceLadderRow
                            label="White base"
                            hint={pricing.base_ilvl ? `ilvl ${pricing.base_ilvl}+ raw base` : 'raw base, slam it yourself'}
                            market={pricing.base_market}
                            url={pricing.base_market?.trade_url || pricing.base_trade_url}
                          />
                          <PriceLadderRow
                            label="Magic partial"
                            hint={
                              pricing.magic_mods.length > 0
                                ? pricing.magic_mods.map((m) => fillMod(m)).join(' + ')
                                : 'blue base, top prefix + suffix'
                            }
                            market={pricing.magic_market}
                            url={pricing.magic_trade_url}
                          />
                          <PriceLadderRow
                            label="Finished rare (good)"
                            hint={`${pricing.prefixes}p / ${pricing.suffixes}s top-tier meta mods`}
                            market={pricing.market}
                            url={pricing.market?.trade_url || pricing.trade_search_url}
                            highlight
                          />
                          {pricing.market_typical?.divine != null && (
                            <div className="ladder-typical">
                              A typical roll floors around {pricing.market_typical.divine} div
                            </div>
                          )}
                        </div>

                        {pricing.target_mods.length > 0 && (
                          <div className="priced-item">
                            <div className="priced-item-head">
                              A good roll (top meta tiers)
                              {pricing.item_level ? ` · ilvl ${pricing.item_level}` : ''}
                            </div>
                            {pricing.target_mods.map((m, i) => (
                              <div key={i} className={`priced-mod origin-${m.origin}`}>
                                <span className="pm-tier">T{m.tier}</span>
                                <span className="pm-text">{fillMod(m)}</span>
                                <span className="pm-usage" title="share of builds using this mod">
                                  {pct(m.usage_pct)}
                                </span>
                                {m.trade_url && (
                                  <a
                                    className="pm-trade"
                                    href={m.trade_url}
                                    target="_blank"
                                    rel="noreferrer"
                                  >
                                    trade ↗
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
                        )}

                        {pricing.note && <div className="pricing-note">{pricing.note}</div>}
                      </div>
                    )}
                  </div>
                  <div className="mod-list">
                    {detail.mods.map((m, i) => (
                      <ModRow key={`${m.mod_template}-${m.mod_origin}-${i}`} mod={m} />
                    ))}
                    {detail.mods.length === 0 && (
                      <div className="pb-state">No mod data for this base.</div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          {meta?.disclaimer && <p className="pb-disclaimer">{meta.disclaimer}</p>}
        </>
      )}
    </div>
  )
}

export default PopularBuilds
