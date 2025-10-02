import pytest_asyncio
import app.security.entra_jwt


@pytest_asyncio.fixture
async def entra_service(monkeypatch):
    # Replace by a null op
    try:
        service = app.security.entra_jwt.get_entrajwt_auth_service()
    except:
        app.security.entra_jwt.build_global_service()  # we only need this once.
    monkeypatch.setattr(app.security.entra_jwt, "build_global_service", lambda: None)
