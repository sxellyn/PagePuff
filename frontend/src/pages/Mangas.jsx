import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { mangaAPI, favoriteAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { FaBook, FaStar, FaSearch, FaHeart } from 'react-icons/fa'
import './Mangas.css'

const Mangas = () => {
  const { user } = useAuth()
  const [mangas, setMangas] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [error, setError] = useState('')
  const [favorites, setFavorites] = useState([])
  const [addingFavorites, setAddingFavorites] = useState({})
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(20)
  const [totalPages, setTotalPages] = useState(1)
  const [totalMangas, setTotalMangas] = useState(0)
  const [allMangas, setAllMangas] = useState([])
  const [useBackendPagination, setUseBackendPagination] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState('')
  const [categories, setCategories] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [savedPagination, setSavedPagination] = useState({ page: 1, limit: 20 })

  const loadFavorites = useCallback(async () => {
    try {
      const favs = await favoriteAPI.getAll()
      setFavorites(favs)
    } catch (err) {
      console.error('Error loading favorites', err)
    }
  }, [])

  const loadCategories = useCallback(async () => {
    try {
      const data = await mangaAPI.getCategories()
      if (data && data.categories && Array.isArray(data.categories)) {
        setCategories(data.categories)
      }
    } catch (err) {
      console.error('Error loading categories', err)
    }
  }, [])

  const loadMangas = async (page = currentPage, limit = itemsPerPage, category = selectedCategory, search = null) => {
    try {
      setLoading(true)
      setError('')
      const data = await mangaAPI.getAll(page, limit, category || null, search || null)
      
      if (data && data.items && Array.isArray(data.items)) {
        setMangas(data.items)
        setTotalPages(data.total_pages || 1)
        setTotalMangas(data.total || 0)
        setAllMangas([])
        setUseBackendPagination(true)
      } 
      else if (Array.isArray(data)) {
        const total = data.length
        setTotalMangas(total)
        setTotalPages(Math.ceil(total / limit) || 1)
        setAllMangas(data)
        setUseBackendPagination(false)
        
        const startIndex = (page - 1) * limit
        const endIndex = startIndex + limit
        const paginatedData = data.slice(startIndex, endIndex)
        
        setMangas(paginatedData)
      } 
      else {
        setError('Invalid API response format')
        console.error('Response is not in expected format:', data)
        console.error('Expected: { items: [], total: number, page: number, limit: number, total_pages: number } or array')
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Error loading mangas'
      setError(`Error loading mangas: ${errorMessage}`)
      console.error('Full error:', err)
      console.error('Error response:', err.response?.data)
      
      if (err.code === 'ECONNREFUSED' || err.message.includes('Network Error')) {
        setError('Error: Could not connect to server. To start the backend, run: cd backend && docker-compose up -d')
      } else if (err.response?.status === 404) {
        setError('Error: Endpoint not found. Check if manga service is running.')
      } else if (err.response?.status === 500) {
        setError('Server error. Check backend logs.')
      } else if (err.response?.status === 422) {
        setError('Validation error. The backend might not support pagination yet. Try restarting the manga service.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCategories()
  }, [loadCategories])

  useEffect(() => {
    if (useBackendPagination) {
      loadMangas(1, 20, selectedCategory)
    }
  }, [])

  const handleSearch = useCallback(() => {
    if (searchTerm.trim()) {
      if (!isSearching) {
        setSavedPagination({ page: currentPage, limit: itemsPerPage })
        setIsSearching(true)
      }
      loadMangas(1, 100, selectedCategory, searchTerm.trim())
    } else {
      if (isSearching) {
        setIsSearching(false)
        setCurrentPage(savedPagination.page)
        setItemsPerPage(savedPagination.limit)
      }
    }
  }, [searchTerm, isSearching, currentPage, itemsPerPage, selectedCategory, savedPagination, loadMangas])

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSearch()
    }
  }

  useEffect(() => {
    if (isSearching) {
      return
    }

    if (!useBackendPagination && allMangas.length > 0 && !selectedCategory) {
      const startIndex = (currentPage - 1) * itemsPerPage
      const endIndex = startIndex + itemsPerPage
      const paginatedData = allMangas.slice(startIndex, endIndex)
      setMangas(paginatedData)
      setTotalPages(Math.ceil(allMangas.length / itemsPerPage) || 1)
    } else if (useBackendPagination) {
      loadMangas(currentPage, itemsPerPage, selectedCategory)
    }
  }, [currentPage, itemsPerPage, selectedCategory, isSearching])

  useEffect(() => {
    if (user) {
      loadFavorites()
    }
  }, [user, loadFavorites])

  const handleAddFavorite = useCallback(async (e, mangaId) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!user) {
      return
    }

    try {
      setAddingFavorites(prev => ({ ...prev, [mangaId]: true }))
      await favoriteAPI.add(mangaId)
      await loadFavorites()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Error adding to favorites'
      if (!errorMsg.includes('already') && !errorMsg.includes('favoritos')) {
        console.error('Error adding favorite', err)
      }
    } finally {
      setAddingFavorites(prev => ({ ...prev, [mangaId]: false }))
    }
  }, [user, loadFavorites])

  const favoritesSet = useMemo(() => {
    return new Set(favorites.map(fav => fav.manga_id))
  }, [favorites])

  const isFavorite = useCallback((mangaId) => {
    return favoritesSet.has(mangaId)
  }, [favoritesSet])

  const displayedMangas = mangas

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const handleItemsPerPageChange = (newLimit) => {
    setItemsPerPage(newLimit)
    setCurrentPage(1)
    if (!useBackendPagination && allMangas.length > 0) {
      setTotalPages(Math.ceil(allMangas.length / newLimit) || 1)
    }
  }

  const handleCategoryChange = (category) => {
    setSelectedCategory(category)
    setCurrentPage(1)
  }

  return (
    <div className="mangas-page">
      <div className="page-header">
        <h1>
          <FaBook />
          <span>Manga Library</span>
        </h1>
        <div className="search-filters">
          <div className="search-box">
            <FaSearch className="search-icon" />
            <input
              type="text"
              placeholder="Search mangas... (Press Enter to search)"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleSearchKeyDown}
            />
          </div>
          <div className="category-filter">
            <label>Category:</label>
            <select
              value={selectedCategory}
              onChange={(e) => handleCategoryChange(e.target.value)}
              className="category-select"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <p>{error}</p>
          {(error.includes('connect') || error.includes('Network Error') || error.includes('ECONNREFUSED')) && (
            <div style={{ fontSize: '0.9rem', marginTop: '0.5rem', opacity: 0.9 }}>
              <p><strong>To start the backend:</strong></p>
              <ol style={{ marginLeft: '1.5rem', marginTop: '0.5rem' }}>
                <li>Open a terminal in the project folder</li>
                <li>Run: <code style={{ background: 'rgba(0,0,0,0.3)', padding: '0.2rem 0.4rem', borderRadius: '3px' }}>cd backend</code></li>
                <li>Run: <code style={{ background: 'rgba(0,0,0,0.3)', padding: '0.2rem 0.4rem', borderRadius: '3px' }}>docker-compose up -d</code></li>
                <li>Wait a few seconds for the services to start</li>
              </ol>
            </div>
          )}
        </div>
      )}

      {loading && displayedMangas.length === 0 ? (
        <div className="loading-container" style={{ minHeight: '400px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div className="loading-spinner"></div>
        </div>
      ) : !error && displayedMangas.length === 0 && !loading ? (
        <div className="empty-state">
          {searchTerm ? (
            <>
              <FaSearch size={64} />
              <p>No mangas found for "{searchTerm}"</p>
              <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
                Try searching with different terms.
              </p>
            </>
          ) : (
            <>
              <FaBook size={64} />
              <p>No mangas found</p>
            </>
          )}
        </div>
      ) : (
        <>
          {!isSearching && !loading && (
            <div className="pagination-controls-top">
              <div className="items-per-page-selector">
                <label>Items per page:</label>
                <select 
                  value={itemsPerPage} 
                  onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
                  className="items-per-page-select"
                >
                  <option value={20}>20</option>
                  <option value={40}>40</option>
                  <option value={60}>60</option>
                  <option value={80}>80</option>
                  <option value={100}>100</option>
                </select>
              </div>
              <div className="pagination-info">
                Showing {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, totalMangas)} of {totalMangas} mangas
              </div>
            </div>
          )}
          {isSearching && displayedMangas.length > 0 && !loading && (
            <div className="pagination-controls-top">
              <div className="pagination-info">
                Found {displayedMangas.length} manga{displayedMangas.length !== 1 ? 's' : ''} for "{searchTerm}"
              </div>
            </div>
          )}
          <div style={{ position: 'relative' }}>
            {loading && displayedMangas.length > 0 && (
              <div style={{ 
                position: 'absolute', 
                top: '2rem', 
                left: '50%', 
                transform: 'translateX(-50%)',
                zIndex: 10,
                pointerEvents: 'none',
                width: '100%',
                display: 'flex',
                justifyContent: 'center'
              }}>
                <div className="loading-spinner" style={{ margin: 0 }}></div>
              </div>
            )}
            <div style={{ opacity: loading && displayedMangas.length > 0 ? 0.5 : 1, pointerEvents: loading && displayedMangas.length > 0 ? 'none' : 'auto' }}>
              <div className="mangas-grid">
                {displayedMangas.map((manga) => {
                  const favorite = isFavorite(manga.id)
                  const adding = addingFavorites[manga.id]
                  
                  return (
                    <div key={manga.id} className="manga-card-wrapper">
                      <Link
                        to={`/mangas/${manga.id}`}
                        className="manga-card"
                      >
                        <div className="manga-cover">
                          {manga.cover ? (
                            <img src={manga.cover} alt={manga.title} />
                          ) : (
                            <div className="manga-placeholder">
                              <FaBook size={48} />
                            </div>
                          )}
                        </div>
                        <div className="manga-info">
                          <h3>{manga.title}</h3>
                          {manga.rating && (
                            <div className="manga-rating">
                              <FaStar />
                              <span>{manga.rating.toFixed(1)}</span>
                            </div>
                          )}
                          {manga.year && <p className="manga-year">{manga.year}</p>}
                          {manga.description && (
                            <p className="manga-description">
                              {manga.description.length > 100
                                ? `${manga.description.substring(0, 100)}...`
                                : manga.description}
                            </p>
                          )}
                          {manga.tags && manga.tags.length > 0 && (
                            <div className="manga-tags">
                              {manga.tags.slice(0, 3).map((tag, idx) => (
                                <span key={idx} className="tag">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </Link>
                      {user && (
                        <button
                          className={`manga-card-favorite-btn ${favorite ? 'active' : ''}`}
                          onClick={(e) => handleAddFavorite(e, manga.id)}
                          disabled={adding || favorite}
                          title={favorite ? 'In favorites' : 'Add to favorites'}
                        >
                          <FaHeart />
                          {adding ? '...' : favorite ? '💖' : ''}
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
          {!isSearching && !searchTerm && totalPages > 1 && !loading && (
            <div className="pagination-controls">
              <button
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              <div className="pagination-numbers">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }
                  return (
                    <button
                      key={pageNum}
                      className={`pagination-number ${currentPage === pageNum ? 'active' : ''}`}
                      onClick={() => handlePageChange(pageNum)}
                    >
                      {pageNum}
                    </button>
                  )
                })}
              </div>
              <button
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Mangas
