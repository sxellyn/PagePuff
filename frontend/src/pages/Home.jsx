import React, { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { FaBook, FaHeart, FaStar } from 'react-icons/fa'
import './Home.css'

const Home = () => {
  const { user, loading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login')
    }
  }, [user, loading, navigate])

  if (loading) {
    return (
      <div className="loading-container" style={{ minHeight: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="loading-spinner"></div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="home">
      <section className="hero">
        <div className="hero-content">
          <div className="logo-container">
            <img src="/logo.png" alt="PagePuff Logo" className="home-logo" />
          </div>
          <h1 className="hero-title">
            Welcome back, <span className="highlight">{user.username}</span>!
          </h1>
          <p className="hero-subtitle">
            Continue exploring your personal manga library!
          </p>
          <div className="hero-buttons">
            <Link to="/mangas" className="btn-primary">
              <FaBook />
              <span>Explore Mangas</span>
            </Link>
            <Link to="/favorites" className="btn-secondary">
              <FaHeart />
              <span>My Favorites</span>
            </Link>
            <Link to="/recommendations" className="btn-secondary">
              <FaStar />
              <span>Recommendations</span>
            </Link>
          </div>
        </div>
      </section>

      <section className="features">
        <h2 className="section-title">Quick Access</h2>
        <div className="features-grid">
          <Link to="/mangas" className="feature-card">
            <div className="feature-icon">
              <FaBook />
            </div>
            <h3>Mangas and Search</h3>
            <p>
              Explore thousands of mangas and manhwas organized by genre, author, and more.
              Find new titles by searching through our extensive collection.
            </p>
          </Link>

          <Link to="/favorites" className="feature-card">
            <div className="feature-icon">
              <FaHeart />
            </div>
            <h3>My Favorites</h3>
            <p>Access your saved favorite mangas quickly and easily.</p>
          </Link>

          <Link to="/recommendations" className="feature-card">
            <div className="feature-icon">
              <FaStar />
            </div>
            <h3>Recommendations</h3>
            <p>Discover personalized suggestions based on your reading habits.</p>
          </Link>
        </div>
      </section>
    </div>
  )
}

export default Home
