# Automated Venture Capital (VC) Investment Analyst Monorepo

Welcome to the **Automated VC Investment Analyst Monorepo**! This repository is organized as a production-grade, Dockerized microservices application split into distinct service packages.

## Architecture Overview

This monorepo separates our core system concerns into three independent containers working inside a private Docker bridge network:

```
                  ┌──────────────────────┐
                  │  Client Browser UI   │
                  │  (React / Vite)      │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼ (1. Get Presigned URL)          ▼ (2. PUT Upload File Binary)
┌───────────────────────┐            ┌───────────────────────┐
│    Backend Gateway    │            │     MinIO Storage     │
│       (FastAPI)       │            │  (S3-Compatible Object│
└──────────┬────────────┘            └──────────┬────────────┘
           │ (3. POST Form Payload              │
           │     w/ File Path)                  │
           ▼                                    │ (4. Fetch File Bytes)
┌───────────────────────┐                       │
│    Analyst Engine     │◄──────────────────────┘
│ (FastAPI & LangGraph) │
└───────────────────────┘
```

---

## Repository Structure

```
.
├── apps/
│   ├── ui/               # React + Vite frontend served via Nginx (Port 3000)
│   ├── backend/          # REST API Gateway (Port 8000)
│   └── analyst/          # LangGraph VC analysis orchestrator service (Port 8001)
├── docker-compose.yml    # Root orchestration config for containers & local MinIO
└── README.md             # This guide
```

---

## Isolated Dependencies

Each application is self-contained with no shared global configurations or root package managers:
* **`apps/ui`**: Node-based package using `package.json` for React/Vite dependencies.
* **`apps/backend`**: Python-based package using `pyproject.toml` managing FastAPI gateway packages (e.g. `boto3`, `httpx`).
* **`apps/analyst`**: Python-based package using `pyproject.toml` managing LangGraph, LangChain, OpenAI, and extraction libraries (e.g. `pymupdf`, `python-pptx`).

---

## Local Development & Setup

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 1. Configure Environment Variables
Create a `.env` file inside the `apps/analyst/` directory to configure your LLM provider api keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Boot the entire stack or individual services
From the root of the repository, execute the following command to build and start all containers in the background:
```bash
docker compose up --build -d
```
Alternatively, if you want to boot and run the **Analyst Engine** and its core persistence/web research dependencies only:
```bash
docker compose up --build -d analyst postgres minio searxng
```

### 3. Verify Container Endpoints
Once the build is complete, you can access the services on your local machine:
* **Frontend Web App UI**: http://localhost:3000
* **Backend API Gateway Docs (Swagger)**: http://localhost:8000/docs
* **Analyst Agent API Docs (Swagger)**: http://localhost:8001/docs
* **PostgreSQL State Saver Database**: `localhost:5432` (Credentials: `postgres` / `postgrespassword`, DB name: `vc_analyst`)
* **MinIO Object Storage Console**: http://localhost:9001 (Credentials: `minioadmin` / `minioadminpassword`)
* **Searxng Local Search Engine**: http://localhost:8080

---

## Output Persistence & Report Storage

All compiled PDF reports generated during the agentic IC review process are saved inside your host workspace directory in real-time:
- **Pattern A (Web-Sleek PDF via Playwright)**: `./outputs/{run_id}/memo_web.pdf`
- **Pattern B (Institutional Typst PDF)**: `./outputs/{run_id}/memo_typst.pdf`

These compiled reports are synced between the container environment and your local machine via a mounted Docker volume, ensuring data persistence and easy local access after container shutdown.

---

## The Secure Direct-to-Storage Upload Flow

1. **Intake Form**: When a user fills out details on the UI and adds a pitch deck PDF, the UI contacts the **Backend Gateway** (Port 8000) to request a temporary, short-lived S3 Upload URL.
2. **Direct Upload**: The Backend uses its external credentials to sign a URL and returns it. The UI then uploads the raw binary file **directly** to the **MinIO Object Storage** (Port 9000). The main Python servers never consume network overhead for file bytes.
3. **Execution**: The UI submits the structured JSON payload containing the MinIO key (`file_path`) and other details to the Backend, which forwards it to the **Analyst Engine** (Port 8001). The Analyst pulls the PDF from MinIO internally, executes the LangGraph agent pipeline, and returns the result.