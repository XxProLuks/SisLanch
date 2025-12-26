"""
LANCH - Sistema de Lanchonete Hospitalar
Configuration settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from typing import List
import os
import secrets


class Settings(BaseSettings):
    # Application
    APP_NAME: str = Field(
        default="LANCH - Sistema de Lanchonete Hospitalar",
        description="Application name"
    )
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode - NEVER True in production!")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///../database/lanch.db",
        description="Database connection URL"
    )
    
    # Security - SECRET_KEY is REQUIRED
    SECRET_KEY: str = Field(
        ...,  # Required, no default
        min_length=32,
        description="Secret key for JWT - MUST be set via environment variable"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=480,  # 8 hours
        description="Token expiration time in minutes"
    )
    
    # CORS - Allowed Origins
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Business Rules
    DEFAULT_EMPLOYEE_LIMIT: float = Field(
        default=500.00,
        description="Default monthly limit for employees"
    )
    
    # Rate Limiting
    LOGIN_RATE_LIMIT: int = Field(
        default=5,
        description="Maximum login attempts per period"
    )
    RATE_LIMIT_PERIOD: int = Field(
        default=60,
        description="Rate limit period in seconds"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_DIR: str = Field(default="logs", description="Log directory")
    LOG_MAX_BYTES: int = Field(default=10485760, description="Max log file size (10MB)")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of log backups")
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate SECRET_KEY is not the default example value"""
        if 'your-secret-key-here' in v.lower() or 'change-this' in v.lower():
            raise ValueError(
                "SECRET_KEY must be changed from the example value! "
                "Generate a new one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    try:
        return Settings()
    except Exception as e:
        print(f"\n❌ ERRO DE CONFIGURAÇÃO: {e}")
        print("\n💡 Dica: Certifique-se de que o arquivo .env existe e contém todas as variáveis necessárias.")
        print("   Você pode copiar .env.example para .env e preencher os valores.\n")
        raise


settings = get_settings()
