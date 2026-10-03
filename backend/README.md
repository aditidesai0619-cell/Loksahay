# LokSahay Backend

FastAPI + SQLAlchemy + SQLite backend implementing the greedy/graph
allocation engine, routing, replanning, scenario simulation and
analytics for LokSahay. See `app/` for the layout (`api`, `models`,
`schemas`, `services`, `algorithms`, `data`, `utils`) and the project
root's final report for the full design writeup.

## Running

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The database (`loksahay.db`, SQLite) is created and seeded with
deterministic demo data automatically on first startup if it doesn't
already exist. Delete `loksahay.db` and restart to reseed from scratch
(e.g. to refresh deadlines relative to the current time).

API docs: http://localhost:8000/docs (FastAPI's auto-generated Swagger UI).

## Testing

```bash
pytest -q
```

## Configuration

Environment variables (prefix `LOKSAHAY_`), e.g. `LOKSAHAY_DATABASE_URL`,
`LOKSAHAY_CORS_ORIGINS` — see `app/config.py` for the full list and
defaults. The default CORS origins already include the frontend's Vite
dev server ports (5173, 5180).
