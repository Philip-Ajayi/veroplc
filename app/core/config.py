from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "VeroPLC"
    APP_ENV: str = "production"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    MAX_UNROLL_CYCLES: int = 30
    SOLVER_TIMEOUT_MS: int = 10000

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
