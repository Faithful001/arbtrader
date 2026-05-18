import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ExternalLink, ArrowUpDown } from 'lucide-react'

// Mock market listings data
function useMockListings() {
  return useQuery({
    queryKey: ['market-listings'],
    queryFn: async () => {
      const cards = [
        { name: 'Charizard Base Set Holo', img: 'https://images.pokemontcg.io/base1/4_hires.png', rarity: 'Holo Rare' },
        { name: 'Blastoise Base Set Holo', img: 'https://images.pokemontcg.io/base1/2_hires.png', rarity: 'Holo Rare' },
        { name: 'Venusaur Base Set Holo', img: 'https://images.pokemontcg.io/base1/15_hires.png', rarity: 'Holo Rare' },
        { name: 'Mewtwo Base Set Holo', img: 'https://images.pokemontcg.io/base1/10_hires.png', rarity: 'Holo Rare' },
        { name: 'Raichu Base Set Holo', img: 'https://images.pokemontcg.io/base1/14_hires.png', rarity: 'Holo Rare' },
        { name: 'Gyarados Base Set Holo', img: 'https://images.pokemontcg.io/base1/6_hires.png', rarity: 'Holo Rare' },
        { name: 'Lugia Neo Genesis', img: 'https://images.pokemontcg.io/neo1/9_hires.png', rarity: 'Holo Rare' },
        { name: 'Ho-Oh Neo Revelation', img: 'https://images.pokemontcg.io/neo2/10_hires.png', rarity: 'Holo Rare' },
        { name: 'Umbreon Gold Star', img: 'https://images.pokemontcg.io/ex5/17_hires.png', rarity: 'Gold Star' },
        { name: 'Espeon Gold Star', img: 'https://images.pokemontcg.io/ex5/16_hires.png', rarity: 'Gold Star' },
      ]
      return cards.flatMap((card, ci) =>
        ['eBay UK', 'eBay US'].map((market, mi) => ({
          id: `${ci}-${mi}`,
          card_name: card.name,
          card_image_url: card.img,
          rarity: card.rarity,
          market,
          region: mi === 0 ? 'UK' : 'US',
          condition: ['Raw', 'Near Mint', 'PSA 9', 'PSA 10'][Math.floor(Math.random() * 4)],
          price_gbp: +(40 + Math.random() * 200).toFixed(2),
          listing_type: Math.random() > 0.5 ? 'Buy It Now' : 'Auction',
          ends_in: Math.random() > 0.5 ? `${Math.floor(Math.random() * 48)}h ${Math.floor(Math.random() * 60)}m` : null,
          url: '#',
          sold_count: Math.floor(Math.random() * 30),
        }))
      ).sort((a, b) => a.price_gbp - b.price_gbp)
    },
  })
}

export default function MarketListings() {
  const { data: listings = [], isLoading } = useMockListings()
  const [regionFilter, setRegionFilter] = useState<'all' | 'UK' | 'US'>('all')
  const [typeFilter, setTypeFilter] = useState<'all' | 'Buy It Now' | 'Auction'>('all')
  const [search, setSearch] = useState('')

  const filtered = listings.filter(l => {
    if (regionFilter !== 'all' && l.region !== regionFilter) return false
    if (typeFilter !== 'all' && l.listing_type !== typeFilter) return false
    if (search && !l.card_name.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Marketplace Listings</h1>
          <p className="page-subtitle">Unified view across eBay UK and eBay US</p>
        </div>
        <div className="live-badge">
          <span className="live-dot" />
          {filtered.length} listings
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          className="input"
          style={{ width: 240 }}
          placeholder="Search card name…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div style={{ display: 'flex', gap: 4 }}>
          {(['all', 'UK', 'US'] as const).map(r => (
            <button key={r} className={`btn btn-sm ${regionFilter === r ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setRegionFilter(r)}>
              {r === 'all' ? 'All Regions' : `eBay ${r}`}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {(['all', 'Buy It Now', 'Auction'] as const).map(t => (
            <button key={t} className={`btn btn-sm ${typeFilter === t ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setTypeFilter(t)}>
              {t === 'all' ? 'All Types' : t}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="loading-state"><div className="spinner" /><span>Loading listings…</span></div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Card</th>
                <th>Market</th>
                <th>Condition</th>
                <th>Type</th>
                <th style={{ textAlign: 'right' }}>Price (GBP)</th>
                <th>Ends In</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(l => (
                <tr key={l.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <img src={l.card_image_url} alt={l.card_name}
                        style={{ width: 32, height: 32, borderRadius: 4, objectFit: 'cover', background: 'var(--bg-overlay)' }}
                        onError={(e) => { (e.target as HTMLImageElement).src = 'https://placehold.co/32x32/161b25/6c63ff?text=TC' }}
                      />
                      <div>
                        <div style={{ fontWeight: 500, fontSize: 13 }}>{l.card_name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{l.rarity}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${l.region === 'UK' ? 'badge-accent' : 'badge-cyan'}`}>
                      {l.market}
                    </span>
                  </td>
                  <td><span className="badge badge-muted">{l.condition}</span></td>
                  <td>
                    <span className={`badge ${l.listing_type === 'Auction' ? 'badge-yellow' : 'badge-muted'}`}>
                      {l.listing_type}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className="mono" style={{ fontWeight: 600 }}>£{l.price_gbp.toFixed(2)}</span>
                  </td>
                  <td style={{ color: l.ends_in ? 'var(--yellow)' : 'var(--text-muted)', fontSize: 12 }}>
                    {l.ends_in ?? '—'}
                  </td>
                  <td>
                    <a href={l.url} target="_blank" rel="noopener noreferrer"
                      className="btn btn-ghost btn-sm btn-icon">
                      <ExternalLink size={13} />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
