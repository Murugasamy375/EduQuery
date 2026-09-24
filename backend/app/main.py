from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.storage.memory import db
from app.storage.seed import seed_database
from app.api.v1 import auth, tickets, dashboards

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Seed realistic in-memory database
    seed_database(db)
    print(f"[OK] EduSupport Backend Initialized! Seeded {len(db.users)} users, {len(db.tickets)} tickets.")
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS config for frontend Vite dev server & production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under /api/v1 and root shortcuts
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(tickets.router, prefix=settings.API_V1_STR)
app.include_router(dashboards.router, prefix=settings.API_V1_STR)

# Also expose without prefix to match direct requirements
app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(dashboards.router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "users_count": len(db.users),
        "tickets_count": len(db.tickets)
    }
