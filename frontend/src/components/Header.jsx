import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getAvatarUrl } from '../services/api'
import { FaBook, FaHeart, FaSignInAlt, FaSignOutAlt, FaUserPlus, FaStar, FaUser } from 'react-icons/fa'
import './Header.css'

const Header = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          <FaBook className="logo-icon" />
          <span>PagePuff</span>
        </Link>

        <nav className="nav">
          <Link to="/mangas" className="nav-link">
            <FaBook />
            <span>Mangas</span>
          </Link>
          
          {user ? (
            <>
              <Link to="/favorites" className="nav-link">
                <FaHeart />
                <span>Favorites</span>
              </Link>
              <Link to="/recommendations" className="nav-link">
                <FaStar />
                <span>Recommendations</span>
              </Link>
              <div className="user-menu">
                <Link to="/profile" className="btn-profile">
                  {user.has_avatar && user.id ? (
                    <img
                      src={getAvatarUrl(user.id, user.avatar_cache_key)}
                      alt=""
                      className="btn-profile-avatar"
                    />
                  ) : (
                    <FaUser />
                  )}
                  <span>Hello, {user.username}!</span>
                </Link>
                <button type="button" onClick={handleLogout} className="btn-logout">
                  <FaSignOutAlt />
                  <span>Logout</span>
                </button>
              </div>
            </>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="btn-login">
                <FaSignInAlt />
                <span>Login</span>
              </Link>
              <Link to="/register" className="btn-register">
                <FaUserPlus />
                <span>Sign Up</span>
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  )
}

export default Header
