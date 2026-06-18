# Frontend Dashboard

Frontend ini murni klien `Next.js` dan tidak menyimpan logika backend. Semua data diambil dari backend publik melalui `NEXT_PUBLIC_API_BASE_URL`.

## Environment

```bash
cp .env.example .env.local
```

Isi `.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Jika backend sudah Anda deploy ke Hugging Face:

```bash
NEXT_PUBLIC_API_BASE_URL=https://username-space-name.hf.space
```

## Menjalankan Lokal

```bash
npm install
npm run dev
```

## Build Production

```bash
npm run lint
npm run build
```

## Cara Frontend Terhubung Ke Backend Hugging Face

Jika backend Anda live di:

```bash
https://username-space-name.hf.space
```

maka frontend akan otomatis:

- memanggil REST API ke `https://username-space-name.hf.space/api/...`
- membuka WebSocket ke `wss://username-space-name.hf.space/ws/dashboard`

Tidak perlu ubah kode komponen, cukup ubah `NEXT_PUBLIC_API_BASE_URL`.
