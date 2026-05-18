import { useState } from "react";
import { RefreshCw, TrendingUp, ArrowRight } from "lucide-react";
import { useOpportunities, useRecalculate } from "../hooks/useOpportunities";
import type { Opportunity } from "../types";
import OpportunityCard from "./OpportunityCard";

const SORT_OPTIONS = [
  { value: "net_profit_gbp", label: "Net Profit" },
  { value: "roi_percent", label: "ROI %" },
  { value: "confidence_score", label: "Confidence" },
];

export default function OpportunityFeed() {
  const [sortBy, setSortBy] = useState("net_profit_gbp");
  const [minProfit, setMinProfit] = useState(5);

  const { data, isLoading, isError } = useOpportunities({
    sort_by: sortBy,
    min_profit: minProfit,
    limit: 50,
  });
  const recalc = useRecalculate();

  const items: Opportunity[] = data?.items ?? [];
  const totalProfit = items.reduce((s, o) => s + o.net_profit_gbp, 0);
  const avgConfidence = items.length
    ? (items.reduce((s, o) => s + o.confidence_score, 0) / items.length) * 100
    : 0;
  const avgRoi = items.length ? items.reduce((s, o) => s + o.roi_percent, 0) / items.length : 0;

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Opportunity Feed</h1>
          <p className="page-subtitle">Live arbitrage opportunities — eBay UK vs eBay US</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => recalc.mutate()}
          disabled={recalc.isPending}
        >
          <RefreshCw size={14} className={recalc.isPending ? "spin" : ""} />
          {recalc.isPending ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {/* Summary stats */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Opportunities</div>
          <div className="stat-value stat-accent">{items.length}</div>
          <div className="stat-sub">above £{minProfit} profit</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Feed Profit</div>
          <div className="stat-value stat-positive">£{totalProfit.toFixed(0)}</div>
          <div className="stat-sub">combined net</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg ROI</div>
          <div className="stat-value stat-cyan">{avgRoi.toFixed(1)}%</div>
          <div className="stat-sub">across feed</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Confidence</div>
          <div className="stat-value">{avgConfidence.toFixed(0)}%</div>
          <div className="stat-sub">data quality</div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, alignItems: "center" }}>
        <div style={{ display: "flex", gap: 4 }}>
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              className={`btn btn-sm ${sortBy === opt.value ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setSortBy(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginLeft: "auto" }}>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Min profit</span>
          <select
            className="input"
            style={{ width: 90, padding: "6px 10px" }}
            value={minProfit}
            onChange={(e) => setMinProfit(Number(e.target.value))}
          >
            {[5, 10, 15, 20, 30, 50].map((v) => (
              <option key={v} value={v}>
                £{v}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Feed */}
      {isLoading ? (
        <div className="loading-state">
          <div className="spinner" />
          <span>Fetching opportunities…</span>
        </div>
      ) : isError ? (
        <div className="empty-state">
          <div className="empty-state-icon">⚠️</div>
          <div className="empty-state-title">Failed to load feed</div>
          <div className="empty-state-sub">Check the server connection</div>
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-title">No opportunities found</div>
          <div className="empty-state-sub">
            Try lowering the minimum profit threshold or click Refresh
          </div>
        </div>
      ) : (
        <div className="feed-list">
          {items.map((opp, i) => (
            <div key={opp.id} style={{ animationDelay: `${i * 30}ms` }} className="fade-in">
              <OpportunityCard opportunity={opp} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
