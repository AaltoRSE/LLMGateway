import pytest
from fastapi import HTTPException
from app.services.key_service import KeyService
from app.services.user_service import UserService
import gateway.app.dbs.redis.redis
from tests.fixtures.db_fixtures import Repositories
from app.schemas.key_schema import APIKey
from app.schemas.user_schema import User


def create_test_user(username="TestUser"):
    return User(auth_id=username, first_name="Test", last_name="User")


async def test_init_keys(
    mock_repositories: Repositories, key_service: KeyService, user_key: APIKey
):

    # Retrieves the keys from the mongo db
    current_keys = await key_service.list_keys()
    assert len(current_keys) == 1
    # We will add an inactive key to the db.
    inactive_key = await mock_repositories.key_repo.create_api_key(
        name="inactive", user_id=user_key.user_id
    )
    await mock_repositories.key_repo.deactivate_key(inactive_key)
    current_keys = await key_service.list_keys()
    # This will list the inactive key
    assert len(current_keys) == 2
    key_not_in_redis = await key_service.get_user_key_if_active(user_key.key)
    assert key_not_in_redis is None
    await key_service.init_keys()
    # The active key works now
    key = await key_service.get_user_key_if_active(user_key.key)
    assert key is not None
    assert key.active
    assert key.name
    inactive = key_service.get_user_key_if_active(inactive_key.key)
    # The inactive still doesn't
    assert inactive is None


# Testing whether keys are checked correctly
async def test_check_key(key_service: KeyService, normal_user: User, admin_user: User):
    normal_key = await key_service.create_key(name="test", user_id=normal_user.id)
    admin_key = await key_service.create_key(name="test", user_id=admin_user.id)

    a_key = await key_service.get_user_key_if_active(normal_key.key)
    assert a_key.user_id == normal_user.id
    b_key = await key_service.get_user_key_if_active(admin_key.key)
    assert b_key.user_id == admin_user.id
    res = await key_service.get_user_key_if_active("efg")
    assert res is None


async def test_delete_key_for_user(
    mock_respositories: Repositories,
    key_service: KeyService,
    normal_user: User,
    admin_user: User,
):
    new_key = await key_service.create_key(user_id=normal_user.id, name="NewKey")
    assert len(mock_respositories.key_repo.__class__.keys.values()) == 1
    with pytest.raises(HTTPException) as execinfo:
        await key_service.delete_key_for_user(new_key.key, admin_user.id)
    assert execinfo.value.status_code == 400
    key = await key_service.get_user_key_if_active(new_key.key)
    assert key is not None
    # now delete it for real
    await key_service.delete_key_for_user(new_key.key, normal_user.id)
    key = await key_service.get_user_key_if_active(new_key.key)
    assert key is None
    assert len(mock_respositories.key_repo.__class__.keys.values()) == 1
    assert mock_respositories.key_repo.__class__.keys[new_key.key].active == False


async def test_delete_key(
    mock_respositories: Repositories,
    key_service: KeyService,
    normal_user: User,
    admin_user: User,
):
    new_key = await key_service.create_key(user_id=normal_user.id, name="NewKey")
    assert len(mock_respositories.key_repo.__class__.keys.values()) == 1
    key = await key_service.get_user_key_if_active(new_key.key)
    assert key is not None
    # now delete it for real
    await key_service.delete_key(new_key.key)
    key = await key_service.get_user_key_if_active(new_key.key)
    assert key is None
    assert len(mock_respositories.key_repo.__class__.keys.values()) == 1
    assert mock_respositories.key_repo.__class__.keys[new_key.key].active == False
