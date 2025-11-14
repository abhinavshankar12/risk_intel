import React, { useState, useEffect } from 'react'
import apiService from '../services/api'
import HotspotMap from '../components/HotspotMap'
import RegionDetail from '../components/RegionDetail'
import TopRiskRegions from '../components/TopRiskRegions'

function HotspotDashboard() {
  const [regions, setRegions] = useState([])
  const [riskScores, setRiskScores] = useState([])
  const [selectedRegion, setSelectedRegion] = useState(null)
  const [selectedDate, setSelectedDate] = useState(getTodayDate())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  function getTodayDate() {
    return new Date().toISOString().split('T')[0]
  }

  useEffect(() => {
    loadData()
  }, [selectedDate])

  async function loadData() {
    setLoading(true)
    setError(null)
    
    try {
      const [regionsRes, scoresRes] = await Promise.all([
        apiService.getRegions(),
        apiService.getRiskScores({ date: selectedDate })
      ])
      
      setRegions(regionsRes.data)
      setRiskScores(scoresRes.data)
    } catch (err) {
      console.error('Error loading data:', err)
      setError('Failed to load data. Please ensure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  function handleRegionClick(regionId) {
    setSelectedRegion(regionId)
  }

  function handleCloseDetail() {
    setSelectedRegion(null)
  }

  if (loading) {
    return (
      <div className="loading">
        <p>Loading hotspot data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error">
        <p>{error}</p>
        <button onClick={loadData} className="primary" style={{ marginTop: '1rem' }}>
          Retry
        </button>
      </div>
    )
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedRegion ? '1fr 1fr' : '2fr 1fr', gap: '2rem', height: 'calc(100vh - 200px)' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div className="card" style={{ padding: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600' }}>Hotspot Map</h2>
            <div>
              <label style={{ marginRight: '0.5rem', fontSize: '0.875rem', color: '#6b7280' }}>
                Date:
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                style={{
                  padding: '0.375rem 0.75rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem'
                }}
              />
            </div>
          </div>
        </div>
        
        <div className="card" style={{ flex: 1, padding: 0, overflow: 'hidden' }}>
          <HotspotMap
            regions={regions}
            riskScores={riskScores}
            onRegionClick={handleRegionClick}
            selectedRegion={selectedRegion}
          />
        </div>
      </div>

      {selectedRegion ? (
        <RegionDetail
          regionId={selectedRegion}
          date={selectedDate}
          onClose={handleCloseDetail}
        />
      ) : (
        <TopRiskRegions
          riskScores={riskScores}
          regions={regions}
          onRegionClick={handleRegionClick}
        />
      )}
    </div>
  )
}

export default HotspotDashboard

