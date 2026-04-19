from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    project_name: str = "Workflow Builder API"
    mongodb_uri: str
    openai_api_key: str
    pynode_url: str = "http://localhost:5000"   # ADD THIS
    pynode_timeout: int = 30                     # ADD THIS

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()