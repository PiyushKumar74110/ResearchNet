# ResearchMind — Full-stack AI Research Assistant

React + TypeScript + Vite frontend, FastAPI backend, LangChain, OpenAI, and Tavily.

## Architecture
- `frontend/`: research dashboard and typed API client
- `backend/app/main.py`: FastAPI application and REST/SSE endpoints
- `backend/app/services/pipeline.py`: async job orchestration and progress events
- `backend/app/agents/agents.py`: search/reader agents and writer/critic chains
- `backend/app/tools/web_tools.py`: Tavily search and safe URL scraping
- `backend/app/core/config.py`: environment configuration

## Requirements
- Python 3.11+
- Node.js 20+
- OpenAI API key
- Tavily API key

## Backend setup (PowerShell)
```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and add OPENAI_API_KEY and TAVILY_API_KEY
uvicorn app.main:app --reload
```
API docs: https://researchnet-tsn5.onrender.com/docs

## Frontend setup (new terminal)
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Open the URL Vite prints (normally http://localhost:5173).

## How it works
1. Submit a topic using `POST /api/research`.
2. The backend returns a job ID immediately.
3. The frontend subscribes to `GET /api/research/{job_id}/events` using Server-Sent Events.
4. Events update each pipeline stage and deliver the completed report and critique.
5. `GET /api/research/{job_id}` can retrieve the current state.

## Notes
- Jobs are held in process memory. Restarting the backend clears them; use Redis/PostgreSQL for durable multi-worker production deployment.
- The current orchestration runs synchronously inside a background task. For production, add a queue (e.g. Celery/Redis or ARQ), rate limits, authentication, and durable job storage.
- URL scraping includes basic protections against non-HTTP URLs and private/local IP targets, but production deployments should add DNS-rebinding-resistant egress controls.
- LLM output and web content are untrusted. Verify citations and claims before relying on reports.
