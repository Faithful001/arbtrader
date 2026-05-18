# ArbTrader — Arbitrage Card Trading Platform

A production-ready arbitrage intelligence platform for trading cards (Pokémon first).
Identifies **buy-low / sell-high** opportunities across eBay UK and eBay US, calculates true net profit, and surfaces high-confidence opportunities with Telegram alerts.

---

## Monorepo Structure

```
/arbtrader
  /client      # React + TypeScript + Vite frontend
  /server      # FastAPI + Celery + SQLAlchemy backend
  /shared      # Shared type definitions (future)
  docker-compose.yml
  README.md
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node 20+
- Python 3.11+

### 1. Environment Setup

```bash
# Backend
cp server/.env.example server/.env
# Fill in your credentials in server/.env

# Frontend
cp client/.env.example client/.env
```

### 2. Run with Docker Compose (Recommended)

```bash
docker-compose up --build
```

Services:
| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Celery Flower | http://localhost:5555 |

### 3. Run Locally (Development)

**Backend:**
```bash
cd server
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

**Celery Worker:**
```bash
cd server
celery -A src.infrastructure.celery.app worker --loglevel=info
```

**Celery Beat (Scheduler):**
```bash
cd server
celery -A src.infrastructure.celery.app beat --loglevel=info
```

**Frontend:**
```bash
cd client
npm install
npm run dev
```

---

## Architecture

- **DDD (Domain-Driven Design)** — 8 domains: cards, markets, pricing, arbitrage, alerts, portfolio, users, automation
- **FastAPI** async API with SQLAlchemy 2.0 ORM
- **Celery + Redis** for background price ingestion, arbitrage recalculation, and alert dispatch
- **Alembic** for database migrations
- **Supabase (PostgreSQL)** as primary datastore
- **React + Vite** SPA with TanStack Query and Zustand

---

## North Star Metric
> **Profit generated per user per week (£)**
