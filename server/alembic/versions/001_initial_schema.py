"""Initial schema — all 10 tables with UUIDs and indexes."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("telegram_chat_id", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("is_admin", sa.Boolean, nullable=False, default=False),
        sa.Column("preferences", JSONB, nullable=False, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "card_sets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("release_year", sa.Integer, nullable=True),
        sa.Column("total_cards", sa.Integer, nullable=True),
        sa.Column("series", sa.String(100), nullable=True),
        sa.Column("set_code", sa.String(20), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("set_id", UUID(as_uuid=True), sa.ForeignKey("card_sets.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("number", sa.String(20), nullable=True),
        sa.Column("rarity", sa.String(50), nullable=True),
        sa.Column("card_type", sa.String(50), nullable=True),
        sa.Column("hp", sa.Integer, nullable=True),
        sa.Column("image_url", sa.Text, nullable=True),
        sa.Column("tcg_player_id", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_cards_name", "cards", ["name"])
    op.create_index("ix_cards_set_id", "cards", ["set_id"])

    op.create_table(
        "markets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("region", sa.String(10), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("fee_percent", sa.Float, nullable=False),
        sa.Column("shipping_estimate_gbp", sa.Float, nullable=False),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_markets_region", "markets", ["region"])

    op.create_table(
        "prices_raw",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("card_id", UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("market_id", UUID(as_uuid=True), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("condition", sa.String(50), nullable=True),
        sa.Column("sold_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=True, unique=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_prices_raw_card_id", "prices_raw", ["card_id"])
    op.create_index("ix_prices_raw_market_id", "prices_raw", ["market_id"])

    op.create_table(
        "prices_normalized",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("price_raw_id", UUID(as_uuid=True), sa.ForeignKey("prices_raw.id"), nullable=False),
        sa.Column("card_id", UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("market_id", UUID(as_uuid=True), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("price_gbp", sa.Float, nullable=False),
        sa.Column("condition_normalized", sa.String(50), nullable=False),
        sa.Column("fx_rate_used", sa.Float, nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_prices_norm_card_id", "prices_normalized", ["card_id"])
    op.create_index("ix_prices_norm_market_id", "prices_normalized", ["market_id"])
    op.create_index("ix_prices_norm_snapshot_at", "prices_normalized", ["snapshot_at"])

    op.create_table(
        "arbitrage_opportunities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("card_id", UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("buy_market_id", UUID(as_uuid=True), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("sell_market_id", UUID(as_uuid=True), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("buy_price_gbp", sa.Float, nullable=False),
        sa.Column("sell_price_gbp", sa.Float, nullable=False),
        sa.Column("gross_spread_gbp", sa.Float, nullable=False),
        sa.Column("platform_fees_gbp", sa.Float, nullable=False),
        sa.Column("shipping_cost_gbp", sa.Float, nullable=False),
        sa.Column("import_duties_gbp", sa.Float, nullable=False, default=0),
        sa.Column("net_profit_gbp", sa.Float, nullable=False),
        sa.Column("roi_percent", sa.Float, nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False),
        sa.Column("volume_score", sa.Float, nullable=False),
        sa.Column("data_points_used", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_arb_card_id", "arbitrage_opportunities", ["card_id"])
    op.create_index("ix_arb_net_profit", "arbitrage_opportunities", ["net_profit_gbp"])
    op.create_index("ix_arb_status", "arbitrage_opportunities", ["status"])

    op.create_table(
        "alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("conditions", JSONB, nullable=False, default={}),
        sa.Column("delivery_channel", sa.String(20), nullable=False, default="telegram"),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])

    op.create_table(
        "alert_triggers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_id", UUID(as_uuid=True), sa.ForeignKey("alerts.id"), nullable=False),
        sa.Column("opportunity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("payload", JSONB, nullable=False, default={}),
        sa.Column("delivered", sa.Boolean, nullable=False, default=False),
        sa.Column("delivery_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alert_triggers_alert_id", "alert_triggers", ["alert_id"])

    op.create_table(
        "portfolios",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("card_id", UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("market_id", UUID(as_uuid=True), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, default=1),
        sa.Column("buy_price_gbp", sa.Float, nullable=False),
        sa.Column("buy_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_value_gbp", sa.Float, nullable=True),
        sa.Column("condition", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"])

    op.create_table(
        "transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("card_id", UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("portfolio_id", UUID(as_uuid=True), sa.ForeignKey("portfolios.id"), nullable=True),
        sa.Column("market_id", UUID(as_uuid=True), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("transaction_type", sa.String(10), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, default=1),
        sa.Column("price_gbp", sa.Float, nullable=False),
        sa.Column("fees_gbp", sa.Float, nullable=False, default=0),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])

    op.create_table(
        "automation_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("conditions", JSONB, nullable=False, default={}),
        sa.Column("actions", JSONB, nullable=False, default={}),
        sa.Column("is_active", sa.Boolean, nullable=False, default=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("automation_rules")
    op.drop_table("transactions")
    op.drop_table("portfolios")
    op.drop_table("alert_triggers")
    op.drop_table("alerts")
    op.drop_table("arbitrage_opportunities")
    op.drop_table("prices_normalized")
    op.drop_table("prices_raw")
    op.drop_table("markets")
    op.drop_table("cards")
    op.drop_table("card_sets")
    op.drop_table("users")
