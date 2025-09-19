import pytest
from fastapi import HTTPException
from app.services.key_service import KeyService
from app.services.user_service import (
    UserService,
    UserBase,
    User,
    SessionAuthData,
    allowedgroups,
    UserUpdate,
)
from tests.fixtures.db_fixtures import Repositories

test_user_base = UserBase(
    auth_id="test",
    first_name="Test",
    last_name="Test",
    admin=False,
    accepted_agreement_version="1.0",
    quota=40,
)

working_test_session_auth_data = SessionAuthData(
    auth_id="NewUser", first_name="New", last_name="User", roles=["employee"]
)
non_working_test_session_auth_data = SessionAuthData(
    auth_id="WrongUser", first_name="New", last_name="User", roles=["student"]
)


# Testing whether keys are checked correctly
@pytest.mark.asyncio
async def test_create_new_user(
    mock_repositories: Repositories, user_service: UserService
):
    all_users = await mock_repositories.user_repo.get_all_users()
    assert len(all_users) == 0
    user = await user_service.create_new_user(test_user_base)
    assert user.auth_id == "test"
    assert user.first_name == "Test"
    # now check that the user has been created in the repo
    all_users = await mock_repositories.user_repo.get_all_users()
    assert len(all_users) == 1
    new_user: User = all_users[0]
    assert new_user.auth_id == "test"
    assert new_user.first_name == "Test"
    assert new_user.last_name == "Test"
    with pytest.raises(HTTPException) as execinfo:
        user = await user_service.create_new_user(test_user_base)
    assert execinfo.value.status_code == 409


@pytest.mark.asyncio
async def test_get_user_by_id(
    normal_user: User,
    admin_user: User,
    user_service: UserService,
    mock_repositories: Repositories,
) -> None:
    user = await user_service.get_user_by_id(admin_user.id)
    assert user is not None
    assert user.first_name == admin_user.first_name
    assert user.admin
    user = await user_service.get_user_by_id(normal_user.id)
    assert user is not None
    assert user.last_name == normal_user.last_name
    assert user.accepted_agreement_version == normal_user.accepted_agreement_version
    assert user.id == normal_user.id
    # To allow different types of IDs being used
    user = await user_service.get_user_by_id("1")
    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_auth_id(
    normal_user: User,
    admin_user: User,
    user_service: UserService,
    mock_repositories: Repositories,
) -> None:
    user = await user_service.get_user_by_auth_id(admin_user.auth_id)
    assert user is not None
    assert user.first_name == admin_user.first_name
    assert user.admin
    user = await user_service.get_user_by_auth_id(normal_user.auth_id)
    assert user is not None
    assert user.last_name == normal_user.last_name
    assert user.accepted_agreement_version == normal_user.accepted_agreement_version
    assert user.id == normal_user.id
    user = await user_service.get_user_by_auth_id("Someone")
    assert user is None


@pytest.mark.asyncio
async def test_get_or_create_user_from_auth_data(
    normal_user: User,
    admin_user: User,
    user_service: UserService,
    mock_repositories: Repositories,
) -> None:

    user = await user_service.get_or_create_user_from_auth_data(
        working_test_session_auth_data
    )
    assert user.first_name == working_test_session_auth_data.first_name
    assert user.last_name == working_test_session_auth_data.last_name
    assert user.admin == False
    user = await user_service.get_or_create_user_from_auth_data(
        SessionAuthData(
            auth_id=admin_user.auth_id,
            first_name=admin_user.first_name,
            last_name=admin_user.last_name,
            roles=[allowedgroups[0]],
        )
    )
    assert user.first_name == admin_user.first_name
    assert user.last_name == admin_user.last_name
    assert user.admin
    with pytest.raises(HTTPException) as execinfo:
        user = await user_service.get_or_create_user_from_auth_data(
            SessionAuthData(
                auth_id=admin_user.auth_id,
                first_name=admin_user.first_name,
                last_name=admin_user.last_name,
                roles=["student"],
            )
        )
    assert execinfo.value.status_code == 403
    user: User = await user_service.get_or_create_user_from_auth_data(
        SessionAuthData(
            auth_id=admin_user.auth_id,
            first_name="NewFirst",
            last_name="NewLast",
            roles=[allowedgroups[0]],
        )
    )
    assert user.first_name == "NewFirst"
    assert user.last_name == "NewLast"
    assert user.admin
    all_users = await mock_repositories.user_repo.get_all_users()
    print(all_users)
    assert len(all_users) == 3

    user = await user_service.get_or_create_user_from_auth_data(
        SessionAuthData(
            auth_id="NewUser",
            first_name="Relevant",
            last_name="Very Relevant",
            roles=[allowedgroups[0]],
        )
    )
    assert user is not None
    assert user.last_name == "Very Relevant"
    assert user.accepted_agreement_version == "0.0"
    assert not user.admin
    user2 = await user_service.get_user_by_auth_id("NewUser")
    assert user2 is not None
    assert user2.last_name == "Very Relevant"
    assert user2.accepted_agreement_version == "0.0"
    assert len(await mock_repositories.user_repo.get_all_users()) == 3


@pytest.mark.asyncio
@pytest.mark.usefixtures("basic_users")
async def test_get_all_users(
    user_service: UserService, mock_repositories: Repositories
) -> None:

    assert len(await user_service.get_all_users()) == 2
    # We can test, that all elements are ok, but I think that's ok here.


@pytest.mark.asyncio
async def test_update_user(
    user_service: UserService, admin_user: User, mock_repositories: Repositories
) -> None:
    # We can test, that all elements are ok, but I think that's ok here.
    update = UserUpdate(accepted_agreement_version="3.0", first_name="None")
    await user_service.update_user(admin_user.id, update)
    user = await user_service.get_user_by_id(admin_user.id)
    assert user is not None
    assert user.admin
    assert user.accepted_agreement_version == "3.0"
    assert user.first_name == "None"
    assert user.last_name == admin_user.last_name
    user_update = UserUpdate(last_name="New")
    await user_service.update_user(admin_user.id, user_update)
    user = await user_service.get_user_by_id(admin_user.id)
    assert user is not None
    assert user.last_name == "New"
    assert user.first_name == "None"
    assert user.accepted_agreement_version == "3.0"


@pytest.mark.asyncio
@pytest.mark.usefixtures("basic_users")
async def test_delete_user(
    user_service: UserService, admin_user: User, mock_repositories: Repositories
) -> None:

    assert len(mock_repositories.user_repo.users) == 2
    await user_service.delete_user(admin_user.id)
    assert len(mock_repositories.user_repo.users) == 1
    assert await user_service.get_user_by_id(admin_user.id) is None
