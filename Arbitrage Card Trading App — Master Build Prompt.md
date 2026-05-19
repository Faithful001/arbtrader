# Arbitrage Card Trading App - Master Build Prompt

## Purpose of This Prompt

This document is a **single source of truth prompt** intended to be given to an AI engineering system or development team.

It must be followed **exactly**. The goal is to build an end-to-end production-ready MVP of the _Arbitrage Card Trading App_ with **no missing pieces**, spanning frontend, backend, data, automation, and infrastructure.

The system must be designed to scale beyond MVP without architectural rewrites.

---

## 1. Product Summary

Build a lightweight but powerful arbitrage intelligence platform for trading cards (starting with Pokémon).

The app identifies **buy-low / sell-high** opportunities across regional marketplaces using historical and near‑real‑time sales data, calculates true net profit, and surfaces high-confidence opportunities with alerts and automation hooks.

Primary user outcome:

- Generate consistent arbitrage profit faster than the market

North Star Metric:

- **Profit generated per user per week (£)**

---

## 2. Architecture Overview (MANDATORY)

### Monorepo Structure

The project **must** be a monorepo with **strict separation** between frontend and backend.

```
/arbtrader
  /client      # Frontend (React)
  /server      # Backend (FastAPI)
  /shared      # Shared types, schemas, constants (optional but encouraged)
  README.md
```

Rules:

- `client` and `server` **must not** import each other directly
- Each folder must have its **own package manager and dependency graph**
- Communication happens **only via HTTP APIs / OpenAPI contracts**

---

## 3. Domain‑Driven Design (CRITICAL)

Both frontend and backend **must** follow **Domain‑Driven Design (DDD)** principles.

### Core Domains

These domains must exist in **both client and server**:

1. **cards** – card metadata, rarity, grading, sets
2. **markets** – marketplaces, regions, currencies
3. **pricing** – raw sales data, normalized prices
4. **arbitrage** – spread calculation, profit logic, confidence scoring
5. **alerts** – notification rules and delivery
6. **portfolio** – owned cards, PnL, valuation
7. **users** – preferences, filters, alert settings
8. **automation** – rules engine (future‑proofed)

Each domain must encapsulate:

- Its own models
- Business logic
- API interfaces
- UI state (frontend)

No "utils dumping ground" allowed.

---

## 4. Backend Specification (FastAPI)

### Tech Stack

- **FastAPI** - API layer
- **SQLAlchemy 2.0** - ORM
- **Supabase (PostgreSQL)** - primary database
- **Celery** - background task queue
- **Redis** - Celery broker + cache
- **Alembic** - database migrations

---

### Backend Folder Structure (MANDATORY)

```
/server
  /src
    /domains
      /arbitrage
      /cards
      /markets
      /pricing
      /alerts
      /portfolio
      /users
      /automation
    /infrastructure
      /database
      /supabase
      /celery
      /external_apis
    /api
      /v1
    /core
      config.py
      logging.py
      security.py
  main.py
```

---

### Arbitrage Engine (Core Feature)

#### Price Aggregation

Implement background tasks that:

- Pull **last sold** data from:
  - eBay UK
  - eBay US
  - (Phase‑ready: eBay Japan)

Normalize:

- Currency (real‑time FX)
- Condition (raw, PSA, etc.)
- Date

Store:

- Raw records
- Normalized pricing snapshots

All ingestion must run via **Celery tasks**.

---

#### Arbitrage Detection Logic

For each card:

- Compare prices between regions
- Calculate:
  - Gross spread
  - Platform fees
  - Shipping
  - Import duties (configurable per user)
- Output:
  - Net profit (£)
  - ROI %
  - Confidence score (based on volume + recency)

Persist results to an **Opportunities Feed** table.

---

### Alerts & Automation

#### Alerts

Support triggers for:

- New arbitrage opportunity
- Price drops
- Undervalued listings
- Auction ending soon

Delivery channels:

- Telegram bot (mandatory)
- Email (optional, pluggable)

Alerts must be event‑driven and processed via Celery.

---

#### Automation (Future‑Safe)

Design interfaces for:

- Auto‑bid rules
- ROI‑based execution rules

**Do not hardcode logic** - use rule definitions stored in DB.

---

## 5. Frontend Specification (React)

### Tech Stack

- **React** (SPA or Next.js optional)
- **TypeScript**
- **Domain‑based folder structure**
- **API client generated from OpenAPI**

---

### Frontend Folder Structure

```
/client
  /src
    /domains
      /arbitrage
      /cards
      /markets
      /pricing
      /alerts
      /portfolio
      /users
    /shared
    /ui
    /api
```

Each domain must include:

- Components
- Hooks
- State management
- API adapters
- Domain models

---

### Core Screens (MVP)

1. **Opportunity Feed (Home)**
   - Sorted by profit / ROI
   - Real‑time refresh (manual initially)

2. **Card Detail Page**
   - Regional pricing comparison
   - Historical chart
   - Arbitrage breakdown

3. **Marketplace Listings**
   - Unified listings view
   - Auction tracking

4. **Alerts Dashboard**
   - Active alerts
   - Trigger history

5. **Portfolio / PnL**
   - Holdings
   - Live valuation
   - Profit tracking

---

### UX Requirements

- Dark mode default
- Data‑dense layouts
- Fast interactions
- Minimal animations

This is a **trading dashboard**, not a consumer app.

---

## 6. Database Design (Supabase / PostgreSQL)

Must include:

- users
- cards
- card_sets
- markets
- prices_raw
- prices_normalized
- arbitrage_opportunities
- alerts
- portfolios
- transactions

All tables must:

- Use UUIDs
- Be migration‑managed
- Be index‑optimized for reads

---

## 7. Background Jobs & Scheduling

Celery must handle:

- Price ingestion
- Arbitrage recalculation
- Alert dispatch
- Portfolio valuation updates

Jobs must be:

- Idempotent
- Retry‑safe
- Observable (logs + metrics)

---

## 8. MVP Constraints (DO NOT OVERBUILD)

MVP includes ONLY:

- eBay UK vs US
- Manual refresh
- Telegram alerts
- No auto‑buy execution

Everything else must be **architecturally prepared but disabled**.

---

## 9. Quality Bar

The system must:

- Be production‑ready
- Be testable
- Be extensible
- Avoid tight coupling

No shortcuts. No hardcoding. No global state hacks.

---

## 10. Final Instruction

If any feature, domain, table, API, or background job is missing - **the implementation is incorrect**.

Build this as if real money depends on it.
