from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Intelligent Scheduler"
    DEBUG: bool = False
    DATABASE_URL: str
    REDIS_URL: str
    OPENAI_API_KEY: str
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()