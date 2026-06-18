"use client";

import Hls from "hls.js";
import { useEffect, useRef } from "react";
import { AlertTriangle, Radio, WifiOff } from "lucide-react";
import type { CCTVAnalytics } from "@/lib/types";

interface LivePlayerProps {
  analytics: CCTVAnalytics | null;
}

export function LivePlayer({ analytics }: LivePlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !analytics || analytics.status !== "online") {
      return;
    }

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = analytics.stream_url;
      return;
    }

    if (!Hls.isSupported()) {
      return;
    }

    const hls = new Hls({
      enableWorker: true,
      lowLatencyMode: true,
    });
    hls.loadSource(analytics.stream_url);
    hls.attachMedia(video);

    return () => {
      hls.destroy();
    };
  }, [analytics]);

  if (!analytics) {
    return (
      <div className="flex h-[360px] items-center justify-center rounded-[28px] border border-white/10 bg-slate-950/70 text-slate-400">
        Pilih CCTV untuk menampilkan stream dan analitik kendaraan.
      </div>
    );
  }

  if (analytics.status !== "online") {
    const Icon = analytics.status === "error" ? AlertTriangle : WifiOff;

    return (
      <div className="flex h-[360px] flex-col items-center justify-center gap-4 rounded-[28px] border border-amber-400/20 bg-slate-950/70 px-6 text-center text-slate-300">
        <Icon className="size-10 text-amber-300" />
        <div>
          <p className="text-lg font-semibold text-white">Stream belum tersedia</p>
          <p className="mt-2 text-sm text-slate-400">
            Status CCTV saat ini <span className="font-semibold capitalize">{analytics.status}</span>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[28px] border border-cyan-400/20 bg-slate-950/80 shadow-[0_30px_80px_rgba(7,10,18,0.55)]">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.35em] text-cyan-200 uppercase">
            Live Video
          </p>
          <h3 className="mt-1 text-lg font-semibold text-white">{analytics.name}</h3>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-200">
          <Radio className="size-3.5" />
          LIVE
        </div>
      </div>

      <div className="relative">
        <video
          ref={videoRef}
          controls
          autoPlay
          muted
          playsInline
          className="h-[360px] w-full bg-black object-cover"
        />

        <div className="pointer-events-none absolute inset-x-0 bottom-0 grid gap-3 bg-gradient-to-t from-slate-950 via-slate-950/70 to-transparent p-5 md:grid-cols-4">
          <CounterCard label="Motor" value={analytics.counts.motorcycle} color="text-emerald-300" />
          <CounterCard label="Mobil" value={analytics.counts.car} color="text-sky-300" />
          <CounterCard label="Truk" value={analytics.counts.truck} color="text-rose-300" />
          <CounterCard label="Bus" value={analytics.counts.bus} color="text-fuchsia-300" />
        </div>
      </div>
    </div>
  );
}

function CounterCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 backdrop-blur">
      <p className="text-[11px] font-semibold tracking-[0.24em] text-slate-400 uppercase">
        {label}
      </p>
      <p className={`mt-2 text-2xl font-semibold ${color}`}>{value}</p>
    </div>
  );
}
