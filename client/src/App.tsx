import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './shared/Layout'
import OpportunityFeed from './domains/arbitrage/components/OpportunityFeed'
import CardDetail from './domains/cards/components/CardDetail'
import MarketListings from './domains/markets/components/MarketListings'
import AlertsDashboard from './domains/alerts/components/AlertsDashboard'
import PortfolioView from './domains/portfolio/components/PortfolioView'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<OpportunityFeed />} />
          <Route path="cards/:id" element={<CardDetail />} />
          <Route path="markets" element={<MarketListings />} />
          <Route path="alerts" element={<AlertsDashboard />} />
          <Route path="portfolio" element={<PortfolioView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
