import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { mangaAPI, favoriteAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { FaBook, FaStar, FaHeart, FaArrowLeft, FaTag } from 'react-icons/fa'
import './MangaDetail.css'

const MangaDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [manga, setManga] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isFavorite, setIsFavorite] = useState(false)
  const [addingFavorite, setAddingFavorite] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadManga()
    if (user) {
      checkFavorite()
    }
  }, [id, user])

  const loadManga = async () => {
    try {
      setLoading(true)
      const data = await mangaAPI.getById(id)
      setManga(data)
      setError('')
    } catch (err) {
      setError('Error loading manga')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const checkFavorite = async () => {
    try {
      const favorites = await favoriteAPI.getAll()
      setIsFavorite(favorites.some((fav) => fav.manga_id === parseInt(id)))
    } catch (err) {
      console.error('Error checking favorite', err)
    }
  }

  const handleAddFavorite = async () => {
    if (!user) {
      navigate('/login')
      return
    }

    try {
      setAddingFavorite(true)
      setError('')
      await favoriteAPI.add(parseInt(id))
      setIsFavorite(true)
      setTimeout(() => setError(''), 2000)
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Error adding to favorites'
      if (errorMsg.includes('already') || errorMsg.includes('favoritos')) {
        setIsFavorite(true)
      } else {
        setError(errorMsg)
      }
      console.error(err)
    } finally {
      setAddingFavorite(false)
    }
  }

  if (loading) {
    return (
        <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  if (error && !manga) {
    return (
      <div className="error-container">
        <p>{error}</p>
        <Link to="/mangas" className="btn-back">
          <FaArrowLeft />
          <span>Back</span>
        </Link>
      </div>
    )
  }

  if (!manga) return null

  return (
    <div className="manga-detail">
      <Link to="/mangas" className="btn-back">
        <FaArrowLeft />
        <span>Back</span>
      </Link>

      <div className="manga-detail-content">
        <div className="manga-detail-cover">
          {manga.cover ? (
            <img src={manga.cover} alt={manga.title} />
          ) : (
            <div className="manga-placeholder-large">
              <FaBook size={80} />
            </div>
          )}
        </div>

        <div className="manga-detail-info">
          <h1>{manga.title}</h1>

          <div className="manga-meta">
            {manga.rating && (
              <div className="manga-rating-large">
                <FaStar />
                <span>{manga.rating.toFixed(1)}</span>
              </div>
            )}
            {manga.year && (
              <div className="manga-year-large">
                <span>{manga.year}</span>
              </div>
            )}
          </div>

          {user && (
            <>
              <button
                onClick={handleAddFavorite}
                className={`btn-favorite ${isFavorite ? 'active' : ''}`}
                disabled={addingFavorite || isFavorite}
              >
                <FaHeart />
                <span>
                  {isFavorite
                    ? 'In Favorites'
                    : addingFavorite
                    ? 'Adding...'
                    : 'Add to Favorites'}
                </span>
              </button>
              {error && !error.includes('already') && !error.includes('favoritos') && (
                <div className="error-message" style={{ marginTop: '1rem', color: 'var(--error)' }}>
                  {error}
                </div>
              )}
            </>
          )}

          {manga.description && (
            <div className="manga-description-full">
              <h3>Synopsis</h3>
              <p>{manga.description}</p>
            </div>
          )}

          {manga.tags && manga.tags.length > 0 && (
            <div className="manga-tags-full">
              <h3>
                <FaTag />
                <span>Tags</span>
              </h3>
              <div className="tags-container">
                {manga.tags.map((tag, idx) => (
                  <span key={idx} className="tag-large">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MangaDetail
