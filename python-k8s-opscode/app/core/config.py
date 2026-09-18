"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "opscode"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Security
    secret_key: str = Field(default="change-this-secret-key-in-production", min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    api_key_header: str = "X-API-Key"

    # Database
    database_url: str = "postgresql+asyncpg://opscode:opscode@localhost:5432/opscode"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5

    # Kubernetes
    kubeconfig_path: str = Field(default="")
    kubernetes_namespace: str = "default"
    kubernetes_timeout: int = 30
    kubernetes_retry_count: int = 3
    kubernetes_retry_backoff: int = 2

    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    metrics_path: str = "/metrics"

    # Monitoring intervals (seconds)
    workload_discovery_interval: int = 60
    health_check_interval: int = 30
    incident_check_interval: int = 60

    # Health thresholds
    cpu_threshold_percent: float = 80.0
    memory_threshold_percent: float = 85.0
    restart_threshold: int = 5
    error_rate_threshold: float = 5.0
    replica_shortage_threshold: int = 1

    # Remediation
    remediation_enabled: bool = True
    remediation_dry_run: bool = True
    remediation_max_retries: int = 3
    remediation_cooldown_seconds: int = 300
    remediation_allowed_namespaces: list[str] = Field(default_factory=lambda: ["default", "staging"])
    remediation_allowed_workloads: list[str] = Field(default_factory=list)

    # Cloud
    aws_enabled: bool = False
    aws_region: str = "us-east-1"
    gcp_enabled: bool = False
    gcp_project: str = ""
    gcp_region: str = "us-central1"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = ""

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Database URL must start with postgresql:// or postgresql+asyncpg://")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
