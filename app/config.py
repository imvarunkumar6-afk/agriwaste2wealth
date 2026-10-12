from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AgriWaste2Wealth"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./agriwaste.db"
    secret_key: str = "change-me-to-a-secure-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    upload_dir: str = "./uploads"
    model_version: str = "baseline-v1.0"
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    seed_demo_data: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
