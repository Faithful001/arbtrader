export interface Opportunity {
  id: string;
  card_id: string;
  card_name?: string;
  card_image_url?: string;
  card_rarity?: string;
  card_number?: string;
  buy_market_id: string;
  sell_market_id: string;
  buy_market_name?: string;
  sell_market_name?: string;
  buy_price_gbp: number;
  sell_price_gbp: number;
  gross_spread_gbp: number;
  platform_fees_gbp: number;
  shipping_cost_gbp: number;
  import_duties_gbp: number;
  net_profit_gbp: number;
  roi_percent: number;
  confidence_score: number;
  volume_score: number;
  data_points_used?: number;
  status: string;
  created_at: string;
  expires_at?: string;
}

export interface OpportunityFeedResponse {
  items: Opportunity[];
  total: number;
  page: number;
  page_size: number;
}
