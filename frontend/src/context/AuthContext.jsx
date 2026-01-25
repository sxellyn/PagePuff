import React, { createContext, useState, useContext, useEffect } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('token')
      const userData = localStorage.getItem('user')
      
      if (token && userData) {
        const parsedUser = JSON.parse(userData)
        if (!parsedUser.id && token) {
          try {
            const { userAPI } = await import('../services/api')
            const userInfo = await userAPI.getCurrentUser()
            const updatedUser = { ...parsedUser, id: userInfo.id, email: userInfo.email }
            localStorage.setItem('user', JSON.stringify(updatedUser))
            setUser(updatedUser)
          } catch {
            setUser(parsedUser)
          }
        } else {
          setUser(parsedUser)
        }
      }
      setLoading(false)
    }
    
    loadUser()
  }, [])

  const login = async (username, password) => {
    try {
      const data = await authAPI.login(username, password)
      localStorage.setItem('token', data.access_token)
      
      try {
        const { userAPI } = await import('../services/api')
        const userInfo = await userAPI.getCurrentUser()
        const userData = { id: userInfo.id, username: userInfo.username, email: userInfo.email }
        localStorage.setItem('user', JSON.stringify(userData))
        setUser(userData)
      } catch {
        const userData = { username }
        localStorage.setItem('user', JSON.stringify(userData))
        setUser(userData)
      }
      
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Error logging in',
      }
    }
  }

  const register = async (userData) => {
    try {
      await authAPI.register(userData)
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Error registering',
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}
