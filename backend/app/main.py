from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .api import telemetry, incidents, investigations, scenarios, webhooks
from .config import settings

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Incident Investigator",
    description="AI-powered causal incident investigation and root-cause analysis",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(telemetry.router)
app.include_router(incidents.router)
app.include_router(investigations.router)
app.include_router(scenarios.router)
app.include_router(webhooks.router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "demo_mode": settings.demo_mode,
        "ai_provider": settings.ai_provider,
    }


@app.get("/")
def root():
    return {
        "app": "AI Incident Investigator",
        "version": "1.0.0",
        "docs": "/api/docs",
    }
