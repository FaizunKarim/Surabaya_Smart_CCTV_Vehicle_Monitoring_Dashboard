---
title: Cctv Surabaya Db
emoji: 🌍
colorFrom: blue
colorTo: pink
sdk: docker
pinned: false
---

# Backend Deployment Guide

Backend ini dirancang sebagai service terpisah dari frontend. Frontend cukup mengetahui satu variabel:

```bash
NEXT_PUBLIC_API_BASE_URL=https://<backend-anda>
```

## Fitur Backend

- Sinkronisasi katalog CCTV Surabaya dari sumber asli setiap 5 menit
- API REST untuk daftar CCTV, detail, analytics, dan histori
- WebSocket dashboard untuk pembaruan 1 detik
- Worker vision terpisah untuk frame sampling HLS
- YOLO + `supervision.ByteTrack` + `LineZone` untuk line-crossing counter
- Penyimpanan historis ke PostgreSQL atau Supabase Postgres

## Struktur Penting

- `app/main.py`: entrypoint FastAPI
- `app/api/routes.py`: endpoint REST + WebSocket
- `app/services/discovery.py`: sinkronisasi CCTV Surabaya
- `app/services/vision.py`: inferensi YOLO, frame sampling, line crossing
- `app/workers/vision_worker.py`: worker vision terpisah
- `Dockerfile`: image untuk Hugging Face Space Docker
- `start-hf.sh`: menjalankan API + worker di satu container HF

## Environment Variables Utama

Lihat juga `.env.example`.

- `FRONTEND_ORIGIN`: origin frontend yang diizinkan CORS
- `PUBLIC_API_BASE_URL`: URL publik backend
- `DATABASE_URL`: PostgreSQL/Supabase atau SQLite
- `ENABLE_AI_PIPELINE`: `true` untuk mengaktifkan YOLO
- `YOLO_MODEL_PATH`: model YOLO, misalnya `yolov8n.pt`
- `VISION_SAMPLE_EVERY_N_FRAMES`: sampling HLS per N frame
- `VISION_FRAMES_PER_CAMERA`: jumlah frame yang diproses per kamera per siklus
- `VISION_MAX_CAMERAS_PER_CYCLE`: jumlah kamera online yang diproses per siklus worker

## Menjalankan Lokal

```bash
cd /workspace/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Worker terpisah:

```bash
cd /workspace/backend
source .venv/bin/activate
python -m app.workers.vision_worker
```

## Supabase / PostgreSQL

Gunakan connection string Postgres Anda:

```bash
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME
```

Contoh Supabase:

```bash
DATABASE_URL=postgresql+asyncpg://postgres.<project-ref>:<password>@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

## Frontend Ke Backend Yang Sudah Dideploy

Jika backend sudah live, misalnya:

```bash
https://username-space-name.hf.space
```

maka frontend hanya perlu:

```bash
NEXT_PUBLIC_API_BASE_URL=https://username-space-name.hf.space
```

Karena frontend membangun WebSocket dari base URL tersebut, koneksi realtime akan berubah otomatis menjadi `wss://.../ws/dashboard`.
