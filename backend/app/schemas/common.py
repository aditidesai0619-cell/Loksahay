from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.utils.camel import to_camel


class CamelModel(BaseModel):
    """Base for every response schema — outputs camelCase JSON keys to
    match the frontend's existing `src/types/index.ts` interfaces exactly."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class LatLng(CamelModel):
    lat: float
    lng: float
