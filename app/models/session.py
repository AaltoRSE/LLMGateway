SESSION_DATA_FIELD = "backend_session"


class HTTPSession:
    def __init__(
        self, key: str, user: str, roles: list, ip: str, data: dict, admin: bool
    ):
        self.key = key
        self.ip = ip
        self.user = user
        self.roles = roles
        self.data = data
        self.admin = admin

    def to_dict(self):
        return {
            "key": self.key,
            "ip": self.ip,
            "user": self.user,
            "roles": self.roles,
            "data": self.data,
            "admin": self.admin,
        }
