import axios from 'axios'

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8081'

export function getAvatarUrl(userId, cacheKey = null) {
  if (userId == null || userId === '') return null
  let url = `${API_URL}/user/avatar/${userId}`
  if (cacheKey != null && cacheKey !== '') {
    url += `?v=${encodeURIComponent(cacheKey)}`
  }
  return url
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: async (username, password) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    
    const response = await api.post('/user/login', params.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  register: async (userData) => {
    const response = await api.post('/user/register', userData)
    return response.data
  },
}

export const mangaAPI = {
  getAll: async (page = 1, limit = 20, category = null, search = null) => {
    const params = { page, limit }
    if (category) {
      params.category = category
    }
    if (search) {
      params.search = search
    }
    const response = await api.get('/manga/mangas', { params })
    return response.data
  },

  getById: async (id) => {
    const response = await api.get(`/manga/mangas/${id}`)
    return response.data
  },

  getCategories: async () => {
    const response = await api.get('/manga/mangas/categories')
    return response.data
  },
}

export const favoriteAPI = {
  getAll: async () => {
    const response = await api.get('/user/favorites')
    return response.data
  },

  add: async (mangaId) => {
    const response = await api.post('/user/favorites', { manga_id: mangaId })
    return response.data
  },

  remove: async (mangaId) => {
    const response = await api.delete(`/user/favorites/${mangaId}`)
    return response.data
  },
}

export const userAPI = {
  getCurrentUser: async () => {
    const response = await api.get('/user/me')
    return response.data
  },

  uploadAvatar: async (file) => {
    const form = new FormData()
    form.append('file', file)
    const response = await api.post('/user/me/avatar', form)
    return response.data
  },

  deleteAvatar: async () => {
    const response = await api.delete('/user/me/avatar')
    return response.data
  },
}

export const recommendationAPI = {
  getRecommendations: async (userId, limit = 10) => {
    const response = await api.get(`/recom/recommendations/${userId}?limit=${limit}`)
    return response.data
  },

  getStats: async () => {
    const response = await api.get('/recom/recommendations/stats')
    return response.data
  },
}

export default api
