import React, { useMemo } from 'react'

function TopRiskRegions({ riskScores, regions, onRegionClick }) {
  const regionMap = useMemo(() => {
    const map = {}
    regions.forEach(r => {
      map[r.region_id] = r
    })
    return map
  }, [regions])

  const sortedScores = useMemo(() => {
    return [...riskScores].sort((a, b) => b.r_smoothed - a.r_smoothed)
  }, [riskScores])

  const topHighRisk = sortedScores.filter(s => s.risk_tier === 'high').slice(0, 10)

  const tierCounts = useMemo(() => {
    return {
      high: riskScores.filter(s => s.risk_tier === 'high').length,
      medium: riskScores.filter(s => s.risk_tier === 'medium').length,
      low: riskScores.filter(s => s.risk_tier === 'low').length,
    }
  }, [riskScores])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Summary Cards */}
      <div className="card">
        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
          Risk Summary
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>High Risk Regions</span>
            <span className="badge badge-high">{tierCounts.high}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Medium Risk Regions</span>
            <span className="badge badge-medium">{tierCounts.medium}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Low Risk Regions</span>
            <span className="badge badge-low">{tierCounts.low}</span>
          </div>
        </div>
      </div>

      {/* Top Risk Regions */}
      <div className="card" style={{ flex: 1, overflow: 'auto' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
          High Risk Regions
        </h3>
        {topHighRisk.length === 0 ? (
          <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
            No high risk regions for this date.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {topHighRisk.map((score) => {
              const region = regionMap[score.region_id]
              if (!region) return null
              
              return (
                <div
                  key={score.region_id}
                  onClick={() => onRegionClick(score.region_id)}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f9fafb'
                    e.currentTarget.style.borderColor = '#3b82f6'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent'
                    e.currentTarget.style.borderColor = '#e5e7eb'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                    <div style={{ fontWeight: '600', fontSize: '0.9375rem' }}>
                      {region.name}
                    </div>
                    <span className={`badge badge-${score.risk_tier}`}>
                      {score.risk_tier}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#6b7280' }}>
                    <div>
                      <span>Score: </span>
                      <span style={{ fontWeight: '600', color: '#374151' }}>
                        {score.r_smoothed.toFixed(3)}
                      </span>
                    </div>
                    <div>
                      <span>Raw: </span>
                      <span style={{ fontWeight: '600', color: '#374151' }}>
                        {score.p_raw.toFixed(3)}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default TopRiskRegions

