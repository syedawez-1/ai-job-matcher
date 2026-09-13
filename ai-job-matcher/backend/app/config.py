from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_storage_bucket: str = "resumes"
    gemini_api_key: str = ""
    frontend_origin: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
