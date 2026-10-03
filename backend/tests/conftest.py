from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register models on Base)
from app.db import Base, get_db


def _new_test_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def db_session():
    """A fresh, empty in-memory SQLite database per test."""
    engine = _new_test_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def seeded_db(db_session):
    """An in-memory database populated by the real seed script — used by
    tests that want the full demo dataset rather than a hand-built one."""
    from app.data.seed import seed_all

    seed_all(db_session)
    return db_session


@pytest.fixture()
def client(db_session):
    """A FastAPI TestClient wired to the SAME per-test in-memory database
    via dependency override — never touches the dev server's loksahay.db,
    and never triggers the app's own startup seeding (lifespan is not
    entered since the client is used outside a `with` block)."""
    from fastapi.testclient import TestClient

    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def seeded_client(client, db_session):
    """Same as `client`, but the shared database is pre-seeded with the
    full demo dataset first."""
    from app.data.seed import seed_all

    seed_all(db_session)
    return client
