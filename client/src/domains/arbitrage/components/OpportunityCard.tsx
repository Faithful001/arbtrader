import { ArrowRight, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Opportunity } from '../types'

interface Props { opportunity: Opportunity }

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 80 ? 'var(--green)' : pct >= 60 ? 'var(--yellow)' : 'var(--red)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div className="confidence-bar">
        <div className="confidence-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', minWidth: 30 }}>
        {pct}%
      </span>
    </div>
  )
}

export default function OpportunityCard({ opportunity: o }: Props) {
  const navigate = useNavigate()
  const profitColor = o.net_profit_gbp >= 20 ? 'var(--green)' : o.net_profit_gbp >= 10 ? 'var(--cyan)' : 'var(--yellow)'

  return (
    <div className="opp-card" onClick={() => navigate(`/cards/${o.card_id}`)}>
      {/* Card image */}
      <img
        className="opp-card-img"
        src={o.card_image_url || `https://via.placeholder.com/48x48/161b25/6c63ff?text=?`}
        alt={o.card_name}
        onError={(e) => {
          (e.target as HTMLImageElement).src = `https://placehold.co/48x48/161b25/6c63ff?text=TC`
        }}
      />

      {/* Info */}
      <div className="opp-card-info">
        <div className="opp-card-name">{o.card_name || 'Unknown Card'}</div>
        <div className="opp-card-route">
          <span style={{ color: 'var(--text-secondary)' }}>{o.buy_market_name || 'eBay US'}</span>
          <ArrowRight size={10} />
          <span style={{ color: 'var(--text-secondary)' }}>{o.sell_market_name || 'eBay UK'}</span>
          {o.data_points_used && (
            <span style={{ marginLeft: 8, color: 'var(--text-muted)' }}>
              · {o.data_points_used} sales
            </span>
          )}
        </div>
      </div>

      {/* Profit */}
      <div className="opp-card-profit">
        <div className="opp-profit-value" style={{ color: profitColor }}>
          £{o.net_profit_gbp.toFixed(2)}
        </div>
        <div className="opp-roi">{o.roi_percent.toFixed(1)}% ROI</div>
      </div>

      {/* Meta: confidence + badge */}
      <div className="opp-card-meta">
        <ConfidenceBar score={o.confidence_score} />
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span className={`badge ${o.net_profit_gbp >= 20 ? 'badge-green' : o.net_profit_gbp >= 10 ? 'badge-cyan' : 'badge-yellow'}`}>
            {o.net_profit_gbp >= 20 ? '🔥 Hot' : o.net_profit_gbp >= 10 ? '📈 Good' : '💡 Mild'}
          </span>
          <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />
        </div>
      </div>
    </div>
  )
}
