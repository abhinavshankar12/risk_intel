import React, { useMemo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

function HotspotMap({ regions, riskScores, onRegionClick, selectedRegion }) {
  const regionMap = useMemo(() => {
    const map = {}
    regions.forEach(r => {
      map[r.region_id] = r
    })
    return map
  }, [regions])

  const getRiskColor = (tier) => {
    switch (tier) {
      case 'high':
        return '#dc2626'
      case 'medium':
        return '#ea580c'
      case 'low':
        return '#16a34a'
      default:
        return '#6b7280'
    }
  }

  const getRadius = (tier) => {
    switch (tier) {
      case 'high':
        return 20
      case 'medium':
        return 15
      case 'low':
        return 10
      default:
        return 8
    }
  }

  // Default center (can be made configurable)
  const center = [39.8283, -98.5795] // Center of US
  const zoom = 5

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {riskScores.map((score) => {
          const region = regionMap[score.region_id]
          if (!region) return null
          
          // For demo, use region_id as mock coordinates
          // In production, use actual geom data
          const lat = 35 + (score.region_id * 2) % 15
          const lng = -120 + (score.region_id * 3) % 40
          
          return (
            <CircleMarker
              key={score.region_id}
              center={[lat, lng]}
              radius={getRadius(score.risk_tier)}
              fillColor={getRiskColor(score.risk_tier)}
              color={selectedRegion === score.region_id ? '#000' : '#fff'}
              weight={selectedRegion === score.region_id ? 3 : 1}
              opacity={1}
              fillOpacity={0.7}
              eventHandlers={{
                click: () => onRegionClick(score.region_id)
              }}
            >
              <Tooltip>
                <strong>{region.name}</strong>
                <br />
                Risk: {score.risk_tier}
                <br />
                Score: {score.r_smoothed.toFixed(3)}
              </Tooltip>
              <Popup>
                <div style={{ minWidth: '150px' }}>
                  <strong>{region.name}</strong>
                  <br />
                  <span className={`badge badge-${score.risk_tier}`}>
                    {score.risk_tier}
                  </span>
                  <br />
                  <small>
                    Smoothed Score: {score.r_smoothed.toFixed(3)}
                    <br />
                    Raw Prediction: {score.p_raw.toFixed(3)}
                  </small>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>
      
      {/* Legend */}
      <div style={{
        position: 'absolute',
        bottom: '2rem',
        right: '1rem',
        background: 'white',
        padding: '1rem',
        borderRadius: '0.5rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        zIndex: 1000
      }}>
        <div style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
          Risk Level
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              backgroundColor: '#dc2626'
            }} />
            <span style={{ fontSize: '0.75rem' }}>High</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              width: '15px',
              height: '15px',
              borderRadius: '50%',
              backgroundColor: '#ea580c'
            }} />
            <span style={{ fontSize: '0.75rem' }}>Medium</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: '#16a34a'
            }} />
            <span style={{ fontSize: '0.75rem' }}>Low</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HotspotMap

