import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'

// Mock price history data for demo
function useMockPriceHistory(cardId: string) {
  return useQuery({
    queryKey: ['price-history', cardId],
    queryFn: async () => {
      const now = Date.now()
      const ukData = Array.from({ length: 20 }, (_, i) => ({
        date: new Date(now - (19 - i) * 86400000 * 1.5).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' }),
        uk: +(75 + Math.sin(i * 0.4) * 15 + Math.random() * 10).toFixed(2),
        us: +(88 + Math.sin(i * 0.4) * 18 + Math.random() * 12).toFixed(2),
      }))
      return ukData
    },
  })
}

function useMockCard(cardId: string) {
  return useQuery({
    queryKey: ['card', cardId],
    queryFn: async () => ({
      id: cardId,
      name: 'Charizard Base Set Holo',
      number: '4/102',
      rarity: 'Holo Rare',
      card_type: 'Fire',
      hp: 120,
      image_url: 'https://images.pokemontcg.io/base1/4_hires.png',
      card_set: { name: 'Base Set', release_year: 1999, set_code: 'BS' },
    }),
  })
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg-overlay)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)', padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 6 }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color, fontFamily: 'var(--font-mono)' }}>
          {p.name === 'uk' ? 'eBay UK' : 'eBay US'}: £{p.value}
        </div>
      ))}
    </div>
  )
}

export default function CardDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: card, isLoading: cardLoading } = useMockCard(id!)
  const { data: history } = useMockPriceHistory(id!)

  if (cardLoading) return (
    <div className="loading-state"><div className="spinner" /><span>Loading card…</span></div>
  )

  const ukPrice = history?.[history.length - 1]?.uk ?? 0
  const usPrice = history?.[history.length - 1]?.us ?? 0
  const spread = usPrice - ukPrice
  const fees = usPrice * 0.129
  const shipping = 12
  const netProfit = spread - fees - shipping
  const roi = (netProfit / ukPrice) * 100

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn btn-ghost btn-sm btn-icon" onClick={() => navigate(-1)}>
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1 className="page-title">{card?.name}</h1>
            <p className="page-subtitle">{card?.card_set?.name} · #{card?.number} · {card?.rarity}</p>
          </div>
        </div>
        <a href={`https://www.ebay.co.uk/sch/i.html?_nkw=${encodeURIComponent(card?.name ?? '')}`}
          target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
          <ExternalLink size={13} /> View on eBay
        </a>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20 }}>
        {/* Card image & meta */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <img
              src={card?.image_url}
              alt={card?.name}
              style={{ width: '100%', borderRadius: 'var(--radius-lg)' }}
              onError={(e) => { (e.target as HTMLImageElement).src = 'https://placehold.co/280x390/161b25/6c63ff?text=Card' }}
            />
          </div>
          <div className="card">
            <div className="card-title" style={{ marginBottom: 12 }}>Card Details</div>
            {[
              ['Set', card?.card_set?.name],
              ['Number', card?.number],
              ['Rarity', card?.rarity],
              ['Type', card?.card_type],
              ['HP', card?.hp],
              ['Year', card?.card_set?.release_year],
            ].map(([k, v]) => (
              <div key={String(k)} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                <span>{v ?? '—'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Arbitrage breakdown */}
          <div className="card">
            <div className="card-title" style={{ marginBottom: 16 }}>Arbitrage Breakdown</div>
            <div className="stat-grid" style={{ marginBottom: 0 }}>
              <div className="stat-card">
                <div className="stat-label">Buy (eBay US)</div>
                <div className="stat-value stat-accent">£{ukPrice.toFixed(2)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Sell (eBay UK)</div>
                <div className="stat-value stat-cyan">£{usPrice.toFixed(2)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Net Profit</div>
                <div className={`stat-value ${netProfit > 0 ? 'stat-positive' : 'stat-negative'}`}>
                  £{netProfit.toFixed(2)}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">ROI</div>
                <div className={`stat-value ${roi > 0 ? 'stat-positive' : 'stat-negative'}`}>
                  {roi.toFixed(1)}%
                </div>
              </div>
            </div>
            <div style={{ marginTop: 20 }}>
              <div className="breakdown">
                <span className="breakdown-label">Gross Spread</span>
                <span className="breakdown-value" style={{ color: 'var(--text-primary)' }}>£{spread.toFixed(2)}</span>
                <span className="breakdown-label">Platform Fees (12.9%)</span>
                <span className="breakdown-value" style={{ color: 'var(--red)' }}>-£{fees.toFixed(2)}</span>
                <span className="breakdown-label">International Shipping</span>
                <span className="breakdown-value" style={{ color: 'var(--red)' }}>-£{shipping.toFixed(2)}</span>
                <span className="breakdown-label">Import Duties</span>
                <span className="breakdown-value" style={{ color: 'var(--text-muted)' }}>£0.00</span>
              </div>
              <div className="breakdown" style={{ marginTop: 8 }}>
                <span className="breakdown-label breakdown-total" style={{ fontWeight: 700, color: 'var(--green)', borderBottom: 'none', paddingTop: 8 }}>Net Profit</span>
                <span className="breakdown-value breakdown-total" style={{ fontWeight: 700, color: 'var(--green)', borderBottom: 'none', paddingTop: 8 }}>£{netProfit.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Price history chart */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Price History (30 days)</div>
              <div style={{ display: 'flex', gap: 12, fontSize: 12 }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 12, height: 2, background: 'var(--accent)', display: 'inline-block' }} />
                  eBay UK
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 12, height: 2, background: 'var(--cyan)', display: 'inline-block' }} />
                  eBay US
                </span>
              </div>
            </div>
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false}
                    tickFormatter={(v) => `£${v}`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="uk" stroke="var(--accent)" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="us" stroke="var(--cyan)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
