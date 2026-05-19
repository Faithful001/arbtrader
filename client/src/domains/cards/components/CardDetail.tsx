import { useParams, useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { useQuery } from "@tanstack/react-query";

import { cardsApi } from "../api/cards.api";
import Spinner from "../../../shared/Spinner";

function usePriceHistory(cardId: string) {
  return useQuery({
    queryKey: ["price-history", cardId],
    queryFn: async () => {
      return [] as Array<{ date: string; uk: number; us: number }>;
    },
  });
}

function useCard(cardId: string) {
  return useQuery({
    queryKey: ["card", cardId],
    queryFn: () => cardsApi.getCard(cardId),
  });
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "var(--bg-panel)",
        border: "1px solid var(--border-focus)",
        padding: "8px",
        fontSize: 11,
        fontFamily: "var(--font-mono)",
      }}
    >
      <div style={{ color: "var(--text-muted)", marginBottom: 4 }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color }}>
          {p.name === "uk" ? "UK BID" : "US ASK"}: £{p.value.toFixed(2)}
        </div>
      ))}
    </div>
  );
};

export default function CardDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: card, isLoading: cardLoading } = useCard(id!);
  const { data: history } = usePriceHistory(id!);

  if (cardLoading)
    return <Spinner label="LOADING ASSET DATA..." />;

  const ukPrice = history?.[history.length - 1]?.uk ?? 0;
  const usPrice = history?.[history.length - 1]?.us ?? 0;
  const spread = usPrice - ukPrice;
  const fees = usPrice * 0.129;
  const shipping = 12;
  const netProfit = spread - fees - shipping;
  const roi = (netProfit / ukPrice) * 100;

  return (
    <div className="main-view">
      <div className="view-header">
        <div>
          <button className="btn-dense" onClick={() => navigate(-1)} style={{ marginBottom: 12 }}>
            ← BACK TO FEED
          </button>
          <h1 className="view-title">
            {card?.card_set?.name} / #{card?.number}
          </h1>
          <p className="view-primary-metric">{card?.name}</p>
        </div>
        <div>
          <a
            href={`https://www.ebay.co.uk/sch/i.html?_nkw=${encodeURIComponent(card?.name ?? "")}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-dense btn-action"
          >
            OPEN EXTERNAL (EBAY)
          </a>
        </div>
      </div>

      <div className="content-pad">
        <div className="grid-asymmetric">
          {/* Left Column: Ledger & Charts */}
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <div className="panel">
              <div className="view-title" style={{ marginBottom: 16 }}>
                SPREAD ANALYSIS LEDGER
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ITEM</th>
                    <th className="right">VALUE (GBP)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="mono">US ASK (Acquisition)</td>
                    <td className="right numeric text-muted">£{ukPrice.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="mono">UK BID (Target)</td>
                    <td className="right numeric text-muted">£{usPrice.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="mono text-bright">Gross Spread</td>
                    <td className="right numeric text-bright">£{spread.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="mono">Platform Fees (12.9%)</td>
                    <td className="right numeric text-loss">-£{fees.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="mono">Est. Shipping</td>
                    <td className="right numeric text-loss">-£{shipping.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="mono text-profit" style={{ fontWeight: 700, paddingTop: 16 }}>
                      NET SPREAD
                    </td>
                    <td
                      className="right numeric text-profit"
                      style={{ fontWeight: 700, paddingTop: 16, fontSize: 16 }}
                    >
                      £{netProfit.toFixed(2)}
                    </td>
                  </tr>
                  <tr>
                    <td className="mono text-profit" style={{ fontWeight: 700 }}>
                      NET ROI
                    </td>
                    <td
                      className="right numeric text-profit"
                      style={{ fontWeight: 700, fontSize: 16 }}
                    >
                      {roi.toFixed(1)}%
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="panel">
              <div className="view-title" style={{ marginBottom: 16 }}>
                30-DAY PRICE TRENDS
              </div>
              <div style={{ height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                    <CartesianGrid
                      strokeDasharray="1 3"
                      stroke="var(--border-dim)"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v) => `£${v}`}
                      orientation="right"
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Line
                      type="stepAfter"
                      dataKey="uk"
                      stroke="var(--text-bright)"
                      strokeWidth={1.5}
                      dot={false}
                      isAnimationActive={false}
                    />
                    <Line
                      type="stepAfter"
                      dataKey="us"
                      stroke="var(--profit)"
                      strokeWidth={1.5}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Right Column: Asset Metadata */}
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <div className="panel" style={{ padding: 0 }}>
              <img
                src={card?.image_url}
                alt={card?.name}
                style={{
                  width: "100%",
                  display: "block",
                  borderBottom: "1px solid var(--border-dim)",
                }}
                onError={(e) => {
                  (e.target as HTMLImageElement).src =
                    "https://placehold.co/280x390/111216/22252C?text=NO+IMAGE";
                }}
              />
              <div style={{ padding: 16 }}>
                <div className="view-title" style={{ marginBottom: 12 }}>
                  ASSET METADATA
                </div>
                <div className="meta-row">
                  <span className="meta-label">SET IDENTIFIER</span>
                  <span className="meta-value">{card?.card_set?.set_code || "-"}</span>
                </div>
                <div className="meta-row">
                  <span className="meta-label">RELEASE YEAR</span>
                  <span className="meta-value">{card?.card_set?.release_year || "-"}</span>
                </div>
                <div className="meta-row">
                  <span className="meta-label">RARITY GRADE</span>
                  <span className="meta-value">{card?.rarity || "-"}</span>
                </div>
                <div className="meta-row">
                  <span className="meta-label">TYPE / HP</span>
                  <span className="meta-value">
                    {card?.card_type} / {card?.hp}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
