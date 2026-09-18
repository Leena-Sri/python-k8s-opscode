"""Incident severity enumeration."""

from enum import Enum


class IncidentSeverity(str, Enum):
    """Severity level of an incident."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
