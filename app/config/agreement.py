import os


def check_agreement_version(agreement_version: str):
    return agreement_version == os.environ.get("AGREEMENT_VERSION", "1.0")
