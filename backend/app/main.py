from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    algorithm_config,
    allocations,
    analytics,
    bottlenecks,
    deliveries,
    map as map_router,
    partners,
    replan,
    requests as requests_router,
    roads,
    routes as routes_router,
    scenario,
    sources,
    system,
    vehicles,
)
from app.config import settings
from app.db import SessionLocal, init_db
from app.models import RoadNode


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        if db.query(RoadNode).count() == 0:
            from app.data.seed import seed_all

            seed_all(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="LokSahay API",
    description=(
        "Algorithmic disaster-relief resource allocation, transport "
        "coordination and dynamic replanning backend. GREEDY primary "
        "paradigm over a GRAPH (road network) routing model."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"error": {"type": "ValueError", "message": str(exc)}})


@app.exception_handler(LookupError)
async def lookup_error_handler(request: Request, exc: LookupError):
    return JSONResponse(status_code=404, content={"error": {"type": "NotFound", "message": str(exc)}})


for r in (
    system,
    requests_router,
    sources,
    vehicles,
    roads,
    routes_router,
    allocations,
    deliveries,
    map_router,
    replan,
    scenario,
    analytics,
    bottlenecks,
    algorithm_config,
    partners,
):
    app.include_router(r.router)
