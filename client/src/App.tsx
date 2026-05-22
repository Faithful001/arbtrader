import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './domains/auth/context/AuthContext'
import { Toaster } from 'sonner'
import Login from './domains/auth/components/Login'
import Layout from './shared/Layout'
import OpportunityFeed from './domains/arbitrage/components/OpportunityFeed'
import CardDetail from './domains/cards/components/CardDetail'
import MarketListings from './domains/markets/components/MarketListings'
import AlertsDashboard from './domains/alerts/components/AlertsDashboard'
import PortfolioView from './domains/portfolio/components/PortfolioView'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) {
    return <Login />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <Toaster richColors theme="dark" position="top-right" />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<OpportunityFeed />} />
            <Route path="cards/:id" element={<CardDetail />} />
            <Route path="markets" element={<MarketListings />} />
            <Route path="alerts" element={<AlertsDashboard />} />
            <Route path="portfolio" element={<PortfolioView />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

