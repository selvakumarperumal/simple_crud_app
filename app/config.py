from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/crud_db"
    app_name: str = "Simple CRUD App"
    debug: bool = False

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
