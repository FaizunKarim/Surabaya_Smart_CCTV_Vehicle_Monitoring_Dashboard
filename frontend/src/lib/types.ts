export type CCTVStatus = "online" | "offline" | "error" | "loading";

export interface VehicleCounts {
  motorcycle: number;
  car: number;
  truck: number;
  bus: number;
  line_in: number;
  line_out: number;
}

export interface CCTVRecord {
  no: number;
  id: number;
  cctv_id: string;
  name: string;
  area: string;
  status: CCTVStatus;
  latitude: number;
  longitude: number;
  stream_url: string;
  vehicle_counts: VehicleCounts;
  ai_source: string;
  last_update: string;
  last_status_change: string;
}

export interface DashboardSummary {
  total_cctv: number;
  online_cctv: number;
  offline_cctv: number;
  error_cctv: number;
  loading_cctv: number;
  total_vehicles_today: number;
  total_crossings_today: number;
  last_sync: string | null;
  ai_pipeline_enabled: boolean;
}

export interface CCTVAnalytics {
  no: number;
  id: number;
  cctv_id: string;
  name: string;
  area: string;
  status: CCTVStatus;
  stream_url: string;
  counts: VehicleCounts;
  total_vehicles: number;
  tracker_active_objects: number;
  processed_frames: number;
  sample_every_n_frames: number;
  last_update: string;
  ai_mode: string;
  line_zone: Record<string, number>;
  metadata: Record<string, unknown>;
}

export interface DashboardSocketPayload {
  type: "dashboard_snapshot";
  generated_at: string;
  summary: DashboardSummary;
  selected: CCTVAnalytics | null;
}
