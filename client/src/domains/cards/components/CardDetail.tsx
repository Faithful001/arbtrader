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
import { useOpportunityByCard } from "../../arbitrage/hooks/useOpportunities";
import { apiClient } from "@/api/client";

import { cardsApi } from "../api/cards.api";
import { marketsApi } from "../../markets/api/markets.api";
import Spinner from "../../../shared/Spinner";

function useMarkets() {
  return useQuery({
    queryKey: ["markets"],
    queryFn: () => marketsApi.getMarkets(),
  });
}

function usePriceHistory(cardId: string) {
  return useQuery({
    queryKey: ["price-history", cardId],
    queryFn: async () => {
      const markets = await marketsApi.getMarkets();
      const ukMarket = markets.find((m: any) => m.region === "UK");
      const usMarket = markets.find((m: any) => m.region === "US");

      const [ukHistory, usHistory] = await Promise.all([
        ukMarket ? cardsApi.getPriceHistory(cardId, ukMarket.id, 30) : Promise.resolve([]),
        usMarket ? cardsApi.getPriceHistory(cardId, usMarket.id, 30) : Promise.resolve([]),
      ]);

      const last3Uk = ukHistory.slice(0, 3);
      const ukAvg = last3Uk.length > 0
        ? last3Uk.reduce((sum: number, h: any) => sum + h.price_gbp, 0) / last3Uk.length
        : 0;

      const dataMap = new Map<string, { date: string; uk: number; us: number }>();

      ukHistory.forEach((h: any) => {
        const date = new Date(h.snapshot_at).toISOString().split("T")[0];
        if (!dataMap.has(date)) dataMap.set(date, { date, uk: 0, us: 0 });
        dataMap.get(date)!.uk = h.price_gbp;
      });

      usHistory.forEach((h: any) => {
        const date = new Date(h.snapshot_at).toISOString().split("T")[0];
        if (!dataMap.has(date)) dataMap.set(date, { date, uk: 0, us: 0 });
        dataMap.get(date)!.us = h.price_gbp;
      });

      const merged = Array.from(dataMap.values()).sort((a, b) => a.date.localeCompare(b.date));

      let lastUk = 0;
      let lastUs = 0;
      merged.forEach((row) => {
        if (row.uk > 0) lastUk = row.uk;
        else row.uk = lastUk;
        if (row.us > 0) lastUs = row.us;
        else row.us = lastUs;
      });

      // Build price distribution data from individual records (sorted by price asc)
      const maxLen = Math.max(ukHistory.length, usHistory.length);
      const ukSorted = [...ukHistory].sort((a: any, b: any) => a.price_gbp - b.price_gbp);
      const usSorted = [...usHistory].sort((a: any, b: any) => a.price_gbp - b.price_gbp);
      const distribution = Array.from({ length: maxLen }, (_, i) => ({
        i: i + 1,
        uk: ukSorted[i]?.price_gbp ?? null,
        us: usSorted[i]?.price_gbp ?? null,
      }));

      return { merged, ukAvg, distribution };
    },
  });
}

function useCard(cardId: string) {
  return useQuery({
    queryKey: ["card", cardId],
    queryFn: () => cardsApi.getCard(cardId),
  });
}

function useCardVariations(cardId: string) {
  return useQuery({
    queryKey: ["card-variations", cardId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/pricing/variations/${cardId}`);
      return data;
    },
    enabled: !!cardId,
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
  const { data: priceData } = usePriceHistory(id!);
  const { data: activeOpportunity } = useOpportunityByCard(id!);
  const { data: variationsData } = useCardVariations(id!);
  const history = priceData?.merged ?? [];
  const ukAvgPrice = priceData?.ukAvg ?? 0;
  const { data: markets } = useMarkets();

  if (cardLoading) return <Spinner label="LOADING ASSET DATA..." />;

  const ukMarket = markets?.find((m: any) => m.region === "UK");

  const buyPrice = activeOpportunity ? activeOpportunity.buy_price_gbp : (history?.[history.length - 1]?.us ?? 0);
  const sellPrice = activeOpportunity ? activeOpportunity.sell_price_gbp : ukAvgPrice;
  const spread = activeOpportunity ? activeOpportunity.gross_spread_gbp : (sellPrice - buyPrice);

  const feePercent = (ukMarket?.fee_percent ?? 12.9) / 100;
  const fees = activeOpportunity ? activeOpportunity.platform_fees_gbp : (sellPrice * feePercent);
  const shipping = activeOpportunity ? activeOpportunity.shipping_cost_gbp : (ukMarket?.shipping_estimate_gbp ?? 3.5);

  const netProfit = activeOpportunity ? activeOpportunity.net_profit_gbp : (spread - fees - shipping);
  const roi = activeOpportunity ? activeOpportunity.roi_percent : (buyPrice > 0 ? (netProfit / buyPrice) * 100 : 0);

  const variations = variationsData?.variations || [];

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
            href={`https://www.ebay.co.uk/sch/i.html?_nkw=${encodeURIComponent(`${card?.name} ${card?.card_set?.name || ""} ${card?.number || ""}`.trim())}`}
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
                    <td className="right numeric text-muted">£{buyPrice.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="mono">UK BID (Target)</td>
                    <td className="right numeric text-muted">£{sellPrice.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="mono text-bright">Gross Spread</td>
                    <td className="right numeric text-bright">£{spread.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="mono">Platform Fees ({(feePercent * 100).toFixed(1)}%)</td>
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
                {new Set(history.map((h: any) => h.date)).size >= 3
                  ? "30-DAY PRICE TRENDS"
                  : "MARKET PRICE DISTRIBUTION"}
              </div>

              {new Set(history.map((h: any) => h.date)).size >= 3 ? (
                <div style={{ height: 240 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={history} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="1 3" stroke="var(--border-dim)" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} tickFormatter={(v) => `£${v}`} orientation="right" />
                      <Tooltip content={<CustomTooltip />} />
                      <Line type="stepAfter" dataKey="uk" stroke="var(--text-bright)" strokeWidth={1.5} dot={false} isAnimationActive={false} />
                      <Line type="stepAfter" dataKey="us" stroke="var(--profit)" strokeWidth={1.5} dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div>
                  <div style={{ height: 200, marginBottom: 10 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={priceData?.distribution ?? []} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="1 3" stroke="var(--border-dim)" vertical={false} />
                        <XAxis dataKey="i" tick={{ fontSize: 10, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} label={{ value: "Listings (price rank)", position: "insideBottom", offset: -2, fontSize: 9, fill: "var(--text-muted)" }} />
                        <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} tickFormatter={(v) => `£${v}`} orientation="right" />
                        <Tooltip content={<CustomTooltip />} />
                        <Line type="monotone" dataKey="uk" stroke="var(--text-bright)" strokeWidth={1.5} dot={{ r: 3, fill: "var(--text-bright)" }} isAnimationActive={false} connectNulls={false} />
                        <Line type="monotone" dataKey="us" stroke="var(--profit)" strokeWidth={1.5} dot={{ r: 3, fill: "var(--profit)" }} isAnimationActive={false} connectNulls={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <div style={{ display: "flex", gap: 16, fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    <span><span style={{ color: "var(--text-bright)" }}>—</span> UK BID (each dot = 1 listing)</span>
                    <span><span style={{ color: "var(--profit)" }}>—</span> US ASK (each dot = 1 listing)</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Asset Metadata */}
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <div className="panel" style={{ padding: 0 }}>
              {card?.image_url && (
                <a
                  href={`https://www.ebay.co.uk/sch/i.html?_nkw=${encodeURIComponent(`${card?.name} ${card?.card_set?.name || ""} ${card?.number || ""}`.trim())}&LH_Complete=1&LH_Sold=1`}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="View last sold on eBay UK"
                  style={{ display: "block" }}
                >
                  <img
                    src={card?.image_url}
                    alt={card?.name}
                    style={{
                      width: "100%",
                      display: "block",
                      borderBottom: "1px solid var(--border-dim)",
                      cursor: "pointer",
                      transition: "opacity 0.15s ease",
                    }}
                    className="hover-opacity"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src =
                        "https://placehold.co/280x390/111216/22252C?text=NO+IMAGE";
                    }}
                  />
                </a>
              )}
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

            {/* Language & Edition Value Variance Panel */}
            {card && (
              <div className="panel" style={{ border: "1px solid var(--border-focus)", background: "var(--bg-panel-dark, #0d0f12)" }}>
                <div className="view-title" style={{ color: "var(--text-bright)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: "#e2b714" }}></span>
                  LANGUAGE & EDITION VARIANCE
                </div>
                
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 16, lineHeight: 1.4 }}>
                  Market values differ drastically by print language and regional set. Our main arbitrage engine operates exclusively on <strong>English</strong> editions to ensure high-fidelity margins.
                </p>

                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {!variationsData ? (
                    <div style={{ color: "var(--text-muted)", fontSize: 11, fontFamily: "var(--font-mono)", textAlign: "center", padding: 24 }}>
                      FETCHING LIVE EBAY VALUE VARIATIONS...
                    </div>
                  ) : (
                    variations.map((v: any) => (
                    <div 
                      key={v.language} 
                      style={{ 
                        border: v.language.includes("English") ? "1px solid var(--profit)" : "1px solid var(--border-dim)",
                        borderRadius: 4, 
                        padding: 12,
                        background: v.language.includes("English") ? "rgba(16, 185, 129, 0.04)" : "transparent"
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                        <span style={{ fontWeight: 700, fontSize: 13, color: v.language.includes("English") ? "var(--profit)" : "var(--text-bright)" }}>
                          {v.language}
                        </span>
                        <span 
                          style={{ 
                            fontSize: 10, 
                            fontWeight: 700, 
                            padding: "2px 6px", 
                            borderRadius: 3, 
                            background: v.status === "Premium" ? "rgba(16, 185, 129, 0.15)" : v.status === "Collector" ? "rgba(59, 130, 246, 0.15)" : "rgba(239, 68, 68, 0.15)",
                            color: v.status === "Premium" ? "var(--profit)" : v.status === "Collector" ? "#3b82f6" : "#ef4444"
                          }}
                        >
                          {v.status.toUpperCase()}
                        </span>
                      </div>
                      
                      <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8, fontFamily: "var(--font-mono)" }}>
                        {v.set}
                      </div>

                      <div style={{ display: "flex", gap: 16, marginBottom: 8 }}>
                        <div>
                          <div style={{ fontSize: 9, color: "var(--text-muted)" }}>US ASK (ACQ)</div>
                          <div style={{ fontSize: 13, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--text-bright)" }}>
                            £{v.usAsk.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: 9, color: "var(--text-muted)" }}>UK BID (TGT)</div>
                          <div style={{ fontSize: 13, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--text-bright)" }}>
                            £{v.ukBid.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: 9, color: "var(--text-muted)" }}>NET SPREAD</div>
                          <div style={{ 
                            fontSize: 13, 
                            fontWeight: 700, 
                            fontFamily: "var(--font-mono)", 
                            color: (v.ukBid - v.usAsk) > 20 ? "var(--profit)" : "var(--text-bright)"
                          }}>
                            +£{(v.ukBid - v.usAsk).toFixed(2)}
                          </div>
                        </div>
                      </div>

                      <div style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.3 }}>
                        {v.notes}
                      </div>
                    </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
