"""Remediation status enumeration."""

from enum import Enum


class RemediationStatus(str, Enum):
    """Status of a remediation action."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
