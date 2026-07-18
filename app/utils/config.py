"""
Job Hunter AI - Configurações Globais da Aplicação
Gerencia o carregamento, validação e tipagem estrita das variáveis de ambiente.
"""

from functools import lru_cache
from typing import Literal
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Configurações do ciclo de vida e carregamento do Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Core Application Settings
    APP_ENV: Literal["development", "production", "testing"] = "development"
    APP_DEBUG: bool = True
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # PostgreSQL Database Connection
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Artificial Intelligence Providers
    OPENAI_API_KEY: str = "dummy-key"
    OPENAI_MODEL: str = "gpt-4o"
    
    GEMINI_API_KEY: str = "dummy-key"
    GEMINI_MODEL: str = "gemini-1.5-pro"
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    
    DEFAULT_AI_PROVIDER: Literal["openai", "gemini", "ollama"] = "openai"

    # Notification Services
    NOTIFICATION_PROVIDER: Literal["twilio", "zenvia"] = "twilio"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    USER_TARGET_PHONE: str = ""

    # File Upload Specifications
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_EXTENSIONS: str = "pdf"

    # Automation & Crawlers
    BROWSER_HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT_MS: int = 30000

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Gera a URL de conexão síncrona usada pelo Alembic e utilitários."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @computed_field
    @property
    def async_database_url(self) -> str:
        """Gera a URL de conexão assíncrona usada pela camada de Repositórios."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


@lru_cache
def get_settings() -> Settings:
    """
    Retorna uma instância Singleton das configurações da aplicação.
    Usa caching do lru_cache para evitar releituras desnecessárias de disco.
    """
    return Settings()