import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, ChevronDown, ChevronUp, ExternalLink, Image as ImageIcon } from "lucide-react";

import { marketsApi } from "../api/markets.api";
import Spinner from "../../../shared/Spinner";

interface SoldItemDetail {
  title: string | null;
  price: number;
  currency: string;
  price_gbp: number;
  url: string | null;
  sold_at: string | null;
}

interface ExplorerCard {
  id: string;
  name: string;
  number: string | null;
  rarity: string | null;
  card_type: string | null;
  image_url: string | null;
  set_name: string;
  uk_avg: number | null;
  us_avg: number | null;
  uk_last_3_avg: number | null;
  us_last_3_avg: number | null;
  uk_last_3: SoldItemDetail[];
  us_last_3: SoldItemDetail[];
  uk_search_url: string;
  us_search_url: string;
}

export default function MarketListings() {
  const [searchQuery, setSearchQuery] = useState("");
  const [rarityFilter, setRarityFilter] = useState("all");
  const [expandedCardId, setExpandedCardId] = useState<string | null>(null);

  const { data: cards = [], isLoading, isError } = useQuery<ExplorerCard[]>({
    queryKey: ["explorer-cards"],
    queryFn: () => marketsApi.getExplorerCards(),
    refetchInterval: 30000, // auto-refresh every 30 seconds
  });

  const uniqueRarities = Array.from(
    new Set(cards.map((c) => c.rarity).filter(Boolean))
  ) as string[];

  const filteredCards = cards.filter((c) => {
    // Search filter: card name, number, set name, rarity
    const searchLower = searchQuery.toLowerCase();
    const nameMatch = c.name.toLowerCase().includes(searchLower);
    const numMatch = c.number ? c.number.toLowerCase().includes(searchLower) : false;
    const rarityMatch = c.rarity ? c.rarity.toLowerCase().includes(searchLower) : false;
    
    if (searchQuery && !nameMatch && !numMatch && !rarityMatch) {
      return false;
    }

    if (rarityFilter !== "all" && c.rarity !== rarityFilter) {
      return false;
    }

    return true;
  });

  const toggleExpand = (cardId: string) => {
    if (expandedCardId === cardId) {
      setExpandedCardId(null);
    } else {
      setExpandedCardId(cardId);
    }
  };

  return (
    <div className="main-view">
      <div className="view-header" style={{ flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 className="view-title">Set Explorer</h1>
          <p className="view-primary-metric">Crown Zenith Set ({cards.length} Cards)</p>
        </div>
        <div className="control-bar" style={{ marginBottom: 0, flexWrap: "wrap", gap: 16 }}>
          {/* Rarity Dropdown */}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase" }}>Rarity</span>
            <select
              className="input-dense"
              value={rarityFilter}
              onChange={(e) => setRarityFilter(e.target.value)}
              style={{ minWidth: 150 }}
            >
              <option value="all">ALL RARITIES</option>
              {uniqueRarities.map((r) => (
                <option key={r} value={r}>
                  {r.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Search bar */}
          <div style={{ display: "flex", alignItems: "center", position: "relative" }}>
            <Search size={14} style={{ position: "absolute", left: 10, color: "var(--text-muted)" }} />
            <input
              className="input-dense"
              style={{ width: 220, paddingLeft: 30 }}
              placeholder="SEARCH BY NAME OR NUMBER..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="content-pad">
        {isLoading ? (
          <Spinner label="LOADING CROWN ZENITH DATA..." />
        ) : isError ? (
          <div style={{ color: "var(--loss)", fontFamily: "var(--font-mono)" }}>
            [ERR: CONNECTION TO PRICING API FAILED]
          </div>
        ) : filteredCards.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            [NO CARDS MATCHING FILTER CRITERIA]
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 40 }}>IMAGE</th>
                <th>ASSET / CARD DETAILS</th>
                <th>RARITY</th>
                <th className="right">US AVG (ALL)</th>
                <th className="right">US LAST 3 (AVG)</th>
                <th className="right">UK AVG (ALL)</th>
                <th className="right">UK LAST 3 (AVG)</th>
                <th className="right" style={{ textAlign: "center", width: 320 }}>
                  MARKET SEARCH & HISTORY
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredCards.map((c) => {
                const isExpanded = expandedCardId === c.id;
                return (
                  <>
                    <tr key={c.id} style={{ verticalAlign: "middle" }}>
                      {/* 1. Image */}
                      <td>
                        <div style={{ position: "relative" }}>
                          {c.image_url ? (
                            <img
                              src={c.image_url}
                              alt={c.name}
                              style={{
                                width: 36,
                                height: 50,
                                objectFit: "contain",
                                borderRadius: 4,
                                border: "1px solid var(--border-dim)",
                                transition: "transform 0.15s ease",
                              }}
                              className="hover-scale-img"
                            />
                          ) : (
                            <div
                              style={{
                                width: 36,
                                height: 50,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                background: "var(--bg-card)",
                                borderRadius: 4,
                                border: "1px solid var(--border-dim)",
                                color: "var(--text-muted)",
                              }}
                            >
                              <ImageIcon size={16} />
                            </div>
                          )}
                        </div>
                      </td>

                      {/* 2. Card details */}
                      <td>
                        <div style={{ fontWeight: 500, color: "var(--text-bright)" }}>{c.name}</div>
                        <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: 2 }}>
                          <span>#{c.number || "N/A"}</span>
                          <span>•</span>
                          <span>{c.set_name}</span>
                        </div>
                      </td>

                      {/* 3. Rarity */}
                      <td style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        {c.rarity || "Unknown Rarity"}
                      </td>

                      {/* 4. US Avg */}
                      <td className="right numeric text-bright">
                        {c.us_avg ? `£${c.us_avg.toFixed(2)}` : "—"}
                      </td>

                      {/* 5. US Last 3 Avg */}
                      <td className="right numeric text-muted">
                        {c.us_last_3_avg ? `£${c.us_last_3_avg.toFixed(2)}` : "—"}
                      </td>

                      {/* 6. UK Avg */}
                      <td className="right numeric text-bright">
                        {c.uk_avg ? `£${c.uk_avg.toFixed(2)}` : "—"}
                      </td>

                      {/* 7. UK Last 3 Avg */}
                      <td className="right numeric text-muted">
                        {c.uk_last_3_avg ? `£${c.uk_last_3_avg.toFixed(2)}` : "—"}
                      </td>

                      {/* 8. Live eBay links & expandable toggle */}
                      <td className="right">
                        <div style={{ display: "flex", gap: 6, justifyContent: "flex-end", alignItems: "center" }}>
                          <a
                            href={c.us_search_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-dense"
                            style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10 }}
                          >
                            EBAY US <ExternalLink size={10} />
                          </a>
                          <a
                            href={c.uk_search_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-dense"
                            style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10 }}
                          >
                            EBAY UK <ExternalLink size={10} />
                          </a>
                          <button
                            className={`btn-dense ${isExpanded ? "btn-action" : ""}`}
                            onClick={() => toggleExpand(c.id)}
                            style={{ display: "flex", alignItems: "center", gap: 2, fontSize: 10, minWidth: 90 }}
                          >
                            {isExpanded ? "HIDE SALES" : "SHOW SALES"}
                            {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                          </button>
                        </div>
                      </td>
                    </tr>

                    {/* Expandable sub-row showing the details of the last 3 sales */}
                    {isExpanded && (
                      <tr style={{ background: "var(--bg-highlight)" }}>
                        <td colSpan={8} style={{ padding: "16px 20px" }}>
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                            {/* US Sales */}
                            <div>
                              <h4 style={{ fontSize: 11, color: "var(--text-bright)", letterSpacing: "0.05em", marginBottom: 10, borderBottom: "1px solid var(--border-dim)", paddingBottom: 4 }}>
                                LATEST EBAY US SOLD TRANSACTIONS
                              </h4>
                              {c.us_last_3.length === 0 ? (
                                <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                                  [NO RECENT US TRANSACTION DATA AVAILABLE]
                                </div>
                              ) : (
                                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                                  {c.us_last_3.map((sale, idx) => (
                                    <div
                                      key={idx}
                                      style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                        background: "rgba(255, 255, 255, 0.02)",
                                        padding: "8px 12px",
                                        borderRadius: 4,
                                        borderLeft: "2px solid var(--border-focus)",
                                      }}
                                    >
                                      <div style={{ flex: 1, marginRight: 16 }}>
                                        <a
                                          href={sale.url || undefined}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          style={{ fontSize: 11, fontWeight: 500, color: "var(--text-bright)", textDecoration: "none", display: "flex", alignItems: "center", gap: 4 }}
                                          className="hover-underline"
                                        >
                                          {sale.title || "eBay Listing"} <ExternalLink size={10} />
                                        </a>
                                        <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                                          Sold at: {sale.sold_at ? new Date(sale.sold_at).toLocaleDateString() : "Unknown"}
                                        </span>
                                      </div>
                                      <div style={{ textAlign: "right" }}>
                                        <div style={{ fontSize: 11, fontWeight: 700, color: "var(--profit)" }}>
                                          {sale.price.toFixed(2)} {sale.currency}
                                        </div>
                                        {sale.currency !== "GBP" && (
                                          <div style={{ fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                                            (£{sale.price_gbp.toFixed(2)})
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* UK Sales */}
                            <div>
                              <h4 style={{ fontSize: 11, color: "var(--text-bright)", letterSpacing: "0.05em", marginBottom: 10, borderBottom: "1px solid var(--border-dim)", paddingBottom: 4 }}>
                                LATEST EBAY UK SOLD TRANSACTIONS
                              </h4>
                              {c.uk_last_3.length === 0 ? (
                                <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                                  [NO RECENT UK TRANSACTION DATA AVAILABLE]
                                </div>
                              ) : (
                                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                                  {c.uk_last_3.map((sale, idx) => (
                                    <div
                                      key={idx}
                                      style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                        background: "rgba(255, 255, 255, 0.02)",
                                        padding: "8px 12px",
                                        borderRadius: 4,
                                        borderLeft: "2px solid var(--border-focus)",
                                      }}
                                    >
                                      <div style={{ flex: 1, marginRight: 16 }}>
                                        <a
                                          href={sale.url || undefined}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          style={{ fontSize: 11, fontWeight: 500, color: "var(--text-bright)", textDecoration: "none", display: "flex", alignItems: "center", gap: 4 }}
                                          className="hover-underline"
                                        >
                                          {sale.title || "eBay Listing"} <ExternalLink size={10} />
                                        </a>
                                        <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                                          Sold at: {sale.sold_at ? new Date(sale.sold_at).toLocaleDateString() : "Unknown"}
                                        </span>
                                      </div>
                                      <div style={{ textAlign: "right" }}>
                                        <div style={{ fontSize: 11, fontWeight: 700, color: "var(--profit)" }}>
                                          £{sale.price.toFixed(2)}
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
