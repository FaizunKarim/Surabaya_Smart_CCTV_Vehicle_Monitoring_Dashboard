# Surabaya Smart CCTV Vehicle Monitoring

Repositori ini sekarang dipisah jelas menjadi:

- `frontend/`: dashboard murni `Next.js`
- `backend/`: service `FastAPI` yang dapat dideploy terpisah ke Hugging Face atau VPS

## Arsitektur

### Frontend

- hanya mengonsumsi REST API dan WebSocket dari backend
- dikonfigurasi lewat `NEXT_PUBLIC_API_BASE_URL`

### Backend

- sinkronisasi katalog CCTV Surabaya dari sumber asli
- menyimpan metadata CCTV ke database
- menyediakan summary, detail analytics, histori, dan websocket
- menjalankan worker vision terpisah untuk inferensi YOLO
- mendukung PostgreSQL / Supabase

## Pipeline Vision Yang Ditambahkan

- frame sampling HLS berbasis `VISION_SAMPLE_EVERY_N_FRAMES`
- deteksi kendaraan dengan `YOLO`
- tracking dengan `supervision.ByteTrack`
- line-crossing counter dengan `supervision.LineZone`
- histori analytics per CCTV di database
- event crossing kendaraan tersimpan untuk analisis lanjutan

## Deploy Terpisah

### Backend ke Hugging Face

Lihat:

- [backend/README.md](file:///workspace/backend/README.md)
- [backend/HUGGINGFACE.md](file:///workspace/backend/HUGGINGFACE.md)

### Frontend ke Vercel / Hosting Lain

Set environment berikut:

```bash
NEXT_PUBLIC_API_BASE_URL=https://username-space-name.hf.space
```

Frontend otomatis akan memakai:

- REST: `https://username-space-name.hf.space/api/...`
- WebSocket: `wss://username-space-name.hf.space/ws/dashboard`

## Production Compose

Untuk deployment production berbasis Docker Compose backend-only, tersedia:

- [docker-compose.production.yml](file:///workspace/docker-compose.production.yml)
- [default.conf](file:///workspace/backend/infra/nginx/default.conf)

Service yang disediakan:

- `postgres`
- `backend-api`
- `vision-worker`
- `nginx`

## Menjalankan Lokal Singkat

### Backend

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

### Frontend

```bash
cd /workspace/frontend
cp .env.example .env.local
npm install
npm run dev
```
