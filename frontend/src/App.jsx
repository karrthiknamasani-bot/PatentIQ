import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import { GoogleOAuthProvider } from '@react-oauth/google'
import ProtectedRoute from './components/ProtectedRoute'
import { Toaster } from 'react-hot-toast'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import AnalysisPage from './pages/AnalysisPage'
import DashboardPage from './pages/DashboardPage'
import SearchPage from './pages/SearchPage'
import LibraryPage from './pages/LibraryPage'
import ReportsPage from './pages/ReportsPage'
import UploadPage from './pages/UploadPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import VerifyOTPPage from './pages/VerifyOTPPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  if (!clientId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 text-center p-4">
        <div className="bg-white p-8 rounded-xl shadow-sm border border-red-200 max-w-md">
          <h2 className="text-xl font-bold text-red-600 mb-2">Configuration Error</h2>
          <p className="text-gray-700">Missing VITE_GOOGLE_CLIENT_ID in frontend/.env</p>
        </div>
      </div>
    );
  }

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Toaster position="top-right" toastOptions={{ className: 'dark:bg-gray-800 dark:text-white' }} />
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/verify-otp" element={<VerifyOTPPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              
              {/* Protected Routes */}
              <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
              <Route path="/upload" element={<ProtectedRoute><UploadPage /></ProtectedRoute>} />
              <Route path="/analysis" element={<ProtectedRoute><AnalysisPage /></ProtectedRoute>} />
              <Route path="/search" element={<ProtectedRoute><SearchPage /></ProtectedRoute>} />
              <Route path="/library" element={<ProtectedRoute><LibraryPage /></ProtectedRoute>} />
              <Route path="/reports" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </GoogleOAuthProvider>
  )
}

export default App
