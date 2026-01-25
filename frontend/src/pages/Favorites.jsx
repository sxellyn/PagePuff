import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { favoriteAPI, mangaAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { FaHeart, FaBook, FaSignInAlt } from 'react-icons/fa'
import './Favorites.css'

const Favorites = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [favorites, setFavorites] = useState([])
  const [mangas, setMangas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    loadFavorites()
  }, [user, navigate])

  const loadFavorites = async () => {
    try {
      setLoading(true)
      const favs = await favoriteAPI.getAll()
      setFavorites(favs)

      const mangaIds = favs.map((fav) => fav.manga_id)
      const mangaPromises = mangaIds.map((id) => mangaAPI.getById(id))
      const mangaData = await Promise.all(mangaPromises)
      setMangas(mangaData)
      setError('')
    } catch (err) {
      setError('Error loading favorites')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (!user) {
    return (
      <div className="auth-required">
        <FaSignInAlt size={64} />
        <h2>Please login to view your favorites</h2>
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
    <div className="favorites-page">
      <div className="page-header">
        <h1>
          <FaHeart />
          <span>My Favorites</span>
        </h1>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {mangas.length === 0 ? (
        <div className="empty-state">
          <FaHeart size={64} />
          <h2>No favorites yet</h2>
          <p>Explore the library and add mangas to your favorites!</p>
          <Link to="/mangas" className="btn-primary">
            <FaBook />
            <span>Explore Mangas</span>
          </Link>
        </div>
      ) : (
        <div className="favorites-grid">
          {mangas.map((manga) => (
            <Link
              key={manga.id}
              to={`/mangas/${manga.id}`}
              className="favorite-card"
            >
              <div className="favorite-cover">
                {manga.cover ? (
                  <img src={manga.cover} alt={manga.title} />
                ) : (
                  <div className="manga-placeholder">
                    <FaBook size={48} />
                  </div>
                )}
                <div className="favorite-badge">
                  <FaHeart />
                </div>
              </div>
              <div className="favorite-info">
                <h3>{manga.title}</h3>
                {manga.rating && (
                  <div className="manga-rating">
                    <FaBook />
                    <span>{manga.rating.toFixed(1)}</span>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default Favorites
