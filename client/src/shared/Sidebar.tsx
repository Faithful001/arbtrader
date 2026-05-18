import { NavLink } from 'react-router-dom'
import {
  TrendingUp, LayoutGrid, Store, Bell, Briefcase, Settings, Zap
} from 'lucide-react'

const navItems = [
  { to: '/',          label: 'Opportunity Feed', icon: TrendingUp },
  { to: '/markets',   label: 'Listings',          icon: Store },
  { to: '/alerts',    label: 'Alerts',            icon: Bell },
  { to: '/portfolio', label: 'Portfolio / PnL',   icon: Briefcase },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Zap size={14} />
        </div>
        <span className="sidebar-logo-text">ArbTrader</span>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">Intelligence</div>
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <Icon size={16} className="nav-item-icon" />
            {label}
          </NavLink>
        ))}

        <div className="nav-section-label" style={{ marginTop: 16 }}>System</div>
        <div className="nav-item" style={{ cursor: 'default' }}>
          <Settings size={16} className="nav-item-icon" />
          Settings
        </div>
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="live-badge">
          <span className="live-dot" />
          Mock Mode Active
        </div>
        <div style={{ marginTop: 6, fontSize: 11, color: 'var(--text-muted)' }}>
          v1.0.0 — MVP
        </div>
      </div>
    </aside>
  )
}
