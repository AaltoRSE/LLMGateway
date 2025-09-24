"""
Agreement helpers
"""

from app.config import app_configuration


def check_agreement_version(agreement_version: str) -> bool:
    """
    Check a agreement version against the greement version indicated in the app.
    """
    return agreement_version == app_configuration.current_agreement_version
