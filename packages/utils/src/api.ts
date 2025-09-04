import axios from 'axios'

// API Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth tokens
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API Functions
export const orchidApi = {
  // Get orchids with filtering
  getOrchids: (params?: {
    query?: string
    genus?: string
    growth_habit?: string
    light_min?: number
    light_max?: number
    temp_min?: number
    temp_max?: number
    page?: number
    limit?: number
  }) => api.get('/orchids', { params }),

  // Get single orchid
  getOrchid: (id: string) => api.get(`/orchids/${id}`),

  // Create orchid (admin/editor only)
  createOrchid: (data: any) => api.post('/orchids', data),

  // Get care wheel data
  getCareWheel: (id: string) => api.get(`/orchids/${id}/care-wheel`),
}

export const searchApi = {
  // Search by growing conditions
  searchByConditions: (params: {
    light?: string
    temperature?: string
    humidity?: string
    limit?: number
  }) => api.get('/search/conditions', { params }),

  // Autocomplete search
  autocomplete: (query: string) => api.get('/search/autocomplete', { params: { q: query } }),
}

export const authApi = {
  // Login
  login: (email: string, password: string) => 
    api.post('/auth/login', { email, password }),

  // Register
  register: (data: {
    email: string
    password: string
    display_name?: string
  }) => api.post('/auth/register', data),

  // Get current user
  getCurrentUser: () => api.get('/auth/me'),

  // Refresh token
  refreshToken: () => api.post('/auth/refresh'),
}

export const widgetApi = {
  // Get widget embed code
  getEmbedCode: (widget: string, options?: Record<string, any>) => 
    api.get(`/widgets/js/${widget}`, { params: options }),
}

export const adminApi = {
  // System health
  getSystemHealth: () => api.get('/admin/health'),

  // Sync status
  getSyncStatus: () => api.get('/admin/sync-status'),

  // Trigger sync
  triggerSync: (source: string) => api.post(`/admin/sync/${source}`),

  // Data quality report
  getDataQuality: () => api.get('/admin/data-quality'),

  // Export data
  exportData: (format: string = 'json') => 
    api.get('/admin/export/orchids', { params: { format } }),
}

export const ingestApi = {
  // GBIF ingestion
  ingestFromGBIF: (data: {
    scientific_name: string
    limit?: number
    include_media?: boolean
    include_occurrences?: boolean
  }) => api.post('/ingest/gbif', data),

  // Google Drive ingestion
  ingestFromDrive: (folder_id: string) => 
    api.post('/ingest/google-drive', { folder_id }),

  // Get data sources
  getDataSources: () => api.get('/ingest/sources'),
}

// Utility functions
export const formatScientificName = (name: string) => {
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return `${parts[0]} ${parts[1]}`
  }
  return name
}

export const getImageUrl = (photo: any) => {
  if (!photo) return null
  
  // Handle different photo sources
  if (photo.source === 'google_drive' && photo.source_ref) {
    return `https://drive.google.com/uc?id=${photo.source_ref}`
  }
  
  return photo.url
}

export const getCareLevel = (value: number, type: 'light' | 'temperature' | 'humidity') => {
  const levels = {
    light: {
      very_low: [0, 800],
      low: [800, 1200],
      medium: [1200, 2000],
      high: [2000, 3000],
      very_high: [3000, 5000]
    },
    temperature: {
      cool: [10, 20],
      cool_intermediate: [15, 22],
      intermediate: [18, 25],
      cool_warm: [20, 28],
      warm: [25, 35]
    },
    humidity: {
      low: [30, 50],
      moderate: [50, 70],
      high: [70, 85],
      very_high: [85, 95]
    }
  }
  
  for (const [level, [min, max]] of Object.entries(levels[type])) {
    if (value >= min && value <= max) {
      return level
    }
  }
  
  return 'unknown'
}

export default api