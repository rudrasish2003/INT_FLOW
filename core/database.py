from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from core.config import settings
from modules.workflows.schemas import WorkflowDocument

# We will populate this array in Phase 2 when we create our MongoDB models
DOCUMENT_MODELS = [WorkflowDocument] 

async def init_db():
    """
    Initialize the MongoDB connection and Beanie ODM.
    """
    client = AsyncIOMotorClient(settings.mongodb_uri)
    
    # Extract the database name from the URI or default to 'workflow_db'
    db = client.get_default_database("workflow_db")
    
    await init_beanie(database=db, document_models=DOCUMENT_MODELS)
    return client

async def ping_db() -> bool:
    """
    Ping the database to check if the connection is alive.
    """
    try:
        client = AsyncIOMotorClient(settings.mongodb_uri)
        await client.admin.command('ping')
        return True
    except Exception:
        return False