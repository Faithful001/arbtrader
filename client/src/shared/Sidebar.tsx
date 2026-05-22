import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  TrendingUp,
  LayoutGrid,
  Store,
  Bell,
  Briefcase,
  Settings,
  Zap,
  LogOut,
} from "lucide-react";
import { useAuth } from "../domains/auth/context/AuthContext";

const navItems = [
  { to: "/", label: "Live Spreads", icon: TrendingUp },
  { to: "/markets", label: "Listings", icon: Store },
  { to: "/alerts", label: "Condition Triggers", icon: Bell },
  { to: "/portfolio", label: "Position Book", icon: Briefcase },
];

export default function Sidebar() {
  const { logout, email } = useAuth();
  const [showConfirm, setShowConfirm] = useState(false);

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
        ARBTRADER
      </div>

      {/* Nav */}
      <nav className="sidebar-nav flex flex-col gap-y-2">
        <div className="nav-section-label mb-2">MARKET DATA</div>
        <div className="flex flex-col gap-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => `nav-item mt-2 ${isActive ? " active" : ""}`}
            >
              <div className="flex items-center gap-x-2">
                <Icon size={14} style={{ flexShrink: 0 }} />
                {label}
              </div>
            </NavLink>
          ))}
        </div>

        {/* <div className="nav-section-label" style={{ marginTop: 24 }}>
          SYSTEM
        </div>
        <div className="nav-item" style={{ cursor: "pointer" }}>
          Config & Routing
        </div> */}
      </nav>

      {/* Footer */}
      <div
        style={{
          marginTop: "auto",
          padding: "16px 20px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        <button
          onClick={() => setShowConfirm(true)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "none",
            border: "none",
            color: "var(--text-muted)",
            cursor: "pointer",
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            padding: 0,
            width: "100%",
            transition: "color 0.1s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "var(--text-bright)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "var(--text-muted)";
          }}
        >
          <LogOut size={14} />
          <span>LOGOUT</span>
        </button>
        <div
          style={{
            marginTop: "auto",
            padding: "16px 20px",
            borderTop: "1px solid var(--border-dim)",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          {email && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                paddingBottom: "8px",
                // borderBottom: "1px solid var(--border-dim)",
              }}
            >
              {/* Initial Circle */}
              <div
                style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "50%",
                  background: "var(--border-focus)",
                  color: "var(--text-bright)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 600,
                  fontSize: "13px",
                  fontFamily: "var(--font-mono)",
                  textTransform: "uppercase",
                }}
              >
                {email.charAt(0)}
              </div>

              {/* Email Text */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  overflow: "hidden",
                }}
              >
                <span
                  style={{
                    color: "var(--text-bright)",
                    fontSize: "12px",
                    fontWeight: 500,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    maxWidth: "140px",
                  }}
                  title={email}
                >
                  {email}
                </span>
                <span
                  style={{
                    fontSize: "10px",
                    color: "var(--text-muted)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  OPERATOR
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            backdropFilter: "blur(4px)",
          }}
        >
          <div
            style={{
              background: "var(--bg-panel)",
              border: "1px solid var(--border-focus)",
              padding: "24px",
              borderRadius: "4px",
              width: "90%",
              maxWidth: "360px",
              fontFamily: "var(--font-mono)",
              textAlign: "center",
            }}
          >
            <h3
              style={{
                color: "var(--text-bright)",
                fontSize: "14px",
                marginBottom: "12px",
                fontWeight: 600,
                letterSpacing: "0.05em",
              }}
            >
              CONFIRM LOGOUT
            </h3>
            <p style={{ color: "var(--text-muted)", fontSize: "12px", marginBottom: "24px" }}>
              Are you sure you want to logout?
            </p>
            <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
              <button
                onClick={() => {
                  setShowConfirm(false);
                  logout();
                }}
                style={{
                  background: "var(--loss)",
                  color: "#fff",
                  border: "none",
                  padding: "8px 16px",
                  fontSize: "12px",
                  fontFamily: "var(--font-mono)",
                  cursor: "pointer",
                  fontWeight: 600,
                  borderRadius: "2px",
                }}
              >
                YES, LOGOUT
              </button>
              <button
                onClick={() => setShowConfirm(false)}
                style={{
                  background: "var(--border-dim)",
                  color: "var(--text-main)",
                  border: "1px solid var(--border-focus)",
                  padding: "8px 16px",
                  fontSize: "12px",
                  fontFamily: "var(--font-mono)",
                  cursor: "pointer",
                  borderRadius: "2px",
                }}
              >
                CANCEL
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
