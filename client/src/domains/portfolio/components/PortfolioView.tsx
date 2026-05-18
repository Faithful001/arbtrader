import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Trash2, TrendingUp, TrendingDown } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

function useMockPortfolio() {
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: async () => ({
      holdings: [
        { id: '1', card_name: 'Charizard Base Set Holo', card_image_url: 'https://images.pokemontcg.io/base1/4_hires.png', market: 'eBay US', buy_price_gbp: 72.50, current_value_gbp: 94.00, quantity: 1, condition: 'Near Mint', buy_date: '2026-03-12' },
        { id: '2', card_name: 'Blastoise Base Set Holo', card_image_url: 'https://images.pokemontcg.io/base1/2_hires.png', market: 'eBay US', buy_price_gbp: 48.00, current_value_gbp: 61.50, quantity: 1, condition: 'Raw', buy_date: '2026-04-02' },
        { id: '3', card_name: 'Lugia Neo Genesis', card_image_url: 'https://images.pokemontcg.io/neo1/9_hires.png', market: 'eBay US', buy_price_gbp: 110.00, current_value_gbp: 98.00, quantity: 1, condition: 'Near Mint', buy_date: '2026-04-18' },
        { id: '4', card_name: 'Umbreon Gold Star', card_image_url: 'https://images.pokemontcg.io/ex5/17_hires.png', market: 'eBay UK', buy_price_gbp: 185.00, current_value_gbp: 224.00, quantity: 1, condition: 'PSA 9', buy_date: '2026-02-28' },
      ],
      pnl_history: Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - (29 - i) * 86400000).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' }),
        value: +(400 + i * 4.5 + Math.sin(i * 0.5) * 20 + Math.random() * 15).toFixed(2),
      })),
    }),
  })
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>£{payload[0].value}</div>
    </div>
  )
}

export default function PortfolioView() {
  const { data, isLoading } = useMockPortfolio()
  const [holdings, setHoldings] = useState<any[] | null>(null)

  const displayed = holdings ?? data?.holdings ?? []
  const history = data?.pnl_history ?? []

  const totalInvested = displayed.reduce((s: number, h: any) => s + h.buy_price_gbp * h.quantity, 0)
  const currentValue = displayed.reduce((s: number, h: any) => s + (h.current_value_gbp ?? h.buy_price_gbp) * h.quantity, 0)
  const totalPnl = currentValue - totalInvested
  const roi = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0

  const removeHolding = (id: string) => setHoldings(displayed.filter((h: any) => h.id !== id))

  if (isLoading) return <div className="loading-state"><div className="spinner" /></div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Portfolio / PnL</h1>
          <p className="page-subtitle">Holdings, live valuation, and profit tracking</p>
        </div>
      </div>

      {/* Summary stats */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Total Invested</div>
          <div className="stat-value mono">£{totalInvested.toFixed(2)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Current Value</div>
          <div className="stat-value stat-cyan mono">£{currentValue.toFixed(2)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total PnL</div>
          <div className={`stat-value mono ${totalPnl >= 0 ? 'stat-positive' : 'stat-negative'}`}>
            {totalPnl >= 0 ? '+' : ''}£{totalPnl.toFixed(2)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">ROI</div>
          <div className={`stat-value ${roi >= 0 ? 'stat-positive' : 'stat-negative'}`}>
            {roi >= 0 ? '+' : ''}{roi.toFixed(1)}%
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Holdings</div>
          <div className="stat-value stat-accent">{displayed.length}</div>
          <div className="stat-sub">cards</div>
        </div>
      </div>

      {/* PnL Chart */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <div className="card-title">Portfolio Value (30 days)</div>
          <span className={`badge ${totalPnl >= 0 ? 'badge-green' : 'badge-red'}`}>
            {totalPnl >= 0 ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {roi.toFixed(1)}%
          </span>
        </div>
        <div style={{ height: 180 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
              <defs>
                <linearGradient id="portfolioGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickLine={false} interval={4} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false}
                tickFormatter={v => `£${v}`} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="value" stroke="var(--accent)" strokeWidth={2}
                fill="url(#portfolioGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Holdings table */}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Card</th>
              <th>Market</th>
              <th>Condition</th>
              <th style={{ textAlign: 'right' }}>Bought</th>
              <th style={{ textAlign: 'right' }}>Current</th>
              <th style={{ textAlign: 'right' }}>PnL</th>
              <th style={{ textAlign: 'right' }}>ROI</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {displayed.map((h: any) => {
              const pnl = (h.current_value_gbp - h.buy_price_gbp) * h.quantity
              const r = ((h.current_value_gbp - h.buy_price_gbp) / h.buy_price_gbp) * 100
              return (
                <tr key={h.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <img src={h.card_image_url} alt={h.card_name}
                        style={{ width: 32, height: 32, borderRadius: 4, objectFit: 'cover', background: 'var(--bg-overlay)' }}
                        onError={e => { (e.target as HTMLImageElement).src = 'https://placehold.co/32x32/161b25/6c63ff?text=TC' }}
                      />
                      <span style={{ fontWeight: 500 }}>{h.card_name}</span>
                    </div>
                  </td>
                  <td><span className="badge badge-muted">{h.market}</span></td>
                  <td><span className="badge badge-muted">{h.condition}</span></td>
                  <td style={{ textAlign: 'right' }}><span className="mono">£{h.buy_price_gbp.toFixed(2)}</span></td>
                  <td style={{ textAlign: 'right' }}><span className="mono">£{h.current_value_gbp.toFixed(2)}</span></td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={`mono ${pnl >= 0 ? 'stat-positive' : 'stat-negative'}`}>
                      {pnl >= 0 ? '+' : ''}£{pnl.toFixed(2)}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={`badge ${r >= 0 ? 'badge-green' : 'badge-red'}`}>
                      {r >= 0 ? '+' : ''}{r.toFixed(1)}%
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-danger btn-sm btn-icon" onClick={() => removeHolding(h.id)}>
                      <Trash2 size={12} />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
