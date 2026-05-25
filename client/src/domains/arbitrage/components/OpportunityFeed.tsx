import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useOpportunities, useRecalculate } from "../hooks/useOpportunities";
import { portfolioApi } from "../../portfolio/api/portfolio.api";
import { marketsApi } from "../../markets/api/markets.api";
import Spinner from "../../../shared/Spinner";
import type { Opportunity } from "../types";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

export default function OpportunityFeed() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [minProfit, setMinProfit] = useState(5);
  const [loggingOpportunity, setLoggingOpportunity] = useState<Opportunity | null>(null);

  // New Filters
  const [rarityFilter, setRarityFilter] = useState("");
  const [minPriceFilter, setMinPriceFilter] = useState("");
  const [maxPriceFilter, setMaxPriceFilter] = useState("");

  // States for logging modal
  const [quantity, setQuantity] = useState(1);
  const [condition, setCondition] = useState("Raw");
  const [buyPrice, setBuyPrice] = useState("");
  const [selectedMarketId, setSelectedMarketId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data, isLoading, isError } = useOpportunities({
    sort_by: "net_profit_gbp",
    min_profit: minProfit,
    limit: 50,
  });
  const recalc = useRecalculate();

  const { data: marketsList = [] } = useQuery({
    queryKey: ["markets-list"],
    queryFn: () => marketsApi.getMarkets(),
  });

  const items: Opportunity[] = data?.items ?? [];

  const uniqueRarities = Array.from(
    new Set(items.map((opp) => opp.card_rarity).filter(Boolean))
  ) as string[];

  const filteredItems = items.filter((opp) => {
    if (rarityFilter && opp.card_rarity !== rarityFilter) {
      return false;
    }
    if (minPriceFilter) {
      const minVal = parseFloat(minPriceFilter);
      if (!isNaN(minVal) && opp.sell_price_gbp < minVal) {
        return false;
      }
    }
    if (maxPriceFilter) {
      const maxVal = parseFloat(maxPriceFilter);
      if (!isNaN(maxVal) && opp.sell_price_gbp > maxVal) {
        return false;
      }
    }
    return true;
  });

  const handleOpenLogModal = (opp: Opportunity) => {
    setLoggingOpportunity(opp);
    setBuyPrice(opp.buy_price_gbp.toFixed(2));
    setQuantity(1);
    setCondition("Raw");
    // Pre-select US market as the default buy/acquisition source
    const usMarket = marketsList.find((m: any) => m.region === "US");
    if (usMarket) {
      setSelectedMarketId(usMarket.id);
    } else if (marketsList.length > 0) {
      setSelectedMarketId(marketsList[0].id);
    }
  };

  const handleLogSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loggingOpportunity || !selectedMarketId || !buyPrice) return;

    setIsSubmitting(true);
    try {
      await portfolioApi.addHolding({
        card_id: loggingOpportunity.card_id,
        market_id: selectedMarketId,
        quantity: Number(quantity),
        buy_price_gbp: parseFloat(buyPrice),
        buy_date: new Date().toISOString(),
        condition: condition,
        notes: `Logged directly from Arbitrage Spread Feed (Spread Profit: £${loggingOpportunity.net_profit_gbp.toFixed(2)})`,
      });
      setLoggingOpportunity(null);
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      toast.success("Opportunity successfully logged into your Portfolio!");
      navigate("/portfolio");
    } catch (error) {
      console.error("Failed to log opportunity position", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="main-view">
      {/* Header */}
      <div className="view-header" style={{ flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 className="view-title">Cross-Market Spreads</h1>
          <p className="view-primary-metric">Live Feed</p>
        </div>
        <div className="control-bar" style={{ marginBottom: 0, flexWrap: "wrap", gap: 16 }}>
          {/* Min Spread */}
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

          {/* Rarity Filter */}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>
              Rarity
            </span>
            <select
              className="input-dense"
              value={rarityFilter}
              onChange={(e) => setRarityFilter(e.target.value)}
            >
              <option value="">ALL RARITIES</option>
              {uniqueRarities.map((r) => (
                <option key={r} value={r}>
                  {r.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Price Filters */}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>
              Price
            </span>
            <input
              type="number"
              placeholder="Min"
              className="input-dense"
              style={{ width: 60 }}
              value={minPriceFilter}
              onChange={(e) => setMinPriceFilter(e.target.value)}
            />
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>–</span>
            <input
              type="number"
              placeholder="Max"
              className="input-dense"
              style={{ width: 60 }}
              value={maxPriceFilter}
              onChange={(e) => setMaxPriceFilter(e.target.value)}
            />
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
        ) : filteredItems.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            [NO SPREADS MATCHING ACTIVE FILTERS]
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
                <th className="right" style={{ textAlign: "center" }}>
                  ACTIONS
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((opp) => (
                <tr key={opp.id}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <a
                        href={`https://www.ebay.co.uk/sch/i.html?_nkw=${encodeURIComponent(opp.card_name ?? "")}&LH_Complete=1&LH_Sold=1`}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="View last sold on eBay UK"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <img
                          src={opp.card_image_url || "https://placehold.co/40x56/111216/22252C?text=No+Img"}
                          alt={opp.card_name}
                          style={{
                            width: 36,
                            height: 50,
                            objectFit: "contain",
                            borderRadius: 4,
                            border: "1px solid var(--border-dim)",
                            cursor: "pointer",
                            transition: "transform 0.15s ease, border-color 0.15s ease",
                          }}
                          className="hover-scale-img"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src =
                              "https://placehold.co/40x56/111216/22252C?text=No+Img";
                          }}
                        />
                      </a>
                      <div>
                        <div style={{ fontWeight: 500 }}>{opp.card_name}</div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                          {opp.card_id.slice(0, 8)}...
                        </div>
                      </div>
                    </div>
                  </td>
                  <td style={{ color: "var(--text-muted)", fontSize: 12 }}>
                    {opp.card_rarity ?? "Unknown"}
                  </td>
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
                  <td
                    className="right"
                    style={{ display: "flex", gap: 8, justifyContent: "center" }}
                  >
                    <Link to={`/cards/${opp.card_id}`} className="btn-dense">
                      ANALYZE
                    </Link>
                    <button
                      className="btn-dense btn-action"
                      onClick={() => handleOpenLogModal(opp)}
                    >
                      LOG
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pre-filled Log Trade Modal */}
      {loggingOpportunity && (
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
              maxWidth: 440,
              border: "1px solid var(--border-focus)",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.5)",
              animation: "fadeIn 0.15s ease-out",
            }}
          >
            <div
              className="view-title"
              style={{
                marginBottom: 16,
                borderBottom: "1px solid var(--border-dim)",
                paddingBottom: 10,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>LOG ACQUISITION TRADE</span>
              <button
                onClick={() => setLoggingOpportunity(null)}
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
              onSubmit={handleLogSubmit}
              style={{ display: "flex", flexDirection: "column", gap: 14 }}
            >
              <div>
                <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 4 }}>
                  CARD TO LOG
                </div>
                <div style={{ fontWeight: 500, fontSize: 13, color: "var(--text-bright)" }}>
                  {loggingOpportunity.card_name}
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: 10,
                      color: "var(--text-muted)",
                      marginBottom: 4,
                    }}
                  >
                    BUYING MARKET
                  </label>
                  <select
                    className="input-dense"
                    style={{ width: "100%" }}
                    value={selectedMarketId}
                    onChange={(e) => setSelectedMarketId(e.target.value)}
                    required
                  >
                    <option value="">-- SELECT --</option>
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
                      marginBottom: 4,
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
                    <option value="PSA 8">PSA 8 NM-Mint</option>
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
                      marginBottom: 4,
                    }}
                  >
                    ACQUISITION PX (GBP)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    className="input-dense"
                    style={{ width: "100%" }}
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
                      marginBottom: 4,
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
                  onClick={() => setLoggingOpportunity(null)}
                  disabled={isSubmitting}
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="btn-dense btn-action"
                  disabled={isSubmitting || !selectedMarketId || !buyPrice}
                >
                  {isSubmitting ? "LOGGING..." : "LOG TRADE"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
