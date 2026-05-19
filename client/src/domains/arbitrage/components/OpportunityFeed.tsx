import { useState } from "react";
import { Link } from "react-router-dom";
import { useOpportunities, useRecalculate } from "../hooks/useOpportunities";
import Spinner from "../../../shared/Spinner";
import type { Opportunity } from "../types";

export default function OpportunityFeed() {
  const [minProfit, setMinProfit] = useState(5);

  const { data, isLoading, isError } = useOpportunities({
    sort_by: "net_profit_gbp",
    min_profit: minProfit,
    limit: 50,
  });
  const recalc = useRecalculate();

  const items: Opportunity[] = data?.items ?? [];

  return (
    <div className="main-view">
      {/* Header */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Cross-Market Spreads</h1>
          <p className="view-primary-metric">Live Feed</p>
        </div>
        <div className="control-bar" style={{ marginBottom: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>
              Min Spread
            </span>
            <select
              className="input-dense"
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
          <button
            className="btn-dense btn-action"
            onClick={() => recalc.mutate()}
            disabled={recalc.isPending}
          >
            {recalc.isPending ? "SYNCING..." : "SYNC"}
          </button>
        </div>
      </div>

      <div className="content-pad">
        {/* Feed Table */}
        {isLoading ? (
          <Spinner label="FETCHING MARKET DATA..." />
        ) : isError ? (
          <div style={{ color: "var(--loss)", fontFamily: "var(--font-mono)" }}>
            [ERR: CONNECTION FAILED]
          </div>
        ) : items.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            [NO SPREADS DETECTED ABOVE THRESHOLD]
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>ASSET / SET</th>
                <th>RARITY</th>
                <th className="right">US ASK (EST)</th>
                <th className="right">UK BID (EST)</th>
                <th className="right">CONF. SCORE</th>
                <th className="right">NET SPREAD</th>
                <th className="right">ROI</th>
                <th className="right">ACTION</th>
              </tr>
            </thead>
            <tbody>
              {items.map((opp) => (
                <tr key={opp.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{opp.card_name}</div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {opp.card_id.slice(0, 8)}...
                    </div>
                  </td>
                  <td style={{ color: "var(--text-muted)", fontSize: 12 }}>-</td>
                  <td className="right numeric text-muted">£{opp.buy_price_gbp.toFixed(2)}</td>
                  <td className="right numeric text-muted">£{opp.sell_price_gbp.toFixed(2)}</td>
                  <td className="right numeric">
                    <span
                      style={{
                        color: opp.confidence_score > 0.8 ? "var(--profit)" : "var(--warn)",
                      }}
                    >
                      {(opp.confidence_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="right numeric text-profit text-bright">
                    +£{opp.net_profit_gbp.toFixed(2)}
                  </td>
                  <td className="right numeric text-profit">{opp.roi_percent.toFixed(1)}%</td>
                  <td className="right">
                    <Link to={`/cards/${opp.card_id}`} className="btn-dense">
                      ANALYZE
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
