# LokSahay

An algorithmic decision-support system for coordinating disaster-relief
resources, vehicles, routes and delivery deadlines. Built for the APSH
2026 demonstration. Full-stack: a FastAPI backend running a greedy/graph
allocation engine, and a React frontend that consumes it.

## Stack

- Backend: FastAPI, SQLAlchemy, SQLite, pytest — see `backend/README.md`
- Frontend: React + TypeScript + Vite, Tailwind CSS v4, React Router, Leaflet / React Leaflet (OpenStreetMap tiles), Recharts

## Running both together

```bash
# Terminal 1 — backend (seeds its own database on first run)
cd backend
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000

# Terminal 2 — frontend
npm install
npm run dev                     # http://localhost:5173 (or 5180)
```

The frontend talks to the backend at `http://localhost:8000` by default;
override with `VITE_API_BASE_URL` (see `.env.example`) if you run the
backend on a different port.

## Structure

- `backend/app` — FastAPI app: `api/` (routers), `models/` (SQLAlchemy), `schemas/` (Pydantic, camelCase JSON), `services/` (orchestration), `algorithms/` (graph routing, priority engine, greedy allocation, baseline, bottlenecks, scenario mutations), `data/` (seed script)
- `backend/tests` — pytest suite covering the algorithm and the API
- `src/types` — domain models (requests, sources, vehicles, routes, allocations, deliveries, replanning, scenarios, analytics, bottlenecks) — the contract both ends agree on
- `src/data/service.ts` — the only module UI code imports domain data through; calls the real backend over HTTP
- `src/components/common` — generic UI primitives (badges, tables, drawers, states)
- `src/components/domain` — LokSahay-specific components (allocation flow, algorithm panel, bottlenecks, etc.)
- `src/components/map` — the Leaflet relief map and marker icon factories
- `src/pages` — one file per route (Overview, Needs, Resources, Allocation, Relief Map, Transport, Replanning, Scenario Simulator, Analytics, plus System Status / Coordinator Profile / Settings)
