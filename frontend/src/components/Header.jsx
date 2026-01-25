import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { FaBook, FaHeart, FaSignInAlt, FaSignOutAlt, FaUserPlus, FaStar } from 'react-icons/fa'
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
                <span className="username">Hello, {user.username}!</span>
                <button onClick={handleLogout} className="btn-logout">
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
