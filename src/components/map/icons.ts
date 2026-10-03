import L from "leaflet";

const HEX = {
  primary: "#254d3a",
  secondary: "#66745f",
  accent: "#c86b3c",
  warning: "#d69a2d",
  critical: "#b84235",
  muted: "#72766f",
  surface: "#ffffff",
};

type Tone = keyof typeof HEX;

export function areaIcon(tone: Tone, size: number): L.DivIcon {
  const px = size;
  return L.divIcon({
    className: "ls-marker",
    html: `<div style="
      width:${px}px;height:${px}px;border-radius:50%;
      background:${HEX[tone]}cc;border:2px solid ${HEX[tone]};
      box-shadow:0 0 0 3px ${HEX[tone]}26;
    "></div>`,
    iconSize: [px, px],
    iconAnchor: [px / 2, px / 2],
    popupAnchor: [0, -px / 2],
  });
}

export function sourceIcon(verified: boolean): L.DivIcon {
  const color = verified ? HEX.primary : HEX.muted;
  return L.divIcon({
    className: "ls-marker",
    html: `<div style="
      width:16px;height:16px;background:${color};border:2px solid ${HEX.surface};
      transform:rotate(45deg);box-shadow:0 1px 3px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    popupAnchor: [0, -10],
  });
}

export function vehicleIcon(tone: Tone): L.DivIcon {
  return L.divIcon({
    className: "ls-marker",
    html: `<div style="
      width:14px;height:14px;background:${HEX[tone]};border:2px solid ${HEX.surface};
      border-radius:3px;box-shadow:0 1px 3px rgba(0,0,0,0.35);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -9],
  });
}

export { HEX };
export type { Tone };
