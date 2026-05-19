import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

import { portfolioApi } from '../api/portfolio.api'
import Spinner from '../../../shared/Spinner'

function usePortfolio() {
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: async () => {
      const [holdings, pnl] = await Promise.all([
        portfolioApi.getHoldings(),
        portfolioApi.getPnl(),
      ])
      return { holdings, pnl_history: pnl?.history ?? [] }
    },
  })
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-focus)', padding: '8px', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ color: 'var(--text-bright)' }}>£{payload[0].value.toFixed(2)}</div>
    </div>
  )
}

export default function PortfolioView() {
  const { data, isLoading, refetch } = usePortfolio()

  const displayed = data?.holdings ?? []
  const history = data?.pnl_history ?? []

  const totalInvested = displayed.reduce((s: number, h: any) => s + h.buy_price_gbp * h.quantity, 0)
  const currentValue = displayed.reduce((s: number, h: any) => s + (h.current_value_gbp ?? h.buy_price_gbp) * h.quantity, 0)
  const totalPnl = currentValue - totalInvested
  const roi = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0

  const removeHolding = async (id: string) => {
    try {
      await portfolioApi.removeHolding(id)
      refetch()
    } catch (error) {
      console.error('Failed to remove holding', error)
    }
  }

  return (
    <div className="main-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">POSITION BOOK</h1>
          <p className="view-primary-metric">Portfolio Summary</p>
        </div>
        <div style={{ display: 'flex', gap: 32, alignItems: 'center' }}>
           <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, textAlign: 'right' }}>CAPITAL ALLOCATED</div>
              <div className="mono text-bright text-lg">£{totalInvested.toFixed(2)}</div>
           </div>
           <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, textAlign: 'right' }}>NOTIONAL VALUE</div>
              <div className="mono text-bright text-lg">£{currentValue.toFixed(2)}</div>
           </div>
           <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, textAlign: 'right' }}>NET PNL / ROI</div>
              <div className={`mono text-lg ${totalPnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                {totalPnl >= 0 ? '+' : ''}£{totalPnl.toFixed(2)} ({roi >= 0 ? '+' : ''}{roi.toFixed(1)}%)
              </div>
           </div>
        </div>
      </div>

      <div className="content-pad">
        {isLoading ? (
          <Spinner label="LOADING PORTFOLIO DATA..." />
        ) : (
          <div className="grid-asymmetric">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="panel">
                <div className="view-title" style={{ marginBottom: 16 }}>OPEN POSITIONS</div>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ASSET IDENTIFIER</th>
                      <th>VENUE</th>
                      <th className="right">ENTRY PX</th>
                      <th className="right">MARK PTM</th>
                      <th className="right">UNREALIZED</th>
                      <th className="right">ROI</th>
                      <th className="right">ACTION</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayed.map((h: any) => {
                      const pnl = (h.current_value_gbp - h.buy_price_gbp) * h.quantity
                      const r = ((h.current_value_gbp - h.buy_price_gbp) / h.buy_price_gbp) * 100
                      return (
                        <tr key={h.id}>
                          <td>
                            <div style={{ fontWeight: 500 }}>{h.card_name}</div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{h.condition.toUpperCase()} · BOUGHT {h.buy_date}</div>
                          </td>
                          <td className="mono">{h.market.toUpperCase()}</td>
                          <td className="right mono text-muted">£{h.buy_price_gbp.toFixed(2)}</td>
                          <td className="right mono text-bright">£{h.current_value_gbp.toFixed(2)}</td>
                          <td className={`right mono ${pnl >= 0 ? 'text-profit text-bright' : 'text-loss'}`}>
                            {pnl >= 0 ? '+' : ''}£{pnl.toFixed(2)}
                          </td>
                          <td className={`right mono ${r >= 0 ? 'text-profit' : 'text-loss'}`}>
                            {r >= 0 ? '+' : ''}{r.toFixed(1)}%
                          </td>
                          <td className="right">
                            <button className="btn-dense" style={{ color: 'var(--loss)' }} onClick={() => removeHolding(h.id)}>
                              LIQ
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="panel">
                <div className="view-title" style={{ marginBottom: 16 }}>30-DAY VALUATION CURVE</div>
                <div style={{ height: 240 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={history} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="1 3" stroke="var(--border-dim)" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} interval={4} />
                      <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} tickFormatter={v => `£${v}`} orientation="right" />
                      <Tooltip content={<CustomTooltip />} />
                      <Area type="stepAfter" dataKey="value" stroke="var(--text-main)" strokeWidth={1.5} fill="var(--bg-hover)" dot={false} isAnimationActive={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
