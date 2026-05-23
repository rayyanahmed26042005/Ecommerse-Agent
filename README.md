# EcoAi — Smart Shopping Agent

ReAct shopping assistant with a production FastAPI backend and React frontend.

## Structure

```
EcoAi/
├── backend/          # FastAPI + LangGraph + Celery
├── frontend-repo_*/  # React (Vite) UI
├── docker-compose.yml
└── infra/            # Prometheus, etc.
```

## Run with Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 (run separately) |
| Flower | http://localhost:5555 |
| Jaeger | http://localhost:16686 |

## Run frontend locally

```bash
cd frontend-repo_u56xm4a6_uhny8m-main
cp .env.example .env
npm install
npm run dev
```

## Environment

Add your free API keys to `backend/.env`:

- `GROQ_API_KEY` — LLM orchestrator (console.groq.com)
- `TAVILY_API_KEY` — backup search (optional)
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` — community reviews (optional)

Without keys, the system runs in mock mode with curated product data and optional DuckDuckGo search.
