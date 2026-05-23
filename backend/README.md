# EcoAi Smart Shopping Backend

Production-grade FastAPI + LangGraph ReAct shopping agent with Celery async processing.

## Architecture

- **FastAPI** — REST API, middleware (rate limit, idempotency, logging, CORS)
- **LangGraph** — ReAct loop: plan → search → details → reviews → synthesize
- **Celery + Redis** — Background AI workloads (`high_priority` / `low_priority` queues)
- **PostgreSQL** — Users, conversations, task metadata
- **Redis** — Cache (L2), rate limits, idempotency, task status
- **Qdrant** — Vector memory (ready for embeddings/RAG extension)

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- API: http://localhost:8000/docs
- Flower: http://localhost:5555
- Jaeger: http://localhost:16686

## Local development (no Docker)

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Terminal 1 — API
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Celery worker (optional for async chat)
celery -A app.workers.celery_app worker -Q high_priority,low_priority -l info
```

Set `GROQ_API_KEY` in `.env` for real LLM reasoning. Without keys, the agent runs in **mock mode** with DuckDuckGo search when available.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health message |
| GET | `/test` | PostgreSQL status |
| GET | `/health` | Redis + circuit breakers |
| GET | `/api/trending` | Sidebar trending |
| GET | `/api/essentials` | Daily essentials |
| GET | `/api/picks/{user_id}` | Personal picks |
| POST | `/api/chat` | Start async agent (returns `task_id`) |
| POST | `/api/chat?sync=true` | Run agent synchronously |
| GET | `/api/chat/tasks/{task_id}` | Poll task result |

## Frontend

Point the React app at the API:

```env
VITE_BACKEND_URL=http://localhost:8000
```
