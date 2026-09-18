"""Incident status enumeration."""

from enum import Enum


class IncidentStatus(str, Enum):
    """Status of an incident."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
