import { useState, useEffect } from 'react'
import { buildsApi } from '@/services/api'
import type { Build, League } from '@/types/build'
import './BuildBrowser.css'

function BuildBrowser() {
  const [builds, setBuilds] = useState<Build[]>([])
  const [leagues, setLeagues] = useState<League[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingLeagues, setLoadingLeagues] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedLeague, setSelectedLeague] = useState<string>('')

  useEffect(() => {
    const fetchLeagues = async () => {
      try {
        const response = await buildsApi.getLeagues()
        const buildLeagues = response.buildLeagues.filter(l => l.indexed)
        setLeagues(buildLeagues)
        if (buildLeagues.length > 0) {
          setSelectedLeague(buildLeagues[0].url)
        }
      } catch (err) {
        console.error('Failed to load leagues:', err)
        setSelectedLeague('abyss')
      } finally {
        setLoadingLeagues(false)
      }
    }

    fetchLeagues()
  }, [])

  const handleFetchBuilds = async () => {
    if (!selectedLeague) {
      setError('Please select a league')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await buildsApi.getBuilds({ league: selectedLeague, limit: 20 })
      setBuilds(response.builds)
    } catch (err) {
      setError('Failed to fetch builds. poe.ninja API may not have build data yet.')
      setBuilds([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="build-browser">
      <h2 className="page-title">Build Browser</h2>
      <p className="page-subtitle">Browse popular builds from poe.ninja</p>

      <div className="controls">
        <select
          className="league-select"
          value={selectedLeague}
          onChange={(e) => setSelectedLeague(e.target.value)}
          disabled={loadingLeagues}
        >
          {loadingLeagues ? (
            <option>Loading leagues...</option>
          ) : leagues.length === 0 ? (
            <option>No leagues available</option>
          ) : (
            leagues.map((league) => (
              <option key={league.url} value={league.url}>
                {league.displayName}
              </option>
            ))
          )}
        </select>
        <button
          className="fetch-button"
          onClick={handleFetchBuilds}
          disabled={loading || loadingLeagues || !selectedLeague}
        >
          {loading ? 'Loading...' : 'Fetch Builds'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {builds.length > 0 && (
        <div className="builds-grid">
          {builds.map((build, idx) => (
            <div key={idx} className="build-card">
              <div className="build-header">
                <h3 className="build-name">{build.character.name}</h3>
                <span className="build-level">Level {build.character.level}</span>
              </div>

              <div className="build-info">
                <div className="info-row">
                  <span className="info-label">Class:</span>
                  <span className="info-value">{build.character.class}</span>
                </div>

                {build.character.ascendancy && (
                  <div className="info-row">
                    <span className="info-label">Ascendancy:</span>
                    <span className="info-value">{build.character.ascendancy}</span>
                  </div>
                )}

                {build.main_skill && (
                  <div className="info-row">
                    <span className="info-label">Main Skill:</span>
                    <span className="info-value">{build.main_skill}</span>
                  </div>
                )}
              </div>

              {build.stats && (
                <div className="build-stats">
                  {build.stats.life && (
                    <div className="stat-item">
                      <span className="stat-label">Life:</span>
                      <span className="stat-value">{build.stats.life}</span>
                    </div>
                  )}
                  {build.stats.energy_shield && (
                    <div className="stat-item">
                      <span className="stat-label">ES:</span>
                      <span className="stat-value">{build.stats.energy_shield}</span>
                    </div>
                  )}
                  {build.stats.dps && (
                    <div className="stat-item">
                      <span className="stat-label">DPS:</span>
                      <span className="stat-value">{build.stats.dps.toFixed(0)}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && builds.length === 0 && !error && (
        <div className="empty-state">
          <p>No builds loaded yet. Click "Fetch Builds" to load data.</p>
        </div>
      )}
    </div>
  )
}

export default BuildBrowser