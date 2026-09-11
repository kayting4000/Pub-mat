from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    PROJECT_NAME: str = "PubMat API"
    DEBUG: bool = False


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.api", env_file_encoding="utf-8")
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.db", env_file_encoding="utf-8")
    POSTGRES_URL: str
    MONGO_URL: str
    MONGO_DB_NAME: str = "pubmat_drafts_db"


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.services", env_file_encoding="utf-8")
    GEMINI_API_KEY: str = ""
    ADMIN_USERNAME: str = "eic"
    ADMIN_EMAIL: str = "eic@pubmat.com"
    ADMIN_PASSWORD: str = "admin123"


class Settings(AppSettings, ApiSettings, DbSettings, ServiceSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.api", ".env.db", ".env.services"),
        env_file_encoding="utf-8",
    )


settings = Settings()
