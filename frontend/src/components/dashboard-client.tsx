"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Camera,
  CarFront,
  MapPinned,
  Search,
  Signal,
  Truck,
  WifiOff,
} from "lucide-react";
import {
  buildDashboardSocketUrl,
  fetchAnalytics,
  fetchCctvs,
  fetchSummary,
  isDashboardSocketPayload,
} from "@/lib/api";
import type { CCTVAnalytics, CCTVRecord, DashboardSummary } from "@/lib/types";
import { LivePlayer } from "@/components/live-player";

const CctvMap = dynamic(
  () => import("@/components/cctv-map").then((mod) => mod.CctvMap),
  {
    ssr: false,
    loading: () => (
      <div className="h-[520px] animate-pulse rounded-[28px] border border-white/10 bg-slate-900/50" />
    ),
  },
);

const emptySummary: DashboardSummary = {
  total_cctv: 0,
  online_cctv: 0,
  offline_cctv: 0,
  error_cctv: 0,
  loading_cctv: 0,
  total_vehicles_today: 0,
  total_crossings_today: 0,
  last_sync: null,
  ai_pipeline_enabled: false,
};

export function DashboardClient() {
  const [cctvs, setCctvs] = useState<CCTVRecord[]>([]);
  const [summary, setSummary] = useState<DashboardSummary>(emptySummary);
  const [selectedId, setSelectedId] = useState<string>();
  const [selectedAnalytics, setSelectedAnalytics] = useState<CCTVAnalytics | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [areaFilter, setAreaFilter] = useState("all");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        setError(undefined);
        const [nextCctvs, nextSummary] = await Promise.all([
          fetchCctvs(),
          fetchSummary(),
        ]);
        if (!active) {
          return;
        }
        setCctvs(nextCctvs);
        setSummary(nextSummary);
        setSelectedId((current) => {
          if (current && nextCctvs.some((item) => item.cctv_id === current)) {
            return current;
          }
          return nextCctvs.find((item) => item.status === "online")?.cctv_id ?? nextCctvs[0]?.cctv_id;
        });
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Gagal memuat data dashboard.");
        }
      }
    }

    loadDashboard();
    const intervalId = window.setInterval(loadDashboard, 60_000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    if (!selectedId) {
      return;
    }

    let active = true;
    fetchAnalytics(selectedId)
      .then((analytics) => {
        if (active) {
          setSelectedAnalytics(analytics);
        }
      })
      .catch(() => {
        if (active) {
          setSelectedAnalytics(null);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedId]);

  useEffect(() => {
    const socket = new WebSocket(buildDashboardSocketUrl(selectedId));

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (!isDashboardSocketPayload(payload)) {
          return;
        }
        setSummary(payload.summary);
        if (payload.selected) {
          setSelectedAnalytics(payload.selected);
        }
      } catch {
        setConnected(false);
      }
    };

    return () => {
      socket.close();
    };
  }, [selectedId]);

  const areas = useMemo(
    () => Array.from(new Set(cctvs.map((item) => item.area))).sort(),
    [cctvs],
  );

  const filteredCctvs = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return [...cctvs]
      .filter((item) => {
        if (statusFilter !== "all" && item.status !== statusFilter) {
          return false;
        }
        if (areaFilter !== "all" && item.area !== areaFilter) {
          return false;
        }
        if (!needle) {
          return true;
        }
        return (
          item.name.toLowerCase().includes(needle) ||
          item.cctv_id.toLowerCase().includes(needle) ||
          item.area.toLowerCase().includes(needle) ||
          String(item.id).includes(needle) ||
          String(item.no).includes(needle)
        );
      })
      .sort((left, right) =>
        sortDirection === "asc" ? left.no - right.no : right.no - left.no,
      );
  }, [areaFilter, cctvs, search, sortDirection, statusFilter]);

  const selectedRecord =
    cctvs.find((item) => item.cctv_id === selectedId) ?? filteredCctvs[0] ?? null;
  const activeAnalytics =
    selectedAnalytics?.cctv_id === selectedId ? selectedAnalytics : null;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(61,105,243,0.28),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(72,227,177,0.16),_transparent_22%),linear-gradient(180deg,_#050816_0%,_#09101f_50%,_#050816_100%)] text-slate-100">
      <div className="mx-auto flex w-full max-w-[1720px] flex-col gap-6 px-4 py-5 lg:px-6 xl:px-8">
        <section className="overflow-hidden rounded-[34px] border border-white/10 bg-slate-950/55 p-6 shadow-[0_40px_120px_rgba(4,8,20,0.55)] backdrop-blur-xl">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold tracking-[0.45em] text-cyan-200 uppercase">
                Surabaya Smart Mobility Grid
              </p>
              <h1 className="mt-4 max-w-4xl text-4xl font-semibold tracking-tight text-white md:text-6xl">
                Dashboard monitoring CCTV kendaraan Surabaya dengan peta live, status real-time, dan analitik AI.
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 md:text-base">
                Menggabungkan discovery 444 CCTV publik, stream HLS, sinkronisasi 5 menit, serta pipeline kendaraan berbasis YOLO + ByteTrack yang siap diaktifkan melalui backend FastAPI.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:w-[520px]">
              <StatCard label="Total CCTV" value={summary.total_cctv} accent="cyan" icon={<Camera className="size-4" />} />
              <StatCard label="Online" value={summary.online_cctv} accent="emerald" icon={<Signal className="size-4" />} />
              <StatCard label="Offline" value={summary.offline_cctv} accent="rose" icon={<WifiOff className="size-4" />} />
              <StatCard label="Kendaraan Hari Ini" value={summary.total_vehicles_today} accent="violet" icon={<CarFront className="size-4" />} />
            </div>
          </div>
        </section>

        {error ? (
          <section className="rounded-[28px] border border-rose-400/25 bg-rose-400/10 px-5 py-4 text-sm text-rose-100">
            {error}
          </section>
        ) : null}

        <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-[30px] border border-white/10 bg-slate-950/50 p-4 backdrop-blur-xl">
            <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-semibold tracking-[0.35em] text-cyan-200 uppercase">
                  Surabaya Map Dashboard
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-white">
                  Marker status CCTV seluruh Surabaya
                </h2>
              </div>

              <div className="flex flex-wrap items-center gap-2 text-xs">
                <Legend status="online" label="Online" />
                <Legend status="offline" label="Offline" />
                <Legend status="error" label="Error" />
                <Legend status="loading" label="Loading" />
              </div>
            </div>

            <CctvMap
              cctvs={filteredCctvs}
              selectedCctvId={selectedRecord?.cctv_id}
              onSelect={setSelectedId}
            />
          </div>

          <div className="flex flex-col gap-6">
            <section className="rounded-[30px] border border-white/10 bg-slate-950/50 p-4 backdrop-blur-xl">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold tracking-[0.35em] text-cyan-200 uppercase">
                    Monitoring Statistics
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold text-white">
                    Snapshot operasional
                  </h2>
                </div>
                <div
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    connected
                      ? "border border-emerald-400/25 bg-emerald-400/10 text-emerald-200"
                      : "border border-amber-400/25 bg-amber-400/10 text-amber-200"
                  }`}
                >
                  {connected ? "WebSocket 1s aktif" : "Menyambung ulang..."}
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <MiniMetric label="Error CCTV" value={summary.error_cctv} icon={<Activity className="size-4" />} />
                <MiniMetric label="Loading CCTV" value={summary.loading_cctv} icon={<Signal className="size-4" />} />
                <MiniMetric label="Area terpilih" value={selectedRecord?.area ?? "-"} icon={<MapPinned className="size-4" />} />
                <MiniMetric label="Mode AI" value={activeAnalytics?.ai_mode ?? (summary.ai_pipeline_enabled ? "yolo-supervision" : "dry-run")} icon={<Truck className="size-4" />} />
                <MiniMetric label="Crossing Hari Ini" value={summary.total_crossings_today} icon={<Activity className="size-4" />} />
                <MiniMetric label="Tracker Aktif" value={activeAnalytics?.tracker_active_objects ?? 0} icon={<Truck className="size-4" />} />
              </div>
            </section>

            <section className="rounded-[30px] border border-white/10 bg-slate-950/50 p-4 backdrop-blur-xl">
              <div className="flex items-end justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold tracking-[0.35em] text-cyan-200 uppercase">
                    CCTV Analytics Page
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold text-white">
                    Viewer dan counter kendaraan
                  </h2>
                </div>
                {activeAnalytics ? (
                  <p className="text-xs text-slate-400">
                    Update terakhir {formatDateTime(activeAnalytics.last_update)}
                  </p>
                ) : null}
              </div>

              <div className="mt-4">
                <LivePlayer analytics={activeAnalytics} />
              </div>

              {activeAnalytics ? (
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <DetailPill label="No CCTV" value={activeAnalytics.no} />
                  <DetailPill label="ID CCTV" value={activeAnalytics.id} />
                  <DetailPill label="Nama" value={activeAnalytics.name} />
                  <DetailPill label="Wilayah" value={activeAnalytics.area} />
                  <DetailPill label="AI Mode" value={activeAnalytics.ai_mode} />
                  <DetailPill label="Frames Diproses" value={activeAnalytics.processed_frames} />
                  <DetailPill label="Sampling Tiap N Frame" value={activeAnalytics.sample_every_n_frames} />
                  <DetailPill label="Line In / Out" value={`${activeAnalytics.counts.line_in} / ${activeAnalytics.counts.line_out}`} />
                </div>
              ) : null}
            </section>
          </div>
        </section>

        <section className="rounded-[30px] border border-white/10 bg-slate-950/50 p-4 backdrop-blur-xl">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-xs font-semibold tracking-[0.35em] text-cyan-200 uppercase">
                CCTV Discovery
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-white">
                Daftar CCTV terurut dan dapat difilter
              </h2>
            </div>

            <div className="grid gap-3 md:grid-cols-4 xl:min-w-[920px]">
              <label className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <Search className="size-4 text-slate-400" />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Cari no, nama, ID, wilayah..."
                  className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
                />
              </label>

              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
              >
                <option value="all">Semua status</option>
                <option value="online">Online</option>
                <option value="offline">Offline</option>
                <option value="error">Error</option>
                <option value="loading">Loading</option>
              </select>

              <select
                value={areaFilter}
                onChange={(event) => setAreaFilter(event.target.value)}
                className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
              >
                <option value="all">Semua wilayah</option>
                {areas.map((area) => (
                  <option key={area} value={area}>
                    {area}
                  </option>
                ))}
              </select>

              <button
                type="button"
                onClick={() =>
                  setSortDirection((current) => (current === "asc" ? "desc" : "asc"))
                }
                className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15"
              >
                Sort Nomor CCTV: {sortDirection === "asc" ? "Ascending" : "Descending"}
              </button>
            </div>
          </div>

          <div className="mt-5 grid max-h-[520px] gap-3 overflow-y-auto pr-1">
            {filteredCctvs.map((cctv) => (
              <button
                key={cctv.cctv_id}
                type="button"
                onClick={() => setSelectedId(cctv.cctv_id)}
                className={`grid gap-3 rounded-[24px] border px-4 py-4 text-left transition md:grid-cols-[auto_1fr_auto] md:items-center ${
                  selectedRecord?.cctv_id === cctv.cctv_id
                    ? "border-cyan-300/40 bg-cyan-300/10 shadow-[0_18px_40px_rgba(56,189,248,0.15)]"
                    : "border-white/8 bg-white/[0.03] hover:bg-white/[0.05]"
                }`}
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/5 text-sm font-semibold text-white">
                  {cctv.no}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <p className="text-base font-semibold text-white">{cctv.name}</p>
                    <StatusBadge status={cctv.status} />
                  </div>
                  <p className="mt-1 text-sm text-slate-400">
                    ID {cctv.id} · {cctv.area} · {cctv.cctv_id}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm text-slate-300 sm:flex sm:items-center">
                  <VehicleChip label="Motor" value={cctv.vehicle_counts.motorcycle} />
                  <VehicleChip label="Mobil" value={cctv.vehicle_counts.car} />
                  <VehicleChip label="Truk" value={cctv.vehicle_counts.truck} />
                  <VehicleChip label="Bus" value={cctv.vehicle_counts.bus} />
                  <VehicleChip label="In/Out" value={`${cctv.vehicle_counts.line_in}/${cctv.vehicle_counts.line_out}`} />
                </div>
              </button>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("id-ID", {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(value));
}

function StatCard({
  label,
  value,
  accent,
  icon,
}: {
  label: string;
  value: number;
  accent: "cyan" | "emerald" | "rose" | "violet";
  icon: React.ReactNode;
}) {
  const accentClass =
    {
      cyan: "from-cyan-400/20 to-cyan-400/5 text-cyan-100",
      emerald: "from-emerald-400/20 to-emerald-400/5 text-emerald-100",
      rose: "from-rose-400/20 to-rose-400/5 text-rose-100",
      violet: "from-violet-400/20 to-violet-400/5 text-violet-100",
    }[accent] ?? "from-cyan-400/20 to-cyan-400/5 text-cyan-100";

  return (
    <div className={`rounded-[24px] border border-white/10 bg-gradient-to-br ${accentClass} px-4 py-4`}>
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold tracking-[0.34em] uppercase">{label}</p>
        {icon}
      </div>
      <p className="mt-5 text-4xl font-semibold tracking-tight">{value.toLocaleString("id-ID")}</p>
    </div>
  );
}

function MiniMetric({
  label,
  value,
  icon,
}: {
  label: string;
  value: number | string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-4">
      <div className="flex items-center justify-between text-slate-400">
        <p className="text-xs font-semibold tracking-[0.25em] uppercase">{label}</p>
        {icon}
      </div>
      <p className="mt-3 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

function Legend({
  status,
  label,
}: {
  status: "online" | "offline" | "error" | "loading";
  label: string;
}) {
  const color = {
    online: "bg-emerald-300",
    offline: "bg-rose-300",
    error: "bg-amber-300",
    loading: "bg-indigo-300",
  }[status];

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-slate-200">
      <span className={`size-2.5 rounded-full ${color}`} />
      <span>{label}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const className =
    {
      online: "border-emerald-400/20 bg-emerald-400/10 text-emerald-200",
      offline: "border-rose-400/20 bg-rose-400/10 text-rose-200",
      error: "border-amber-400/20 bg-amber-400/10 text-amber-200",
      loading: "border-indigo-400/20 bg-indigo-400/10 text-indigo-200",
    }[status] ?? "border-white/10 bg-white/10 text-white";

  return (
    <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase ${className}`}>
      {status}
    </span>
  );
}

function VehicleChip({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-slate-200">
      {label}: {value}
    </div>
  );
}

function DetailPill({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3">
      <p className="text-[11px] font-semibold tracking-[0.25em] text-slate-400 uppercase">
        {label}
      </p>
      <p className="mt-2 text-sm text-white">{value}</p>
    </div>
  );
}
