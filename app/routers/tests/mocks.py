from app.services.user_service import UserService
from app.models.user import User
from app.security.auth import BackendUser
from starlette.authentication import AuthCredentials


async def user_callable(arg1, arg2, username: str, isadmin: bool) -> BackendUser:
    return AuthCredentials(["authenticated"]), BackendUser(
        username=username, userdata={}, roles=[], isadmin=isadmin, agreement_ok=True
    )


def mockAdminUserAuth(username: str = "Admin"):
    user_service = UserService()
    user_service.create_new_user(
        User(auth_id=username, first_name="test", last_name="test", admin=True)
    )

    # create a lambda function that returns a Valid backend user.
    return lambda arg1, arg2: user_callable(arg1, arg2, username, True)


def mockNormalUserAuth(username: str = "User"):
    user_service = UserService()
    user_service.create_new_user(
        User(auth_id=username, first_name="test", last_name="test", admin=False)
    )
    # create a lambda function that returns a Valid backend user.
    return lambda arg1, arg2: user_callable(arg1, arg2, username, False)
