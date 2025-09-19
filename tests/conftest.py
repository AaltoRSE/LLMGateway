"""Overall test configuration module"""

# pylint: disable=unused-import
# pylint: disable=wrong-import-position
import os

os.environ["SQLALCHEMY_DATABASE_URL"] = (
    "postgresql+psycopg://postgres:bogus@localhost/aaltoai"
)

from tests.fixtures.user_fixtures import normal_user, admin_user
from tests.fixtures.db_fixtures import mock_repositories
