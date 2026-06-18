"use client";

import type { ComponentType, ReactNode } from "react";
import { MapContainer, CircleMarker, Popup, TileLayer } from "react-leaflet";
import type { CCTVRecord, CCTVStatus } from "@/lib/types";

const statusStyles: Record<
  CCTVStatus,
  { fill: string; stroke: string; label: string }
> = {
  online: { fill: "#54f0a6", stroke: "#7ff7bd", label: "Online" },
  offline: { fill: "#ff6b7d", stroke: "#ff8d9b", label: "Offline" },
  error: { fill: "#f6be57", stroke: "#ffd57e", label: "Error" },
  loading: { fill: "#8ca4ff", stroke: "#b4c2ff", label: "Loading" },
};

interface CctvMapProps {
  cctvs: CCTVRecord[];
  selectedCctvId?: string;
  onSelect: (cctvId: string) => void;
}

interface MapRootProps {
  center: [number, number];
  zoom: number;
  scrollWheelZoom: boolean;
  className?: string;
  children: ReactNode;
}

interface TileLayerRootProps {
  attribution: string;
  url: string;
}

interface CircleMarkerRootProps {
  center: [number, number];
  radius: number;
  pathOptions: {
    color: string;
    fillColor: string;
    fillOpacity: number;
    weight: number;
  };
  eventHandlers: {
    click: () => void;
  };
  children: ReactNode;
}

export function CctvMap({
  cctvs,
  selectedCctvId,
  onSelect,
}: CctvMapProps) {
  const MapRoot = MapContainer as unknown as ComponentType<MapRootProps>;
  const TileLayerRoot = TileLayer as unknown as ComponentType<TileLayerRootProps>;
  const CircleMarkerRoot =
    CircleMarker as unknown as ComponentType<CircleMarkerRootProps>;
  const PopupRoot = Popup as unknown as ComponentType<{ children: ReactNode }>;

  return (
    <MapRoot
      center={[-7.2756, 112.7508]}
      zoom={12}
      scrollWheelZoom
      className="h-[520px] w-full rounded-[28px]"
    >
      <TileLayerRoot
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {cctvs.map((cctv) => {
        const style = statusStyles[cctv.status];
        const selected = selectedCctvId === cctv.cctv_id;

        return (
          <CircleMarkerRoot
            key={cctv.cctv_id}
            center={[cctv.latitude, cctv.longitude]}
            radius={selected ? 10 : 7}
            pathOptions={{
              color: style.stroke,
              fillColor: style.fill,
              fillOpacity: selected ? 0.95 : 0.78,
              weight: selected ? 3 : 2,
            }}
            eventHandlers={{
              click: () => onSelect(cctv.cctv_id),
            }}
          >
            <PopupRoot>
              <div className="space-y-2 text-sm text-slate-900">
                <p className="text-xs font-semibold tracking-[0.3em] text-slate-500 uppercase">
                  CCTV #{cctv.no}
                </p>
                <div>
                  <p className="font-semibold">{cctv.name}</p>
                  <p className="text-slate-600">{cctv.area}</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <p className="text-slate-500">ID</p>
                    <p>{cctv.id}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Status</p>
                    <p>{style.label}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Motor + Mobil</p>
                    <p>{cctv.vehicle_counts.motorcycle + cctv.vehicle_counts.car}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Truk + Bus</p>
                    <p>{cctv.vehicle_counts.truck + cctv.vehicle_counts.bus}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => onSelect(cctv.cctv_id)}
                  className="w-full rounded-full bg-slate-900 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800"
                >
                  Open Dashboard
                </button>
              </div>
            </PopupRoot>
          </CircleMarkerRoot>
        );
      })}
    </MapRoot>
  );
}
