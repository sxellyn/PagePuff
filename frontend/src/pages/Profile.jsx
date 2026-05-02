import React, { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { userAPI, favoriteAPI, getAvatarUrl } from '../services/api'
import { FaUser, FaEnvelope, FaHeart, FaBook, FaSignInAlt, FaCamera, FaTrash } from 'react-icons/fa'
import './Profile.css'

const Profile = () => {
  const { user, loading: authLoading, updateUser } = useAuth()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [profile, setProfile] = useState(null)
  const [favoriteCount, setFavoriteCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [avatarBusy, setAvatarBusy] = useState(false)

  useEffect(() => {
    if (authLoading) {
      return
    }
    if (!user) {
      navigate('/login')
      return
    }

    const load = async () => {
      try {
        setLoading(true)
        setError('')
        const info = await userAPI.getCurrentUser()
        setProfile(info)
        updateUser({
          username: info.username,
          email: info.email,
          has_avatar: info.has_avatar === true,
        })
        const favs = await favoriteAPI.getAll()
        setFavoriteCount(Array.isArray(favs) ? favs.length : 0)
      } catch (err) {
        setError(err.response?.data?.detail || 'Could not load profile')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [authLoading, user?.id, navigate, updateUser])

  if (authLoading) {
    return (
      <div className="profile-loading">
        <div className="profile-loading-spinner" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="auth-required profile-auth">
        <FaSignInAlt size={64} />
        <h2>Please login to view your profile</h2>
        <Link to="/login" className="btn-primary">
          Login
        </Link>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="profile-loading">
        <div className="profile-loading-spinner" />
      </div>
    )
  }

  const display = profile || user
  const avatarUid = display.id ?? user?.id
  const avatarSrc =
    display.has_avatar && avatarUid
      ? getAvatarUrl(avatarUid, user?.avatar_cache_key)
      : null

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || !file.type.startsWith('image/')) {
      setError('Choose an image file (JPEG, PNG or WebP).')
      return
    }
    try {
      setAvatarBusy(true)
      setError('')
      await userAPI.uploadAvatar(file)
      const cacheKey = Date.now()
      setProfile((p) => (p ? { ...p, has_avatar: true } : p))
      updateUser({ has_avatar: true, avatar_cache_key: cacheKey })
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not update profile photo')
      console.error(err)
    } finally {
      setAvatarBusy(false)
    }
  }

  const handleRemoveAvatar = async () => {
    try {
      setAvatarBusy(true)
      setError('')
      await userAPI.deleteAvatar()
      setProfile((p) => (p ? { ...p, has_avatar: false } : p))
      updateUser({ has_avatar: false })
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not remove profile photo')
      console.error(err)
    } finally {
      setAvatarBusy(false)
    }
  }

  return (
    <div className="profile-page">
      <div className="page-header">
        <h1>
          <FaUser />
          <span>Your profile</span>
        </h1>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="profile-card">
        <div className="profile-avatar-block">
          <div className="profile-avatar" aria-hidden>
            {avatarSrc ? (
              <img src={avatarSrc} alt="" className="profile-avatar-img" />
            ) : (
              <FaUser />
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="profile-file-input"
            onChange={handleFileChange}
            disabled={avatarBusy}
          />
          <div className="profile-avatar-actions">
            <button
              type="button"
              className="btn-avatar-change"
              disabled={avatarBusy}
              onClick={() => fileInputRef.current?.click()}
            >
              <FaCamera />
              <span>{avatarBusy ? 'Saving…' : 'Change photo'}</span>
            </button>
            {display.has_avatar && (
              <button
                type="button"
                className="btn-avatar-remove"
                disabled={avatarBusy}
                onClick={handleRemoveAvatar}
              >
                <FaTrash />
                <span>Remove</span>
              </button>
            )}
          </div>
          <p className="profile-avatar-hint">JPEG, PNG or WebP. Max practical size ~2&nbsp;MB.</p>
        </div>

        <dl className="profile-fields">
          <div className="profile-row">
            <dt>
              <FaUser className="profile-field-icon" />
              Username
            </dt>
            <dd>{display.username}</dd>
          </div>
          <div className="profile-row">
            <dt>
              <FaEnvelope className="profile-field-icon" />
              Email
            </dt>
            <dd>{display.email || '—'}</dd>
          </div>
          <div className="profile-row">
            <dt>
              <FaHeart className="profile-field-icon" />
              Favorites
            </dt>
            <dd>{favoriteCount}</dd>
          </div>
        </dl>

        <div className="profile-actions">
          <Link to="/favorites" className="btn-profile-secondary">
            <FaHeart />
            <span>My favorites</span>
          </Link>
          <Link to="/mangas" className="btn-profile-primary">
            <FaBook />
            <span>Browse mangas</span>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Profile
