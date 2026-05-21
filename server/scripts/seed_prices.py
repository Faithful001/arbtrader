"""
seed_prices.py
--------------
Clears all existing pricing data from the database, then immediately
re-fetches live eBay 'Completed Listings' data for every active region
and repopulates both price_raw and price_normalized tables.

Usage (from the `server/` directory, with venv activated):
    python scripts/seed_prices.py

Optional flags:
    --regions UK US     Override which regions to ingest (default: all active in DB)
    --dry-run           Fetch data but do NOT write to DB (useful for debugging)
"""

import asyncio
import argparse
import sys
import os

# ── Make sure `server/src` is importable no matter where you call from ──────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import structlog
from sqlalchemy import delete, select, text

from src.infrastructure.database.session import AsyncSessionFactory
from src.domains.pricing.models import PriceRaw, PriceNormalized
from src.domains.markets.models import Market
from src.domains.pricing.service import pricing_service

log = structlog.get_logger("seed_prices")


async def clear_pricing_tables(db) -> tuple[int, int]:
    """Delete every row from price_normalized then price_raw (FK order)."""
    norm_result = await db.execute(delete(PriceNormalized))
    raw_result  = await db.execute(delete(PriceRaw))
    return raw_result.rowcount, norm_result.rowcount


async def get_active_regions(db) -> list[str]:
    """Return the `region` codes of every active Market row."""
    result = await db.execute(
        select(Market.region).where(Market.is_active == True).distinct()
    )
    return [row[0] for row in result.all()]


async def main(regions_override: list[str] | None, dry_run: bool) -> None:
    log.info("=== ArbTrader Price Seed Script ===")

    async with AsyncSessionFactory() as db:
        # ── 1. Discover regions ──────────────────────────────────────────────
        if regions_override:
            regions = regions_override
            log.info("Using CLI-supplied regions", regions=regions)
        else:
            regions = await get_active_regions(db)
            if not regions:
                log.error(
                    "No active markets found in the database. "
                    "Make sure the markets table is seeded before running this script."
                )
                sys.exit(1)
            log.info("Discovered active regions from DB", regions=regions)

        # ── 2. Clear existing data ───────────────────────────────────────────
        if dry_run:
            log.warning("DRY-RUN enabled — skipping database clear and writes.")
        else:
            log.info("Clearing existing pricing data…")
            raw_deleted, norm_deleted = await clear_pricing_tables(db)
            await db.commit()
            log.info(
                "Tables cleared",
                price_raw_deleted=raw_deleted,
                price_normalized_deleted=norm_deleted,
            )

        # ── 3. Ingest fresh data from eBay for each region ───────────────────
        total_ingested = 0
        for region in regions:
            log.info("Starting eBay ingestion", region=region)
            try:
                if dry_run:
                    # Still call ingest so we can see what *would* be fetched,
                    # but wrap in a savepoint we immediately roll back.
                    async with db.begin_nested():
                        count = await pricing_service.ingest_for_region(db, region)
                        log.info(
                            "[DRY-RUN] Would have ingested records",
                            region=region,
                            count=count,
                        )
                        await db.rollback()   # discard the savepoint writes
                else:
                    count = await pricing_service.ingest_for_region(db, region)
                    await db.commit()
                    log.info("Ingestion committed", region=region, records=count)
                    total_ingested += count
            except Exception as exc:
                log.error("Ingestion failed for region", region=region, error=str(exc))
                await db.rollback()

        # ── 4. Summary ───────────────────────────────────────────────────────
        if dry_run:
            log.info("=== DRY-RUN complete — no data was written ===")
        else:
            log.info(
                "=== Seed complete ===",
                regions_processed=regions,
                total_records_ingested=total_ingested,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clear pricing DB tables and re-fetch from eBay."
    )
    parser.add_argument(
        "--regions",
        nargs="+",
        metavar="REGION",
        help="Explicit list of region codes to ingest (e.g. UK US). "
             "Defaults to all active regions found in the DB.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch data from eBay but do not persist anything to the DB.",
    )
    args = parser.parse_args()

    asyncio.run(main(regions_override=args.regions, dry_run=args.dry_run))
