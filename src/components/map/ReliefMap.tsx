import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Polyline, Tooltip, useMap } from "react-leaflet";
import type { AffectedRequest, Delivery, LatLng, RoadEdge, RoadNode, Route, SupplySource, Vehicle } from "@/types";
import { MAP_CENTER, MAP_DEFAULT_ZOOM } from "@/data/geo";
import { areaIcon, sourceIcon, vehicleIcon, HEX } from "./icons";

export interface MapLayerState {
  affectedAreas: boolean;
  supplySources: boolean;
  vehicles: boolean;
  routes: boolean;
  blockedRoads: boolean;
}

export const DEFAULT_LAYER_STATE: MapLayerState = {
  affectedAreas: true,
  supplySources: true,
  vehicles: true,
  routes: true,
  blockedRoads: true,
};

interface ReliefMapProps {
  requests: AffectedRequest[];
  sources: SupplySource[];
  vehicles: Vehicle[];
  routes: Route[];
  roadNodes: RoadNode[];
  roadEdges: RoadEdge[];
  deliveries: Delivery[];
  layers: MapLayerState;
  highlightedRouteId?: string;
  onSelectRequest?: (r: AffectedRequest) => void;
  onSelectSource?: (s: SupplySource) => void;
  onSelectVehicle?: (v: Vehicle) => void;
  onSelectEdge?: (e: RoadEdge) => void;
  heightClassName?: string;
}

function urgencyTone(urgency: AffectedRequest["urgency"]) {
  switch (urgency) {
    case "Critical":
      return "critical" as const;
    case "High":
      return "warning" as const;
    case "Medium":
      return "secondary" as const;
    case "Low":
      return "muted" as const;
  }
}

function urgencySize(urgency: AffectedRequest["urgency"]) {
  switch (urgency) {
    case "Critical":
      return 30;
    case "High":
      return 24;
    case "Medium":
      return 19;
    case "Low":
      return 15;
  }
}

function FlyToPath({ path }: { path: LatLng[] }) {
  const map = useMap();
  useEffect(() => {
    if (path.length === 0) return;
    const bounds = path.map((p) => [p.lat, p.lng] as [number, number]);
    map.flyToBounds(bounds, { padding: [48, 48], maxZoom: 11 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(path)]);
  return null;
}

export function ReliefMap({
  requests,
  sources,
  vehicles,
  routes,
  roadNodes,
  roadEdges,
  deliveries,
  layers,
  highlightedRouteId,
  onSelectRequest,
  onSelectSource,
  onSelectVehicle,
  onSelectEdge,
  heightClassName = "h-full",
}: ReliefMapProps) {
  const nodeMap = new Map(roadNodes.map((n) => [n.id, n.location]));
  const deliveryByRoute = new Map(deliveries.map((d) => [d.routeId, d]));
  const highlightedRoute = highlightedRouteId ? routes.find((r) => r.id === highlightedRouteId) : undefined;

  return (
    <MapContainer
      center={[MAP_CENTER.lat, MAP_CENTER.lng]}
      zoom={MAP_DEFAULT_ZOOM}
      className={heightClassName}
      style={{ width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {highlightedRoute && <FlyToPath path={highlightedRoute.path} />}

      {layers.blockedRoads &&
        roadEdges.map((edge) => {
          const from = nodeMap.get(edge.from);
          const to = nodeMap.get(edge.to);
          if (!from || !to) return null;
          const color = edge.condition === "Blocked" ? HEX.critical : edge.condition === "Degraded" ? HEX.warning : "#b9b7ac";
          return (
            <Polyline
              key={edge.id}
              positions={[
                [from.lat, from.lng],
                [to.lat, to.lng],
              ]}
              pathOptions={{
                color,
                weight: edge.condition === "Blocked" ? 3 : 2,
                dashArray: edge.condition === "Blocked" ? "2 7" : undefined,
                opacity: edge.condition === "Clear" ? 0.45 : 0.85,
              }}
              eventHandlers={onSelectEdge ? { click: () => onSelectEdge(edge) } : undefined}
            >
              <Tooltip sticky>
                {edge.id}: {edge.from} ↔ {edge.to} · {edge.condition}
                {edge.blockedReason ? ` — ${edge.blockedReason}` : ""}
              </Tooltip>
            </Polyline>
          );
        })}

      {layers.routes &&
        routes.map((route) => {
          if (route.id === highlightedRouteId) return null; // drawn last, on top
          const delivery = deliveryByRoute.get(route.id);
          return (
            <Polyline
              key={route.id}
              positions={route.path.map((p) => [p.lat, p.lng] as [number, number])}
              pathOptions={{
                color: route.feasible ? HEX.accent : HEX.critical,
                weight: 3.5,
                opacity: highlightedRouteId ? 0.3 : 0.85,
              }}
            >
              <Tooltip sticky>
                Route {route.id} · {route.distanceKm} km · ETA {route.etaMinutes} min
                {delivery ? ` · ${delivery.destinationName}` : ""}
              </Tooltip>
            </Polyline>
          );
        })}

      {layers.routes && highlightedRoute && (
        <>
          {/* Underlay "glow" so the selected route reads clearly against overlapping roads/routes. */}
          <Polyline
            positions={highlightedRoute.path.map((p) => [p.lat, p.lng] as [number, number])}
            pathOptions={{ color: HEX.primary, weight: 10, opacity: 0.25 }}
          />
          <Polyline
            positions={highlightedRoute.path.map((p) => [p.lat, p.lng] as [number, number])}
            pathOptions={{ color: HEX.primary, weight: 4.5, opacity: 1 }}
          >
            <Tooltip sticky>
              Selected route {highlightedRoute.id} · {highlightedRoute.distanceKm} km · ETA{" "}
              {highlightedRoute.etaMinutes} min
            </Tooltip>
          </Polyline>
        </>
      )}

      {layers.affectedAreas &&
        requests.map((req) => (
          <Marker
            key={req.id}
            position={[req.location.lat, req.location.lng]}
            icon={areaIcon(urgencyTone(req.urgency), urgencySize(req.urgency))}
            eventHandlers={onSelectRequest ? { click: () => onSelectRequest(req) } : undefined}
          >
            <Tooltip>
              <strong>{req.areaName}</strong>
              <br />
              {req.resource} · {req.urgency} · {req.status}
            </Tooltip>
          </Marker>
        ))}

      {layers.supplySources &&
        sources.map((src) => (
          <Marker
            key={src.id}
            position={[src.location.lat, src.location.lng]}
            icon={sourceIcon(src.verified)}
            eventHandlers={onSelectSource ? { click: () => onSelectSource(src) } : undefined}
          >
            <Tooltip>
              <strong>{src.name}</strong>
              <br />
              {src.type} · {src.verified ? "Verified" : "Unverified"}
            </Tooltip>
          </Marker>
        ))}

      {layers.vehicles &&
        vehicles.map((v) => (
          <Marker
            key={v.id}
            position={[v.location.lat, v.location.lng]}
            icon={vehicleIcon(v.status === "Unavailable" ? "critical" : v.status === "Available" ? "secondary" : "accent")}
            eventHandlers={onSelectVehicle ? { click: () => onSelectVehicle(v) } : undefined}
          >
            <Tooltip>
              <strong>{v.id}</strong> · {v.partner}
              <br />
              {v.type} · {v.status}
            </Tooltip>
          </Marker>
        ))}
    </MapContainer>
  );
}
