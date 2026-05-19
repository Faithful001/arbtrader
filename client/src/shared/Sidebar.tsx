import { NavLink } from "react-router-dom";
import { TrendingUp, LayoutGrid, Store, Bell, Briefcase, Settings, Zap } from "lucide-react";

const navItems = [
  { to: "/", label: "Live Spreads" },
  { to: "/markets", label: "Listings" },
  { to: "/alerts", label: "Condition Triggers" },
  { to: "/portfolio", label: "Position Book" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div
        style={{
          padding: "0 20px 20px",
          color: "var(--text-bright)",
          fontWeight: 700,
          letterSpacing: "0.05em",
        }}
      >
        ARBTRADER<span className="text-profit">.SYS</span>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">MARKET DATA</div>
        {navItems.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            {label}
          </NavLink>
        ))}

        <div className="nav-section-label" style={{ marginTop: 24 }}>
          SYSTEM
        </div>
        <div className="nav-item" style={{ cursor: "pointer" }}>
          Config & Routing
        </div>
      </nav>

      {/* Footer */}
      <div
        style={{
          marginTop: "auto",
          padding: "20px",
          borderTop: "1px solid var(--border-dim)",
          fontSize: 11,
          fontFamily: "var(--font-mono)",
        }}
      >
        <div style={{ color: "var(--profit)", marginBottom: 4 }}>● LIVE_ENV</div>
        <div style={{ color: "var(--text-muted)" }}>v1.0.0-rc.1</div>
      </div>
    </aside>
  );
}
