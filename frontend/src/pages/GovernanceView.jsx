import React, { useState, useEffect } from 'react'
import apiService from '../services/api'

function GovernanceView() {
  const [activeModel, setActiveModel] = useState(null)
  const [models, setModels] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    setError(null)
    
    try {
      const [modelRes, modelsRes, logsRes] = await Promise.all([
        apiService.getActiveModel(),
        apiService.getModels(10),
        apiService.getAuditLogs({ limit: 50 })
      ])
      
      setActiveModel(modelRes.data)
      setModels(modelsRes.data)
      setAuditLogs(logsRes.data)
    } catch (err) {
      console.error('Error loading governance data:', err)
      setError('Failed to load governance data.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading"><p>Loading governance data...</p></div>
  }

  if (error) {
    return <div className="error"><p>{error}</p></div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '1400px' }}>
      {/* Active Model Section */}
      <div className="card">
        <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>
          Active Model
        </h2>
        {activeModel && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                Model Version
              </p>
              <p style={{ fontSize: '1.125rem', fontWeight: '600' }}>
                {activeModel.model_version}
              </p>
            </div>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                Algorithm
              </p>
              <p style={{ fontSize: '1.125rem', fontWeight: '600', textTransform: 'capitalize' }}>
                {activeModel.algorithm.replace('_', ' ')}
              </p>
            </div>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                Trained At
              </p>
              <p style={{ fontSize: '1.125rem', fontWeight: '600' }}>
                {new Date(activeModel.trained_at).toLocaleString()}
              </p>
            </div>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                Metrics
              </p>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                {Object.entries(activeModel.metrics_json).map(([key, value]) => (
                  <div key={key}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase' }}>
                      {key}:
                    </span>
                    <span style={{ marginLeft: '0.25rem', fontWeight: '600' }}>
                      {typeof value === 'number' ? value.toFixed(3) : value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Model History Section */}
      <div className="card">
        <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>
          Model History
        </h2>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Version</th>
                <th>Algorithm</th>
                <th>Trained At</th>
                <th>AUC</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model.id}>
                  <td style={{ fontWeight: '500' }}>{model.model_version}</td>
                  <td style={{ textTransform: 'capitalize' }}>
                    {model.algorithm.replace('_', ' ')}
                  </td>
                  <td>{new Date(model.trained_at).toLocaleDateString()}</td>
                  <td>{model.metrics_json.auc?.toFixed(3) || 'N/A'}</td>
                  <td>{model.metrics_json.precision?.toFixed(3) || 'N/A'}</td>
                  <td>{model.metrics_json.recall?.toFixed(3) || 'N/A'}</td>
                  <td>
                    {model.active_flag ? (
                      <span className="badge" style={{ backgroundColor: '#dcfce7', color: '#166534' }}>
                        Active
                      </span>
                    ) : (
                      <span className="badge" style={{ backgroundColor: '#f3f4f6', color: '#6b7280' }}>
                        Inactive
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Logs Section */}
      <div className="card">
        <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>
          Recent Audit Logs
        </h2>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action Type</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.slice(0, 20).map((log) => (
                <tr key={log.id}>
                  <td style={{ fontSize: '0.875rem' }}>
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td>{log.actor}</td>
                  <td>
                    <span className="badge" style={{ backgroundColor: '#dbeafe', color: '#1e40af' }}>
                      {log.action_type}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.875rem', maxWidth: '400px' }}>
                    {JSON.stringify(log.payload_json).slice(0, 100)}
                    {JSON.stringify(log.payload_json).length > 100 ? '...' : ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default GovernanceView

