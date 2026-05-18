import { useState } from 'react'
import { Bell, Plus, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

const TRIGGER_LABELS: Record<string, string> = {
  new_opportunity: 'New Opportunity',
  price_drop: 'Price Drop',
  undervalued: 'Undervalued Listing',
  auction_ending: 'Auction Ending Soon',
}

function useMockAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => [
      { id: '1', name: 'High Profit Alerts', trigger_type: 'new_opportunity',
        conditions: { min_profit_gbp: 20, min_roi_percent: 15 },
        delivery_channel: 'telegram', is_active: true },
      { id: '2', name: 'Any Opportunity', trigger_type: 'new_opportunity',
        conditions: { min_profit_gbp: 5 }, delivery_channel: 'telegram', is_active: false },
      { id: '3', name: 'Charizard Price Drop', trigger_type: 'price_drop',
        conditions: { drop_percent: 10 }, delivery_channel: 'telegram', is_active: true },
    ],
  })
}

export default function AlertsDashboard() {
  const { data: seedAlerts = [], isLoading } = useMockAlerts()
  const [alerts, setAlerts] = useState<any[] | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newAlert, setNewAlert] = useState({ name: '', trigger_type: 'new_opportunity', min_profit: 10 })

  const displayed = alerts ?? seedAlerts
  const active = displayed.filter((a: any) => a.is_active).length

  const toggle = (id: string) => setAlerts(displayed.map((a: any) => a.id === id ? { ...a, is_active: !a.is_active } : a))
  const remove = (id: string) => setAlerts(displayed.filter((a: any) => a.id !== id))
  const create = () => {
    if (!newAlert.name.trim()) return
    setAlerts([{ id: String(Date.now()), ...newAlert, conditions: { min_profit_gbp: newAlert.min_profit }, delivery_channel: 'telegram', is_active: true }, ...displayed])
    setShowCreate(false)
    setNewAlert({ name: '', trigger_type: 'new_opportunity', min_profit: 10 })
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Alerts Dashboard</h1>
          <p className="page-subtitle">Telegram notification rules for arbitrage events</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(v => !v)}>
          <Plus size={14} /> New Alert
        </button>
      </div>

      <div className="stat-grid">
        <div className="stat-card"><div className="stat-label">Active Rules</div><div className="stat-value stat-positive">{active}</div></div>
        <div className="stat-card"><div className="stat-label">Total Rules</div><div className="stat-value stat-accent">{displayed.length}</div></div>
        <div className="stat-card"><div className="stat-label">Channel</div><div className="stat-value" style={{ fontSize: 18 }}>Telegram</div><div className="stat-sub">primary delivery</div></div>
      </div>

      {showCreate && (
        <div className="card" style={{ marginBottom: 20, borderColor: 'var(--accent)' }}>
          <div className="card-title" style={{ marginBottom: 16 }}>Create Alert Rule</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <div className="input-group">
              <label className="input-label">Rule Name</label>
              <input className="input" placeholder="e.g. High Profit Alert" value={newAlert.name}
                onChange={e => setNewAlert(p => ({ ...p, name: e.target.value }))} />
            </div>
            <div className="input-group">
              <label className="input-label">Trigger</label>
              <select className="input" value={newAlert.trigger_type}
                onChange={e => setNewAlert(p => ({ ...p, trigger_type: e.target.value }))}>
                {Object.entries(TRIGGER_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div className="input-group">
              <label className="input-label">Min Profit (£)</label>
              <input className="input" type="number" min={0} value={newAlert.min_profit}
                onChange={e => setNewAlert(p => ({ ...p, min_profit: Number(e.target.value) }))} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
            <button className="btn btn-primary" onClick={create}>Create Rule</button>
            <button className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="loading-state"><div className="spinner" /></div>
      ) : displayed.length === 0 ? (
        <div className="empty-state">
          <Bell size={32} style={{ color: 'var(--text-muted)' }} />
          <div className="empty-state-title">No alert rules yet</div>
          <div className="empty-state-sub">Create your first rule to get Telegram notifications</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {displayed.map((a: any) => (
            <div key={a.id} className="alert-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: a.is_active ? 'var(--accent-glow)' : 'var(--bg-overlay)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bell size={15} style={{ color: a.is_active ? 'var(--accent)' : 'var(--text-muted)' }} />
                </div>
                <div>
                  <div className="alert-card-name">{a.name}</div>
                  <div className="alert-card-meta">
                    {TRIGGER_LABELS[a.trigger_type] ?? a.trigger_type}
                    {a.conditions?.min_profit_gbp != null && ` · Min £${a.conditions.min_profit_gbp}`}
                    {' · Telegram'}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className={`badge ${a.is_active ? 'badge-green' : 'badge-muted'}`}>{a.is_active ? 'Active' : 'Paused'}</span>
                <button className="btn btn-ghost btn-sm btn-icon" onClick={() => toggle(a.id)}>
                  {a.is_active ? <ToggleRight size={18} style={{ color: 'var(--green)' }} /> : <ToggleLeft size={18} />}
                </button>
                <button className="btn btn-danger btn-sm btn-icon" onClick={() => remove(a.id)}>
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
