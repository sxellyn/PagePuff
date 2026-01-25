import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { recommendationAPI, mangaAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { FaStar, FaBook, FaSignInAlt } from 'react-icons/fa'
import './Recommendations.css'

const Recommendations = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [stats, setStats] = useState(null)

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    loadRecommendations()
    loadStats()
  }, [user, navigate])

  const loadRecommendations = async () => {
    try {
      setLoading(true)
      setError('')
      
      if (!user.id) {
        const { userAPI } = await import('../services/api')
        const userInfo = await userAPI.getCurrentUser()
        user.id = userInfo.id
      }
      
      const userId = user.id
      
      const data = await recommendationAPI.getRecommendations(userId, 12)
      
      if (data.recommendations && data.recommendations.length > 0) {
        const processedRecs = data.recommendations.map(manga => {
          let tags = manga.tags
          
          if (typeof tags === 'string') {
            try {
              tags = JSON.parse(tags)
            } catch {
              try {
                tags = JSON.parse(tags.replace(/'/g, '"'))
              } catch {
                tags = tags.split(',').map(t => t.trim()).filter(t => t)
              }
            }
          }
          
          if (!Array.isArray(tags)) {
            tags = []
          }
          
          return {
            ...manga,
            tags
          }
        })
        setRecommendations(processedRecs)
      } else {
        setRecommendations([])
        if (data.message) {
          setError(data.message)
        }
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Error loading recommendations'
      setError(errorMsg)
      console.error('Error loading recommendations', err)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const data = await recommendationAPI.getStats()
      setStats(data)
    } catch (err) {
      console.error('Error loading stats', err)
    }
  }

  if (!user) {
    return (
      <div className="auth-required">
        <FaSignInAlt size={64} />
        <h2>Please login to view recommendations</h2>
        <Link to="/login" className="btn-primary">
          Login
        </Link>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  return (
    <div className="recommendations-page">
      <div className="page-header">
        <h1>
          <FaStar />
          <span>Recommendations for You</span>
        </h1>
      </div>

      {stats && (
        <div className="recommendations-stats">
          <p>Based on {stats.users_in_model || 0} users with similar tastes</p>
        </div>
      )}

      {error && !error.includes('Not enough') && (
        <div className="error-banner">{error}</div>
      )}

      {recommendations.length === 0 ? (
        <div className="empty-state">
          <FaStar size={64} />
          <h2>No recommendations yet</h2>
          <p>
            {error.includes('Not enough') 
              ? 'Add more favorites to get personalized recommendations!'
              : 'Explore mangas and add them to your favorites to get recommendations!'}
          </p>
          <Link to="/mangas" className="btn-primary">
            <FaBook />
            <span>Explore Mangas</span>
          </Link>
        </div>
      ) : (
        <>
          <div className="recommendations-intro">
            <p>These mangas are recommended based on users with similar preferences to yours!</p>
          </div>
          <div className="recommendations-grid">
            {recommendations.map((manga) => (
              <Link
                key={manga.id}
                to={`/mangas/${manga.id}`}
                className="recommendation-card"
              >
                <div className="recommendation-cover">
                  {manga.cover ? (
                    <img src={manga.cover} alt={manga.title} />
                  ) : (
                    <div className="manga-placeholder">
                      <FaBook size={48} />
                    </div>
                  )}
                  <div className="recommendation-badge">
                    <FaStar />
                  </div>
                </div>
                <div className="recommendation-info">
                  <h3>{manga.title}</h3>
                  {manga.rating && (
                    <div className="manga-rating">
                      <FaBook />
                      <span>{manga.rating.toFixed(1)}</span>
                    </div>
                  )}
                  {manga.tags && Array.isArray(manga.tags) && manga.tags.length > 0 && (
                    <div className="manga-tags">
                      {manga.tags.slice(0, 3).map((tag, index) => (
                        <span key={index} className="tag">
                          {tag}
                        </span>
                      ))}
                      {manga.tags.length > 3 && (
                        <span className="tag-more">+{manga.tags.length - 3}</span>
                      )}
                    </div>
                  )}
                  {manga.description && (
                    <p className="recommendation-description">
                      {manga.description.length > 80
                        ? `${manga.description.substring(0, 80)}...`
                        : manga.description}
                    </p>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default Recommendations
