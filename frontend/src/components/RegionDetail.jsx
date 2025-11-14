import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import apiService from '../services/api'

function RegionDetail({ regionId, date, onClose }) {
  const [region, setRegion] = useState(null)
  const [riskHistory, setRiskHistory] = useState([])
  const [incidents, setIncidents] = useState([])
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [explanationLoading, setExplanationLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [regionId, date])

  async function loadData() {
    setLoading(true)
    
    try {
      const [regionRes, historyRes, incidentsRes] = await Promise.all([
        apiService.getRegion(regionId),
        apiService.getRegionRiskHistory(regionId, { limit: 30 }),
        apiService.getRecentIncidents(regionId, 10)
      ])
      
      setRegion(regionRes.data)
      setRiskHistory(historyRes.data.reverse()) // Reverse to show oldest first
      setIncidents(incidentsRes.data)
    } catch (err) {
      console.error('Error loading region detail:', err)
    } finally {
      setLoading(false)
    }
  }

  async function loadExplanation() {
    setExplanationLoading(true)
    
    try {
      const res = await apiService.explainHotspot(regionId, date)
      setExplanation(res.data.explanation)
    } catch (err) {
      console.error('Error loading explanation:', err)
      setExplanation('Unable to generate explanation. The AI service may be unavailable.')
    } finally {
      setExplanationLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="card" style={{ height: '100%' }}>
        <div className="loading">Loading region details...</div>
      </div>
    )
  }

  if (!region) {
    return (
      <div className="card" style={{ height: '100%' }}>
        <p>Region not found</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%', overflow: 'auto' }}>
      {/* Header */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              {region.name}
            </h2>
            <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              Baseline Risk: {region.baseline_risk.toFixed(3)}
            </p>
          </div>
          <button onClick={onClose} className="secondary">
            Close
          </button>
        </div>
      </div>

      {/* Risk History Chart */}
      <div className="card">
        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
          Risk Score History
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={riskHistory}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickFormatter={(date) => new Date(date).toLocaleDateString()}
            />
            <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
            <Tooltip
              labelFormatter={(date) => new Date(date).toLocaleDateString()}
              formatter={(value) => value.toFixed(3)}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="r_smoothed"
              stroke="#3b82f6"
              name="Smoothed Score"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="p_raw"
              stroke="#10b981"
              name="Raw Prediction"
              strokeWidth={1}
              strokeDasharray="5 5"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* AI Explanation */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600' }}>
            AI Explanation
          </h3>
          <button
            onClick={loadExplanation}
            disabled={explanationLoading}
            className="primary"
            style={{ fontSize: '0.875rem', padding: '0.375rem 0.75rem' }}
          >
            {explanationLoading ? 'Generating...' : 'Generate Explanation'}
          </button>
        </div>
        {explanation ? (
          <div style={{
            padding: '1rem',
            backgroundColor: '#f9fafb',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
            lineHeight: '1.5',
            whiteSpace: 'pre-wrap'
          }}>
            {explanation}
          </div>
        ) : (
          <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
            Click "Generate Explanation" to get an AI-powered analysis of this region's risk factors.
          </p>
        )}
      </div>

      {/* Recent Incidents */}
      <div className="card">
        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
          Recent Incidents
        </h3>
        {incidents.length === 0 ? (
          <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>No recent incidents</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((incident) => (
                  <tr key={incident.incident_id}>
                    <td style={{ fontSize: '0.875rem' }}>
                      {new Date(incident.occurred_at).toLocaleDateString()}
                    </td>
                    <td style={{ textTransform: 'capitalize' }}>
                      {incident.type.replace('_', ' ')}
                    </td>
                    <td>
                      <div style={{
                        display: 'inline-block',
                        padding: '0.125rem 0.5rem',
                        borderRadius: '0.25rem',
                        backgroundColor: incident.severity > 0.7 ? '#fecaca' :
                                        incident.severity > 0.4 ? '#fed7aa' : '#d1fae5',
                        color: incident.severity > 0.7 ? '#991b1b' :
                               incident.severity > 0.4 ? '#9a3412' : '#065f46',
                        fontSize: '0.75rem',
                        fontWeight: '600'
                      }}>
                        {incident.severity.toFixed(2)}
                      </div>
                    </td>
                    <td style={{ fontSize: '0.875rem' }}>{incident.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default RegionDetail

