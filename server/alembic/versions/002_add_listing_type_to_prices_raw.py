"""Add listing_type column to prices_raw

Revision ID: 002
Revises: 001
Create Date: 2026-05-21

"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "prices_raw",
        sa.Column("listing_type", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("prices_raw", "listing_type")
