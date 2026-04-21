from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.database import init_db
from core.config import settings
from modules.workflows.router import router as workflows_router
from fastapi.middleware.cors import CORSMiddleware
from modules.health.router import router as health_router
from modules.ai.router import router as ai_router
from modules.execution.router import router as execution_router
from modules.demo import wfh_router
from modules.agent.router import router as agent_router  # NEW


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.project_name}...")
    await init_db()
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(workflows_router)
app.include_router(ai_router)
app.include_router(execution_router)
app.include_router(wfh_router.router)
app.include_router(agent_router)      # NEW

@app.get("/")
async def root():
    return {"message": f"Welcome to the {settings.project_name}"}