import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { marketsApi } from "../api/markets.api";
import Spinner from "../../../shared/Spinner";

interface Listing {
  id: string;
  card_name: string;
  card_image_url: string | null;
  rarity: string | null;
  market: string;
  region: string;
  condition: string;
  price_gbp: number;
  listing_type: string;
  ends_in: string | null;
  url: string | null;
  sold_count: number;
}

function useListings() {
  return useQuery<Listing[]>({
    queryKey: ["market-listings"],
    queryFn: () => marketsApi.getListings(),
  });
}

export default function MarketListings() {
  const { data: listings = [], isLoading } = useListings();
  const [regionFilter, setRegionFilter] = useState<"all" | "UK" | "US">("all");
  const [typeFilter, setTypeFilter] = useState<"all" | "Buy It Now" | "Auction">("all");
  const [search, setSearch] = useState("");

  const filtered = listings.filter((l: Listing) => {
    if (regionFilter !== "all" && l.region !== regionFilter) return false;
    if (typeFilter !== "all" && l.listing_type !== typeFilter) return false;
    if (search && !l.card_name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="main-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">MARKETPLACE LISTINGS</h1>
          <p className="view-primary-metric">Raw Order Book</p>
        </div>
        <div className="control-bar" style={{ marginBottom: 0 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>MKT:</span>
            {(["all", "UK", "US"] as const).map((r) => (
              <button
                key={r}
                className="btn-dense"
                style={{ background: regionFilter === r ? "var(--border-focus)" : "transparent" }}
                onClick={() => setRegionFilter(r)}
              >
                {r.toUpperCase()}
              </button>
            ))}
          </div>
          {/* <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginLeft: 16 }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>TYPE:</span>
            {(['all', 'Buy It Now', 'Auction'] as const).map(t => (
              <button key={t} className="btn-dense"
                style={{ background: typeFilter === t ? 'var(--border-focus)' : 'transparent' }}
                onClick={() => setTypeFilter(t)}>
                {t === 'all' ? 'ALL' : t.toUpperCase()}
              </button>
            ))}
          </div> */}
          <input
            className="input-dense"
            style={{ width: 200, marginLeft: 16 }}
            placeholder="SEARCH ASSET..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="content-pad">
        {isLoading ? (
          <Spinner label="LOADING ORDER BOOK..." />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>ASSET / RARITY</th>
                <th>EXCHANGE</th>
                <th>GRADE</th>
                <th>EXECUTION</th>
                <th className="right">ASK SIZE (GBP)</th>
                <th className="right">TIME IN FORCE</th>
                <th className="right">ROUTE</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((l) => (
                <tr key={l.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{l.card_name}</div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{l.rarity}</div>
                  </td>
                  <td className="mono">{l.market.toUpperCase()}</td>
                  <td className="mono">{l.condition.toUpperCase()}</td>
                  <td
                    className="mono"
                    style={{
                      color: l.listing_type === "Auction" ? "var(--warn)" : "var(--text-muted)",
                    }}
                  >
                    {l.listing_type.toUpperCase()}
                  </td>
                  <td className="right numeric text-bright">£{l.price_gbp.toFixed(2)}</td>
                  <td
                    className="right numeric"
                    style={{ color: l.ends_in ? "var(--warn)" : "var(--text-muted)" }}
                  >
                    {l.ends_in ?? "GTC"}
                  </td>
                  <td className="right">
                    <a
                      href={l.url ?? undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-dense"
                    >
                      VIEW
                    </a>
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
