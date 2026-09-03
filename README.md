# AI Incident Investigator

> **Observability collects the evidence. AI Incident Investigator connects the evidence.**

An AI-powered causal incident investigation and root-cause analysis system for software engineers and SREs.

---

## What it does

When an incident occurs, engineers typically have to manually correlate:
- Grafana metrics
- Application logs
- GitHub deployments
- Distributed traces

**AI Incident Investigator** automates the reasoning layer:

```
Telemetry → Correlation → Evidence → Hypothesis Evaluation → Root Cause → Recommended Action
```

It tells you **why** the incident happened, **what evidence** supports that conclusion, **what alternatives were considered**, and **what to investigate next** — while keeping the engineer in control.

---

## Quick Start (Local — No Docker)

### Backend

```bash
cd backend
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings httpx pytest pytest-asyncio python-dotenv
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/api/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at: http://localhost:3000

---

## Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

---

## Demo Flow

1. Open http://localhost:3000
2. Go to **Demo Scenarios**
3. Click **Run Scenario** on "Deployment Regression"
4. Click **Open Investigation**
5. Click **Run AI Investigation**
6. Explore: Timeline → Metrics → Hypotheses → Evidence → Actions

---

## Demo Scenarios

| Scenario | Root Cause |
|---|---|
| `deployment_regression` | DB connection pool exhaustion post-deployment |
| `database_failure` | Database server failure (no deployment) |
| `traffic_spike` | CPU/resource saturation from traffic surge |
| `dependency_failure` | External payment gateway outage |

---

## Architecture

```
Telemetry Ingestion (metrics, logs, traces, deployments)
         ↓
Temporal Correlation Engine
         ↓
Evidence Builder
         ↓
AI Investigation Engine (stub / OpenAI / Anthropic)
         ↓
Root Cause + Hypotheses + Recommended Actions
         ↓
Engineer Investigation Dashboard
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/telemetry/metrics` | Ingest metric event |
| POST | `/api/v1/telemetry/logs` | Ingest log event |
| POST | `/api/v1/telemetry/traces` | Ingest trace event |
| POST | `/api/v1/telemetry/deployments` | Ingest deployment event |
| GET | `/api/v1/incidents` | List incidents |
| POST | `/api/v1/incidents` | Create incident |
| GET | `/api/v1/incidents/{id}` | Get incident |
| POST | `/api/v1/incidents/{id}/investigate` | Trigger AI investigation |
| GET | `/api/v1/incidents/{id}/investigation` | Get investigation result |
| GET | `/api/v1/incidents/{id}/timeline` | Get event timeline |
| GET | `/api/v1/incidents/{id}/evidence` | Get evidence package |
| GET | `/api/v1/scenarios` | List demo scenarios |
| POST | `/api/v1/scenarios/{name}/run` | Load and run a scenario |

---

## AI Safety Rules

The AI investigator enforces these rules:

1. **No hallucinated telemetry** — only uses provided evidence
2. **Separates facts from inference** — labels each conclusion type
3. **Evaluates competing hypotheses** — always considers alternatives
4. **Confidence reflects evidence** — no arbitrary high confidence
5. **Never executes production changes** — recommends only

---

## Using a Real LLM

Set in your `.env`:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

Or for Anthropic:

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

The stub provider (`AI_PROVIDER=stub`) works without any key and is fully functional for demos.

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

25 tests covering: telemetry ingestion, incident CRUD, correlation engine, AI investigation engine, AI safety rules, end-to-end flow.
