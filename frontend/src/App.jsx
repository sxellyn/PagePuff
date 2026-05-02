import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Header from './components/Header'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Mangas from './pages/Mangas'
import MangaDetail from './pages/MangaDetail'
import Favorites from './pages/Favorites'
import Recommendations from './pages/Recommendations'
import Profile from './pages/Profile'
import './App.css'

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Header />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/mangas" element={<Mangas />} />
              <Route path="/mangas/:id" element={<MangaDetail />} />
              <Route path="/favorites" element={<Favorites />} />
              <Route path="/recommendations" element={<Recommendations />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App
