import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { PoE2ItemFrame, PoE2Section, PoE2Separator } from '@/components/poe2'
import { buildsApi } from '@/services/builds-api'
import type { BuildDetail as BuildDetailType, ResolvedBuildItem, ResolvedBuildMod } from '@/types/builds'
import './BuildDetail.css'

function fmtDps(dps: number): string {
  if (dps >= 1_000_000) return `${(dps / 1_000_000).toFixed(dps >= 10_000_000 ? 0 : 1)}M`
  if (dps >= 1_000) return `${(dps / 1_000).toFixed(dps >= 100_000 ? 0 : 1)}k`
  return String(dps)
}

// origin/mod_type -> the poe2-mod-line colour class
function modClass(mod: ResolvedBuildMod): string {
  switch (mod.origin) {
    case 'implicit':
      return 'implicit'
    case 'enchant':
      return 'enchant'
    case 'rune':
      return 'rune'
    case 'fractured':
      return 'fractured'
    case 'desecrated':
      return 'desecrated'
    case 'crafted':
      return 'crafted'
    default:
      return mod.mod_type === 'suffix' ? 'suffix' : 'prefix'
  }
}

function ModLine({ mod }: { mod: ResolvedBuildMod }) {
  const badge =
    mod.resolved && mod.tier != null
      ? `T${mod.tier}`
      : mod.origin === 'rune'
        ? 'rune'
        : mod.origin === 'crafted'
          ? 'crafted'
          : mod.origin === 'enchant'
            ? 'enchant'
            : ''
  return (
    <div className={`poe2-mod-line ${modClass(mod)}`} title={mod.mod_group || undefined}>
      <div className="poe2-mod-content">
        <span className="poe2-mod-text">{mod.text}</span>
        {badge && <span className="poe2-mod-tier">{badge}</span>}
      </div>
    </div>
  )
}

const AFFIX_ORIGINS = ['explicit', 'crafted', 'fractured', 'desecrated']

function BuildItemFrame({ item }: { item: ResolvedBuildItem }) {
  const byOrigin = (o: string) => item.mods.filter((m) => m.origin === o)
  const enchant = byOrigin('enchant')
  const implicit = byOrigin('implicit')
  const affixes = item.mods.filter((m) => AFFIX_ORIGINS.includes(m.origin))
  const runeMods = byOrigin('rune')

  const itemName = item.name || item.base_type
  const itemBase = item.name ? item.base_type : undefined

  return (
    <PoE2ItemFrame rarity={item.rarity} itemName={itemName} itemBase={itemBase} className="build-item">
      <PoE2Section>
        <div className="bi-meta">
          <span className="bi-slot">{item.slot.replace(/_/g, ' ')}</span>
          {item.item_level > 0 && <span className="bi-ilvl">ilvl {item.item_level}</span>}
          {item.corrupted && <span className="bi-corrupted">Corrupted</span>}
        </div>
      </PoE2Section>

      {enchant.length > 0 && (
        <>
          <PoE2Separator />
          <PoE2Section>{enchant.map((m, i) => <ModLine key={`e${i}`} mod={m} />)}</PoE2Section>
        </>
      )}

      {implicit.length > 0 && (
        <>
          <PoE2Separator />
          <PoE2Section>{implicit.map((m, i) => <ModLine key={`im${i}`} mod={m} />)}</PoE2Section>
        </>
      )}

      {affixes.length > 0 && (
        <>
          <PoE2Separator />
          <PoE2Section>{affixes.map((m, i) => <ModLine key={`a${i}`} mod={m} />)}</PoE2Section>
        </>
      )}

      {runeMods.length > 0 && (
        <>
          <PoE2Separator />
          <PoE2Section title={item.runes.length ? `Runes: ${item.runes.join(', ')}` : 'Runes'}>
            {runeMods.map((m, i) => <ModLine key={`r${i}`} mod={m} />)}
          </PoE2Section>
        </>
      )}
    </PoE2ItemFrame>
  )
}

function BuildDetail() {
  const { buildId } = useParams<{ buildId: string }>()
  const [build, setBuild] = useState<BuildDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!buildId) return
    let cancelled = false
    setLoading(true)
    setError(null)
    buildsApi
      .getBuild(buildId)
      .then((b) => !cancelled && setBuild(b))
      .catch((err) => {
        if (cancelled) return
        setError(err?.response?.status === 404 ? 'Build not found.' : 'Failed to load build.')
        console.error(err)
      })
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [buildId])

  const copyPob = () => {
    if (!build?.pob_export) return
    navigator.clipboard.writeText(build.pob_export).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    })
  }

  return (
    <div className="build-detail">
      <Link to="/builds" className="bd-back">← Back to builds</Link>

      {loading && <div className="bd-state">Loading build…</div>}
      {error && <div className="bd-state bd-error">{error}</div>}

      {build && (
        <>
          <div className="bd-header">
            <div className="bd-id">
              <h1>{build.character}</h1>
              <div className="bd-class">
                <span className="bd-ascendancy">{build.ascendancy || build.base_class || 'Unknown'}</span>
                {build.base_class && build.ascendancy && (
                  <span className="bd-baseclass">{build.base_class}</span>
                )}
                <span className="bd-level">Level {build.level}</span>
              </div>
            </div>
            <div className="bd-actions">
              {build.poeninja_url && (
                <a className="bd-btn" href={build.poeninja_url} target="_blank" rel="noreferrer">
                  View on poe.ninja
                </a>
              )}
              {build.pob_export && (
                <button className="bd-btn bd-btn-primary" onClick={copyPob}>
                  {copied ? 'Copied!' : 'Copy PoB code'}
                </button>
              )}
            </div>
          </div>

          <div className="bd-defense">
            {build.defense.life > 0 && <Stat label="Life" value={build.defense.life} cls="life" />}
            {build.defense.energy_shield > 0 && <Stat label="Energy Shield" value={build.defense.energy_shield} cls="es" />}
            {build.defense.mana > 0 && <Stat label="Mana" value={build.defense.mana} cls="mana" />}
            {build.defense.ehp > 0 && <Stat label="EHP" value={build.defense.ehp} cls="ehp" />}
            <Stat label="Fire" value={`${build.defense.fire_res}%`} cls="fire" />
            <Stat label="Cold" value={`${build.defense.cold_res}%`} cls="cold" />
            <Stat label="Lightning" value={`${build.defense.lightning_res}%`} cls="lightning" />
            <Stat label="Chaos" value={`${build.defense.chaos_res}%`} cls="chaos" />
          </div>

          {build.main_skills.length > 0 && (
            <div className="bd-skills">
              <h2>Skills</h2>
              <div className="bd-skills-list">
                {build.main_skills.map((s, i) => (
                  <div key={i} className="bd-skill">
                    <div className="bd-skill-head">
                      <span className="bd-skill-name">{s.name}</span>
                      {s.dps > 0 && <span className="bd-skill-dps">{fmtDps(s.dps)} dps</span>}
                    </div>
                    {s.supports.length > 0 && (
                      <div className="bd-skill-supports">
                        {s.supports.map((sup) => (
                          <span key={sup} className="support-chip">{sup}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bd-gear">
            <h2>Gear</h2>
            <div className="bd-gear-grid">
              {build.items.map((it, i) => (
                <BuildItemFrame key={`${it.slot}-${i}`} item={it} />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function Stat({ label, value, cls }: { label: string; value: string | number; cls: string }) {
  return (
    <div className={`bd-stat bd-stat-${cls}`}>
      <span className="bd-stat-value">{value}</span>
      <span className="bd-stat-label">{label}</span>
    </div>
  )
}

export default BuildDetail
