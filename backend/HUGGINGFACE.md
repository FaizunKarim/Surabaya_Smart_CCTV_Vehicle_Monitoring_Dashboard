# Hugging Face Space Deployment

Dokumen ini menjelaskan cara deploy backend ke Hugging Face Space berbasis Docker.

## Kenapa Backend Dipisah?

- Frontend tetap murni dan cukup mengonsumsi API publik
- Backend dapat diskalakan terpisah
- Worker vision, database, dan inferensi YOLO tidak membebani aplikasi frontend

## Tipe Space

Gunakan **Docker Space**, bukan Gradio/Streamlit.

## File Yang Sudah Disiapkan

- `Dockerfile`
- `start-hf.sh`
- `start-api.sh`
- `start-worker.sh`

`start-hf.sh` menjalankan worker vision di background lalu menyalakan FastAPI pada port `7860`, yang merupakan default untuk Hugging Face Space.

## Langkah Deploy

1. Buat Space baru di Hugging Face dengan tipe **Docker**
2. Upload seluruh isi folder `backend/`
3. Tambahkan secrets / variables berikut di Hugging Face:

```bash
FRONTEND_ORIGIN=https://frontend-anda.com
PUBLIC_API_BASE_URL=https://username-space-name.hf.space
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB
ENABLE_AI_PIPELINE=true
YOLO_MODEL_PATH=yolov8n.pt
VISION_SAMPLE_EVERY_N_FRAMES=12
VISION_FRAMES_PER_CAMERA=60
VISION_MAX_CAMERAS_PER_CYCLE=4
HF_SPACE_MODE=true
```

## Rekomendasi Database

Jangan menaruh database lokal di Hugging Face container. Gunakan:

- Supabase Postgres
- Neon Postgres
- Managed PostgreSQL lain

## Rekomendasi Runtime

- CPU Space masih bisa berjalan untuk model kecil seperti `yolov8n`, tetapi throughput rendah
- Untuk analytics lebih stabil, gunakan GPU Space atau pindahkan worker vision ke VPS

## Endpoint Setelah Live

Misal URL Space:

```bash
https://username-space-name.hf.space
```

Endpoint penting:

- `GET /api/health`
- `GET /api/cctvs`
- `GET /api/dashboard/summary`
- `GET /api/cctvs/{cctv_id}/analytics`
- `GET /api/cctvs/{cctv_id}/history`
- `WS /ws/dashboard`

## Menghubungkan Frontend

Di frontend, set:

```bash
NEXT_PUBLIC_API_BASE_URL=https://username-space-name.hf.space
```

Lalu deploy frontend Anda seperti biasa. Frontend akan:

- fetch REST ke `https://username-space-name.hf.space/api/...`
- membuka WebSocket ke `wss://username-space-name.hf.space/ws/dashboard`

## Catatan Penting

- Hugging Face Docker Space hanya satu container, jadi worker “terpisah” di sini berjalan sebagai proses background di container yang sama
- Untuk production traffic tinggi, pakai deployment VPS terpisah dengan `docker-compose.production.yml` agar API, worker, dan reverse proxy benar-benar dipisah
