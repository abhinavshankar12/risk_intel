/**
 * API service for communicating with backend
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const apiService = {
  // Region endpoints
  getRegions: () => api.get('/api/regions'),
  getRegion: (regionId) => api.get(`/api/regions/${regionId}`),
  
  // Risk score endpoints
  getRiskScores: (params = {}) => api.get('/api/risk_scores', { params }),
  getRegionRiskHistory: (regionId, params = {}) => 
    api.get(`/api/regions/${regionId}/risk_history`, { params }),
  
  // Incident endpoints
  getRecentIncidents: (regionId, limit = 10) => 
    api.get(`/api/regions/${regionId}/recent_incidents`, { params: { limit } }),
  
  // Copilot endpoints
  explainHotspot: (regionId, date) => 
    api.get('/api/copilot/explain_hotspot', { params: { region_id: regionId, date } }),
  
  // Model endpoints
  getActiveModel: () => api.get('/api/models/active'),
  getModels: (limit = 10) => api.get('/api/models', { params: { limit } }),
  
  // Audit endpoints
  getAuditLogs: (params = {}) => api.get('/api/audit/logs', { params }),
}

export default apiService

