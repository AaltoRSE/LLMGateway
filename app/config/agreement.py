import os
from app.config import app_configuration


def check_agreement_version(agreement_version: str):
    return agreement_version == app_configuration.current_agreement_version
