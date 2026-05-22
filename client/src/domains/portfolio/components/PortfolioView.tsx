import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

import { portfolioApi } from "../api/portfolio.api";
import { cardsApi } from "../../cards/api/cards.api";
import { marketsApi } from "../../markets/api/markets.api";
import Spinner from "../../../shared/Spinner";

import { toast } from "sonner";

function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: async () => {
      const [holdings, pnl] = await Promise.all([
        portfolioApi.getHoldings(),
        portfolioApi.getPnl(),
      ]);
      return { holdings, pnl_history: pnl?.history ?? [] };
    },
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
      <div style={{ color: "var(--text-bright)" }}>£{payload[0].value.toFixed(2)}</div>
    </div>
  );
};

export default function PortfolioView() {
  const queryClient = useQueryClient();
  const { data, isLoading, refetch } = usePortfolio();
  const [showLogModal, setShowLogModal] = useState(false);

  // Modal form states
  const [selectedCardId, setSelectedCardId] = useState("");
  const [selectedMarketId, setSelectedMarketId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [buyPrice, setBuyPrice] = useState("");
  const [condition, setCondition] = useState("Raw");
  const [buyDate, setBuyDate] = useState(new Date().toISOString().substring(0, 10));
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Queries for the modal
  const { data: cardsList = [] } = useQuery({
    queryKey: ["cards-list"],
    queryFn: () => cardsApi.listCards(),
    enabled: showLogModal,
  });

  const { data: marketsList = [] } = useQuery({
    queryKey: ["markets-list"],
    queryFn: () => marketsApi.getMarkets(),
    enabled: showLogModal,
  });

  const displayed = data?.holdings ?? [];
  const history = data?.pnl_history ?? [];

  const totalInvested = displayed?.reduce(
    (s: number, h: any) => s + (h.buy_price_gbp ?? 0) * (h.quantity ?? 0),
    0
  );
  const currentValue = displayed?.reduce(
    (s: number, h: any) => s + (h.current_value_gbp ?? h.buy_price_gbp) * (h.quantity ?? 0),
    0
  );
  const totalPnl = currentValue - totalInvested;
  const roi = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0;

  const removeHoldingMutation = useMutation({
    mutationFn: (id: string) => portfolioApi.removeHolding(id),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      toast.success("Position successfully liquidated!");
    },
    onError: () => {
      toast.error("Failed to remove holding");
    },
  });

  const handleLogPosition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCardId || !selectedMarketId || !buyPrice) return;

    setIsSubmitting(true);
    try {
      await portfolioApi.addHolding({
        card_id: selectedCardId,
        market_id: selectedMarketId,
        quantity: Number(quantity),
        buy_price_gbp: parseFloat(buyPrice),
        buy_date: new Date(buyDate).toISOString(),
        condition: condition,
        notes: notes || undefined,
      });

      toast.success("New position logged successfully!");

      // Reset form
      setSelectedCardId("");
      setSelectedMarketId("");
      setQuantity(1);
      setBuyPrice("");
      setCondition("Raw");
      setBuyDate(new Date().toISOString().substring(0, 10));
      setNotes("");
      setShowLogModal(false);

      // Refresh data
      refetch();
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    } catch (error) {
      console.error("Failed to log position", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="main-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">POSITION BOOK</h1>
          <p className="view-primary-metric">Portfolio Summary</p>
        </div>
        <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
          <div>
            <div
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                marginBottom: 4,
                textAlign: "right",
              }}
            >
              CAPITAL ALLOCATED
            </div>
            <div className="mono text-bright text-lg">£{totalInvested?.toFixed(2)}</div>
          </div>
          <div>
            <div
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                marginBottom: 4,
                textAlign: "right",
              }}
            >
              NOTIONAL VALUE
            </div>
            <div className="mono text-bright text-lg">£{currentValue?.toFixed(2)}</div>
          </div>
          <div>
            <div
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                marginBottom: 4,
                textAlign: "right",
              }}
            >
              NET PNL / ROI
            </div>
            <div className={`mono text-lg ${totalPnl >= 0 ? "text-profit" : "text-loss"}`}>
              {totalPnl >= 0 ? "+" : ""}£{totalPnl?.toFixed(2)} ({roi >= 0 ? "+" : ""}
              {roi?.toFixed(1)}%)
            </div>
          </div>
          <button
            className="btn-dense btn-action"
            onClick={() => setShowLogModal(true)}
            style={{ marginLeft: 8 }}
          >
            + LOG POSITION
          </button>
        </div>
      </div>

      <div className="content-pad">
        {isLoading ? (
          <Spinner label="LOADING PORTFOLIO DATA..." />
        ) : (
          <div className="grid-asymmetric">
            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              <div className="panel">
                <div className="view-title" style={{ marginBottom: 16 }}>
                  OPEN POSITIONS
                </div>
                {displayed.length === 0 ? (
                  <div
                    style={{
                      padding: "32px 16px",
                      textAlign: "center",
                      color: "var(--text-muted)",
                      fontFamily: "var(--font-mono)",
                      fontSize: 12,
                      border: "1px dashed var(--border-dim)",
                    }}
                  >
                    [NO OPEN POSITIONS LOGGED]
                    <div style={{ marginTop: 12 }}>
                      <button
                        className="btn-dense btn-action"
                        onClick={() => setShowLogModal(true)}
                      >
                        LOG YOUR FIRST POSITION
                      </button>
                    </div>
                  </div>
                ) : (
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
                        const pnl = (h.current_value_gbp - h.buy_price_gbp) * h.quantity;
                        const r = ((h.current_value_gbp - h.buy_price_gbp) / h.buy_price_gbp) * 100;
                        return (
                          <tr key={h.id}>
                            <td>
                              <div style={{ fontWeight: 500 }}>{h.card_name}</div>
                              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                                {h.condition?.toUpperCase()} · BOUGHT{" "}
                                {new Date(h.buy_date).toLocaleDateString()}
                              </div>
                            </td>
                            <td className="mono">{h.market?.toUpperCase()}</td>
                            <td className="right mono text-muted">
                              £{h.buy_price_gbp?.toFixed(2)}
                            </td>
                            <td className="right mono text-bright">
                              £{h.current_value_gbp?.toFixed(2)}
                            </td>
                            <td
                              className={`right mono ${
                                pnl >= 0 ? "text-profit text-bright" : "text-loss"
                              }`}
                            >
                              {pnl >= 0 ? "+" : ""}£{pnl?.toFixed(2)}
                            </td>
                            <td className={`right mono ${r >= 0 ? "text-profit" : "text-loss"}`}>
                              {r >= 0 ? "+" : ""}
                              {r?.toFixed(1)}%
                            </td>
                            <td className="right">
                              <button
                                className={`btn-dense ${removeHoldingMutation.isPending && removeHoldingMutation.variables === h.id ? "opacity-50 disabled disabled:cursor-not-allowed" : "cursor-pointer"}`}
                                style={{ color: "var(--loss)" }}
                                onClick={() => removeHoldingMutation.mutate(h.id)}
                              >
                                {removeHoldingMutation.isPending &&
                                removeHoldingMutation.variables === h.id
                                  ? "LIQ..."
                                  : "LIQ"}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              <div className="panel">
                <div className="view-title" style={{ marginBottom: 16 }}>
                  30-DAY VALUATION CURVE
                </div>
                {history.length === 0 ? (
                  <div
                    style={{
                      height: 240,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "var(--text-muted)",
                      fontFamily: "var(--font-mono)",
                      fontSize: 11,
                      border: "1px dashed var(--border-dim)",
                    }}
                  >
                    [NO VALUATION HISTORY DATA]
                  </div>
                ) : (
                  <div style={{ height: 240 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={history} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
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
                          interval={Math.max(0, Math.floor(history.length / 5))}
                        />
                        <YAxis
                          tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                          tickLine={false}
                          axisLine={false}
                          tickFormatter={(v) => `£${v}`}
                          orientation="right"
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Area
                          type="stepAfter"
                          dataKey="value"
                          stroke="var(--text-main)"
                          strokeWidth={1.5}
                          fill="var(--bg-hover)"
                          dot={false}
                          isAnimationActive={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Manual Add Modal */}
      {showLogModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            className="panel"
            style={{
              width: "100%",
              maxWidth: 480,
              border: "1px solid var(--border-focus)",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.5)",
              animation: "fadeIn 0.2s ease-out",
            }}
          >
            <div
              className="view-title"
              style={{
                marginBottom: 20,
                borderBottom: "1px solid var(--border-dim)",
                paddingBottom: 12,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>LOG ACQUISITION POSITION</span>
              <button
                onClick={() => setShowLogModal(false)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  fontSize: 14,
                }}
              >
                ✕
              </button>
            </div>

            <form
              onSubmit={handleLogPosition}
              style={{ display: "flex", flexDirection: "column", gap: 16 }}
            >
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: 10,
                    color: "var(--text-muted)",
                    marginBottom: 6,
                  }}
                >
                  SELECT ASSET CARD
                </label>
                <select
                  className="input-dense"
                  style={{ width: "100%" }}
                  value={selectedCardId}
                  onChange={(e) => setSelectedCardId(e.target.value)}
                  required
                >
                  <option value="">-- SELECT POKEMON CARD --</option>
                  {cardsList.map((c: any) => (
                    <option key={c.id} value={c.id}>
                      {c.name} (#{c.number}) - {c.rarity || "Rare"}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: 10,
                      color: "var(--text-muted)",
                      marginBottom: 6,
                    }}
                  >
                    ACQUISITION VENUE
                  </label>
                  <select
                    className="input-dense"
                    style={{ width: "100%" }}
                    value={selectedMarketId}
                    onChange={(e) => setSelectedMarketId(e.target.value)}
                    required
                  >
                    <option value="">-- SELECT VENUE --</option>
                    {marketsList.map((m: any) => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.region})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: 10,
                      color: "var(--text-muted)",
                      marginBottom: 6,
                    }}
                  >
                    CONDITION GRADE
                  </label>
                  <select
                    className="input-dense"
                    style={{ width: "100%" }}
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                  >
                    <option value="Raw">Raw</option>
                    <option value="Near Mint">Near Mint (NM)</option>
                    <option value="PSA 10">PSA 10 Gem Mint</option>
                    <option value="PSA 9">PSA 9 Mint</option>
                    <option value="PSA 8">PSA 8 Near Mint-Mint</option>
                  </select>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: 10,
                      color: "var(--text-muted)",
                      marginBottom: 6,
                    }}
                  >
                    ENTRY PRICE (GBP)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    className="input-dense"
                    style={{ width: "100%" }}
                    placeholder="£0.00"
                    value={buyPrice}
                    onChange={(e) => setBuyPrice(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: 10,
                      color: "var(--text-muted)",
                      marginBottom: 6,
                    }}
                  >
                    QUANTITY
                  </label>
                  <input
                    type="number"
                    min="1"
                    className="input-dense"
                    style={{ width: "100%" }}
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    required
                  />
                </div>
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: 10,
                    color: "var(--text-muted)",
                    marginBottom: 6,
                  }}
                >
                  ACQUISITION DATE
                </label>
                <input
                  type="date"
                  className="input-dense"
                  style={{ width: "100%" }}
                  value={buyDate}
                  onChange={(e) => setBuyDate(e.target.value)}
                  required
                />
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: 10,
                    color: "var(--text-muted)",
                    marginBottom: 6,
                  }}
                >
                  INTERNAL NOTES
                </label>
                <textarea
                  className="input-dense"
                  style={{ width: "100%", height: 60, resize: "none", fontFamily: "inherit" }}
                  placeholder="e.g. Purchased with 10% coupon, target sale on eBay UK"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  gap: 12,
                  marginTop: 8,
                  borderTop: "1px solid var(--border-dim)",
                  paddingTop: 12,
                }}
              >
                <button
                  type="button"
                  className="btn-dense"
                  onClick={() => setShowLogModal(false)}
                  disabled={isSubmitting}
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="btn-dense btn-action"
                  disabled={isSubmitting || !selectedCardId || !selectedMarketId || !buyPrice}
                >
                  {isSubmitting ? "LOGGING..." : "LOG POSITION"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
