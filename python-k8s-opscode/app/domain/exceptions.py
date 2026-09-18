"""Custom exceptions for the application."""


class OpscodeException(Exception):
    """Base exception for Opscode errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class WorkloadNotFoundError(OpscodeException):
    """Raised when a workload is not found."""

    pass


class IncidentNotFoundError(OpscodeException):
    """Raised when an incident is not found."""

    pass


class KubernetesConnectionError(OpscodeException):
    """Raised when Kubernetes connection fails."""

    pass


class DatabaseError(OpscodeException):
    """Raised when database operation fails."""

    pass


class RedisError(OpscodeException):
    """Raised when Redis operation fails."""

    pass


class RemediationError(OpscodeException):
    """Raised when remediation action fails."""

    pass


class ValidationError(OpscodeException):
    """Raised when validation fails."""

    pass


class ConfigurationError(OpscodeException):
    """Raised when configuration is invalid."""

    pass
