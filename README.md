# AI Meeting Prep Agent — Backend API

This repository contains the production-ready, modular MVP backend for the **AI Meeting Preparation Agent (AURA)**. The system automatically syncs calendar events from Google Calendar and generates comprehensive preparation briefings (including attendee details, company news, Gmail thread contexts, talking points, and opportunities) using a state-graph workflow orchestrated via LangGraph, OpenAI GPT-4o, and Pinecone vector database.

---

## Technical Architecture

The application is built in Python using **FastAPI** and is organized around clean, modular architecture:

```
app/
  ├── main.py             # Entrypoint and app initialization
  ├── config.py           # Configuration management via Pydantic Settings
  ├── database.py         # SQLAlchemy engine and session provider
  ├── core/               # Security, password hashing, symmetric Fernet encryption
  ├── models/             # SQLAlchemy ORM schemas (PostgreSQL)
  ├── schemas/            # Pydantic validation schemas
  ├── api/                # Router controllers (Auth, Dashboard, Meetings, Briefs, Copilot, Transcripts)
  └── services/           # Services layer (OAuth, Gmail/Calendar API, OpenAI, Pinecone, LangGraph Agent)
```

### Core Technologies
- **LangGraph**: Compiles the preparation workflow as a StateGraph containing 5 sequential nodes: Metadata parsing, Gmail thread collection, Company research (scraping & SerpAPI), Context RAG aggregation (with Pinecone vectors), and GPT-4o Brief compilation.
- **Pinecone**: Acts as the semantic index. Emails, past briefs, and transcript chunks are embedded using OpenAI `text-embedding-3-small` and indexed with workspace isolation keys.
- **Symmetric Encryption**: Access and refresh tokens for Google accounts are encrypted using AES-GCM Fernet (`cryptography` library) before being written to PostgreSQL.
- **Redis**: Caches API results and external scrapes, avoiding API rate limiting.
- **SQLAlchemy (PostgreSQL)**: Handles the 10 core tables: `users`, `workspaces`, `oauth_connections`, `meetings`, `meeting_attendees`, `meeting_briefs`, `meeting_transcripts`, `action_items`, `companies`, `audit_logs`.

---

## Getting Started

### 1. Prerequisites
- Python 3.12+
- Docker and Docker Compose
- PostgreSQL and Redis (if running locally without Docker)

### 2. Configuration Setup
Create a `.env` file in the root directory based on the `.env.example` template:
```bash
cp .env.example .env
```
Ensure you provide your Google OAuth credentials, OpenAI API key, and Pinecone endpoints.

### 3. Local Development Run
Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Launch the FastAPI application locally:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Visit the interactive API documentation at: **`http://localhost:8000/docs`**

### 4. Running with Docker Compose
Run the entire backend stack (API, PostgreSQL, Redis) with a single command:
```bash
docker-compose up --build
```
This automatically boots up the services, runs health checks on PostgreSQL, and launches the uvicorn API. Database tables are generated automatically on startup.

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **POST** | `/auth/register` | Register a new user and create their default workspace | No |
| **POST** | `/auth/login` | Login with email/password to retrieve JWT token | No |
| **POST** | `/auth/google` | Exchange Google OAuth code for JWT token & connect account | No |
| **GET** | `/dashboard` | Retrieve synced dashboard statistics and calendar events | Yes |
| **GET** | `/meetings` | List all synced meetings for the current workspace | Yes |
| **GET** | `/meetings/{id}` | Get specific meeting details | Yes |
| **POST** | `/meetings/{id}/prepare` | Trigger the LangGraph agent preparation workflow | Yes |
| **GET** | `/briefs/{id}` | Fetch the prepared briefing dossier for a meeting | Yes |
| **POST** | `/copilot/start` | Retrieve low-latency talking points for dashboard overlays | Yes |
| **POST** | `/transcripts/upload` | Process meeting transcript and generate action items | Yes |

---

## Testing

The test suite runs against an in-memory SQLite database and mocks external API boundaries. To execute tests:
```bash
python -m pytest
```
Tests are located in the `tests/` folder:
- `tests/conftest.py` — Database fixtures and overrides
- `tests/test_auth.py` — Auth flows (login, register)
- `tests/test_meetings.py` — Calendar sync, briefings, and transcript uploads

---

## Production Deployment Guide

This guide details how to deploy the full-stack application properly using **Vercel** for the frontend and **Railway** for the backend.

### 1. Backend Deployment (Railway)

Railway compiles the Python backend and connects it to PostgreSQL and Redis.

1. **Create a New Project on Railway**: Import your repository.
2. **Configure Root Directory**: In settings, set the **Root Directory** to `backend`.
3. **Provision Database & Redis**:
   - Add a **PostgreSQL** database service to your Railway project.
   - Add a **Redis** database service to your Railway project.
   - Railway will automatically inject `DATABASE_URL` and `REDIS_URL` env variables.
4. **Configure Environment Variables**:
   - `JWT_SECRET_KEY`: Set to a strong random string (e.g. `openssl rand -hex 32`).
   - `JWT_ALGORITHM`: `HS256`.
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `1440`.
   - `TOKEN_ENCRYPTION_KEY`: A 32-byte base64-encoded key for credential encryption (e.g., `wT-k0X65tS9v8P-1aR6-7c_4Z9u-T1YV8Wv1bX2z3E=`).
   - `OPENAI_API_KEY`: Your OpenAI credential.
   - `SERPAPI_API_KEY`: Your SerpAPI credential.
   - `PINECONE_API_KEY`: Your Pinecone credential.
   - `PINECONE_INDEX_NAME`: Your Pinecone index name.
   - `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID.
   - `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret.
   - `GOOGLE_REDIRECT_URI`: Set to `https://<your-backend-railway-url>.railway.app/api/v1/auth/google/callback`.
5. **Start Command**: Railway will auto-detect the `Dockerfile` in `backend/` and build it. Alternatively, it can build via Nixpacks running:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

---

### 2. Frontend Deployment (Vercel)

Vercel serves the static files at maximum performance with zero serverless function configurations.

1. **Deploy Repository on Vercel**: Import your repository.
2. **Prevent Serverless Function Crashes**: The repository contains a root [vercel.json](file:///c:/Users/USER/OneDrive/Desktop/Meeting_prep/vercel.json) that automatically configures Vercel to only build the static files in the `frontend` folder and ignore `backend/`. This prevents the "This Serverless Function has crashed" error.
3. **Configure the Backend API Connection**:
   - Copy `frontend/config.json.example` to `frontend/config.json` inside the repository.
   - Edit the `API_BASE` key to point to your Railway deployment:
     ```json
     {
       "API_BASE": "https://<your-backend-railway-url>.railway.app/api/v1"
     }
     ```
   - Commit and push to deploy. The frontend will dynamically fetch this configuration on startup to route API calls directly to Railway under full CORS authorization.
