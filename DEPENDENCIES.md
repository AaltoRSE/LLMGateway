# Dependencies

## Direct runtime dependencies

### Core dependencies

| Package                                                        | Scope   | Purpose (why it's needed)                                 | License (SPDX) | GitHub                                                                |
| -------------------------------------------------------------- | ------- | --------------------------------------------------------- | -------------- | --------------------------------------------------------------------- |
| [alembic](https://pypi.org/project/alembic/)                   | schema  | Database schema migrations. Not used in runtime           | MIT            | [sqlalchemy/alembic](https://github.com/sqlalchemy/alembic/)          |
| [SQLAlchemy](https://pypi.org/project/SQLAlchemy/)             | runtime | Main ORM for the app, and SQL toolkit                     | MIT            | [sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy)     |
| [fastapi](https://pypi.org/project/fastapi/)                   | runtime | Web framework for APIs in the backend                     | MIT            | [fastapi/fastapi](https://github.com/fastapi/fastapi)                 |
| [psycopg](https://pypi.org/project/psycopg/)                   | runtime | PostgreSQL driver (source build) for DB connection        | LGPL-3.0       | [psycopg/psycopg](https://github.com/psycopg/psycopg)                 |
| [psycopg-binary](https://pypi.org/project/psycopg-binary/)     | runtime | PostgreSQL driver (prebuilt wheels)                       | LGPL-3.0       | [psycopg/psycopg](https://github.com/psycopg/psycopg)                 |
| [uvicorn](https://pypi.org/project/uvicorn/)                   | runtime | ASGI server for FastAPI                                   | BSD-3-Clause   | [encode/uvicorn](https://github.com/encode/uvicorn)                   |
| [requests](https://pypi.org/project/requests/)                 | runtime | HTTP client (sync), used for entra certificates           | Apache-2.0     | [psf/requests](https://github.com/psf/requests)                       |
| [httpx](https://pypi.org/project/httpx/)                       | runtime | HTTP client (async/sync)                                  | BSD-3-Clause   | [encode/httpx](https://github.com/encode/httpx)                       |
| [h11](https://pypi.org/project/h11/)                           | runtime | HTTP/1.1 protocol library (used by ASGI servers)          | MIT            | [python-hyper/h11](https://github.com/python-hyper/h11)               |
| [urllib3](https://pypi.org/project/urllib3/)                   | runtime | HTTP transport (dependency of requests)                   | MIT            | [urllib3/urllib3](https://github.com/urllib3/urllib3)                 |
| [python-multipart](https://pypi.org/project/python-multipart/) | runtime | Handle multipart/form-data media uploads                  | Apache-2.0     | [Kludex/python-multipart](https://github.com/Kludex/python-multipart) |
| [redis](https://pypi.org/project/redis/)                       | runtime | Session handling (in memory db for concurrent deployment) | MIT0           | [redis/redis-py](https://github.com/redis/redis-py)                   |

### LLM APIs

| Package                                                        | Scope | Purpose (why it's needed)                             | License (SPDX) | GitHub                                                          |
| -------------------------------------------------------------- | ----- | ----------------------------------------------------- | -------------- | --------------------------------------------------------------- |
| [openai](https://pypi.org/project/openai/)                     | llm   | OpenAI API Embedding specs                            | Apache-2.0     | [openai/openai-python](https://github.com/openai/openai-python) |
| [sse-starlette](https://pypi.org/project/sse-starlette/2.1.3/) | llm   | Server sent events, for streaming api responses specs | BSD-3-Clause   | [ sysid/sse-starlette](https://github.com/sysid/sse-starlette)  |

### Security

| Package                                                | Scope   | Purpose (why it's needed)               | License (SPDX)      | GitHub                                                                      |
| ------------------------------------------------------ | ------- | --------------------------------------- | ------------------- | --------------------------------------------------------------------------- |
| [python3-saml](https://pypi.org/project/python3-saml/) | runtime | SAML Handling                           | MIT                 | [SAML-Toolkits/python3-saml](https://github.com/SAML-Toolkits/python3-saml) |
| [pyjwt[crypto]](https://pypi.org/project/PyJWT/)       | runtime | Entra AD auth, JWT handling             | MIT                 | [jpadilla/pyjwt](https://github.com/jpadilla/pyjwt)                         |
| [itsdangerous](https://pypi.org/project/itsdangerous/) | runtime | Token signature handling in saml        | BSD 3-Clause        | [pallets/itsdangerous](https://github.com/pallets/itsdangerous/)            |
| [cryptography](https://pypi.org/project/cryptography/) | runtime | Token signature handling for jwt tokens | Apache-2.0 3-Clause | [pyca/cryptography](https://github.com/pyca/cryptography/)                  |

### Unsorted dependencies

| Package | Scope | Purpose (why it's needed) | License (SPDX) | GitHub |
| ------- | ----- | ------------------------- | -------------- | ------ |

## Development dependencies

| Package                                                          | Scope   | Purpose (why it's needed)         | License (SPDX)    | GitHub                                                                            |
| ---------------------------------------------------------------- | ------- | --------------------------------- | ----------------- | --------------------------------------------------------------------------------- |
| [pytest](https://pypi.org/project/pytest/)                       | dev     | Test runner                       | MIT               | [pytest-dev/pytest](https://github.com/pytest-dev/pytest)                         |
| [mock](https://pypi.org/project/mock/)                           | dev     | Mocking utilities                 | BSD-2-Clause      | [testing-cabal/mock](https://github.com/testing-cabal/mock)                       |
| [pylint](https://pypi.org/project/pylint/)                       | dev     | Linting                           | GPT-2.0           | [pylint-dev/pylint](https://github.com/pylint-dev/pylint)                         |
| [pytest-asyncio](https://pypi.org/project/pytest-asyncio/)       | dev     | Asyncio support for pytest        | Apache-2.0        | [pytest-dev/pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)         |
| [pip-audit](https://pypi.org/project/pip-audit/)                 | dev     | Dependency vulnerability auditing | Apache-2.0        | [pypa/pip-audit](https://github.com/pypa/pip-audit)                               |
| [dill](https://pypi.org/project/dill/)                           | dev     | Advanced pickling/serialization   | ?                 | [uqfoundation/dill](https://github.com/uqfoundation/dill)                         |
| [mypy](https://pypi.org/project/mypy/)                           | dev     | Static type checking              | MIT               | [python/mypy](https://github.com/python/mypy)                                     |
| [types-requests](https://pypi.org/project/types-requests/)       | dev     | Type stubs for requests           | Apache-2.0        | [python/typeshed](https://github.com/python/typeshed)                             |
| [pytest-cov](https://pypi.org/project/pytest-cov/)               | dev     | Coverage reporting for pytest     | MIT               | [pytest-dev/pytest-cov](https://github.com/pytest-dev/pytest-cov)                 |
| [responses](https://pypi.org/project/responses/)                 | dev     | requests mocking                  | Apache-2.0        | [getsentry/responses](https://github.com/getsentry/responses)                     |
| [respx](https://pypi.org/project/respx/)                         | runtime | TBD: could this be dev-only?      | BSD-3-Clause      | [lundberg/respx](https://github.com/lundberg/respx)                               |
| [pytest-postgresql](https://pypi.org/project/pytest-postgresql/) | dev     | PostgreSQL fixtures for tests     | LGPL-3.0, GPL-3.0 | [ClearcodeHQ/pytest-postgresql](https://github.com/ClearcodeHQ/pytest-postgresql) |
| [fakeredis](https://pypi.org/project/fakeredis/)                 | dev     | Redis fixtures for tests          | BSD-3-Clause      | [cunla/fakeredis-py](https://github.com/cunla/fakeredis-py)                       |
