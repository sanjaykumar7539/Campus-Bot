# Ask EGSPEC — React Frontend

Original React (Vite) chatbot UI for **E.G.S. Pillay Engineering College**, using official brand colors and logo.

## Stack

- React 18 + Vite
- Official EGSPEC logo & magenta/navy palette
- Streams answers from the existing CampusMind FastAPI backend (`/api/v1/chat/stream`)
- Voice input via Web Speech API (en-IN)

## Run (development)

1. Start the Python backend (project root):

```bash
python main.py
```

2. In another terminal:

```bash
cd frontend-react
npm install
npm run dev
```

Open **http://127.0.0.1:5173** — Vite proxies `/api` to `http://127.0.0.1:8000`.

## Production build

```bash
cd frontend-react
npm install
npm run build
```

Output is in `frontend-react/dist/`. You can serve it with any static host, or mount `dist` from FastAPI instead of the classic `frontend/` folder.

## Features

- Attractive landing with quick-topic cards
- Streaming chat with source citations
- Quick replies
- Voice input button
- Responsive layout
- Official EGSPEC branding
