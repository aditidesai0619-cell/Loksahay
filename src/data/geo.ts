import type { LatLng } from "@/types";

// Static map-view defaults for the Uttarakhand demo region. Actual road
// network, requests, sources and vehicles all come from the live
// backend (see `service.ts`) — these are just the Leaflet map's initial
// center/zoom, kept here since they're UI configuration, not domain data.

export const REGION_NAME = "Uttarakhand Demo Region";
export const MAP_CENTER: LatLng = { lat: 30.15, lng: 79.1 };
export const MAP_DEFAULT_ZOOM = 8;
