"""Remediation action enumeration."""

from enum import Enum


class RemediationAction(str, Enum):
    """Type of remediation action."""

    RESTART = "RESTART"
    SCALE = "SCALE"
    ROLLOUT_RESTART = "ROLLOUT_RESTART"
    DELETE_POD = "DELETE_POD"
    PATCH_DEPLOYMENT = "PATCH_DEPLOYMENT"
