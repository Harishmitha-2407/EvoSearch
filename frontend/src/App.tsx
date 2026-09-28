import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth, AuthProvider } from './contexts/AuthContext'
import { useTheme, ThemeProvider } from './contexts/ThemeContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DocumentsPage from './pages/Documents'
import DocumentDetail from './pages/DocumentDetail'
import SearchPage from './pages/Search'
import ChatPage from './pages/Chat'
import TimelinePage from './pages/Timeline'
import ComparisonPage from './pages/Comparison'
import KnowledgeMapPage from './pages/KnowledgeMap'
import CodeAnalysisPage from './pages/CodeAnalysis'
import SettingsPage from './pages/Settings'
import LoginPage from './pages/Login'
import SignupPage from './pages/Signup'

function ProtectedRoute({ element }: { element: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) return <div>Loading...</div>
  if (!isAuthenticated) return <Navigate to="/login" />
  
  return <Layout>{element}</Layout>
}

function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-900">
        <div className="text-center">
          <div className="animate-spin text-3xl mb-2 text-blue-600 dark:text-blue-400">⟳</div>
          <p className="text-slate-600 dark:text-slate-400">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" /> : <LoginPage />} />
      <Route path="/signup" element={isAuthenticated ? <Navigate to="/" /> : <SignupPage />} />
      
      <Route path="/" element={<ProtectedRoute element={<Dashboard />} />} />
      <Route path="/documents" element={<ProtectedRoute element={<DocumentsPage />} />} />
      <Route path="/documents/:id" element={<ProtectedRoute element={<DocumentDetail />} />} />
      <Route path="/search" element={<ProtectedRoute element={<SearchPage />} />} />
      <Route path="/chat" element={<ProtectedRoute element={<ChatPage />} />} />
      <Route path="/timeline" element={<ProtectedRoute element={<TimelinePage />} />} />
      <Route path="/comparison" element={<ProtectedRoute element={<ComparisonPage />} />} />
      <Route path="/knowledge-map" element={<ProtectedRoute element={<KnowledgeMapPage />} />} />
      <Route path="/code" element={<ProtectedRoute element={<CodeAnalysisPage />} />} />
      <Route path="/settings" element={<ProtectedRoute element={<SettingsPage />} />} />
    </Routes>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ThemeProvider>
  )
}
