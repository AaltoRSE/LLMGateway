from pytest_mock_resources.container.mongo import MongoConfig
import pytest


@pytest.fixture(scope="session")
def pmr_mongo_config():
    return MongoConfig(image="mongo:7.0.4")
