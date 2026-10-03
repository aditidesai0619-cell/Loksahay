"""Application configuration.

Kept intentionally small: this is an APSH prototype backend, not a
multi-environment production service. A single SQLite file is the
persistent store; no external infra is required to run it.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOKSAHAY_", env_file=".env", extra="ignore")

    database_url: str = f"sqlite:///{(BASE_DIR / 'loksahay.db').as_posix()}"
    region_name: str = "Uttarakhand Demo Region"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5180",
        "http://127.0.0.1:5180",
    ]

    # Priority engine defaults (section 11). Configurable at runtime via
    # GET/PUT /algorithm/config — these are only the fallback defaults used
    # to seed that single-row config table on first boot.
    default_priority_urgency: float = 0.40
    default_priority_population_need: float = 0.25
    default_priority_supply_deficit: float = 0.25
    default_priority_accessibility: float = 0.10

    # Fraction of a feasible request's requirement reserved in the fairness
    # pass before priority-ordered allocation proceeds (section 12).
    default_minimum_coverage_pct: float = 0.60

    # Average road speeds (km/h) used to convert distance into travel time
    # for Dijkstra edge weights and ETA calculations. Prototype assumption
    # for unpaved/mountain terrain — not measured.
    speed_kmh_clear: float = 36.0
    speed_kmh_degraded: float = 20.0


settings = Settings()
