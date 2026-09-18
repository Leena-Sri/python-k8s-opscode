"""Incident type enumeration."""

from enum import Enum


class IncidentType(str, Enum):
    """Type of incident."""

    POD_CRASH_LOOP = "POD_CRASH_LOOP"
    HIGH_CPU = "HIGH_CPU"
    HIGH_MEMORY = "HIGH_MEMORY"
    REPLICA_SHORTAGE = "REPLICA_SHORTAGE"
    HIGH_ERROR_RATE = "HIGH_ERROR_RATE"
    HIGH_LATENCY = "HIGH_LATENCY"
    DEPLOYMENT_FAILURE = "DEPLOYMENT_FAILURE"
    NETWORK_ISSUE = "NETWORK_ISSUE"
