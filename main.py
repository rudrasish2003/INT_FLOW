from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.database import init_db
from core.config import settings
from modules.workflows.router import router as workflows_router
from fastapi.middleware.cors import CORSMiddleware


# Import routers
from modules.health.router import router as health_router
# Add this import
from modules.ai.router import router as ai_router

# Add this below your workflows_router registration
 

from modules.execution.router import router as execution_router
from modules.demo import wfh_router
# Then app.include_router(wfh_router.router) would work.


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    print(f"Starting {settings.project_name}...")
    await init_db()
    yield
    # Shutdown logic goes here if needed

app = FastAPI(
    title=settings.project_name,
    lifespan=lifespan
)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
]

# 3. Add the middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)
# Register Modules
app.include_router(health_router)

@app.get("/")
async def root():
    return {"message": f"Welcome to the {settings.project_name}"}

app.include_router(workflows_router)
app.include_router(ai_router)
 
app.include_router(execution_router)
app.include_router(wfh_router.router)