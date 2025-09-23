# Database name for Aalto AI
DB_NAME=aaltollms

# PostgreSQL database password
POSTGRES_PASSWORD=devbackend123

# Podman container name for database
DB_CONTAINER_NAME=aalto-llms-db

# Select between podman and docker (podman default)
CONTAINER_ENGINE=$(shell command -v podman 2>/dev/null || echo docker)
CONTAINER_ENGINE_COMPOSE=$(shell command -v podman-compose 2>/dev/null || echo docker compose)

# Function to prompt for user input
define prompt
    @read -p "$(1)" $(2); echo $$$(2)
endef

# Starts the podman stack
start:
	$(CONTAINER_ENGINE_COMPOSE) -f docker-compose.yml up --force-recreate

# Just rebuild necessary don't doa  full rebuild
restart:
	$(CONTAINER_ENGINE_COMPOSE) -f docker-compose.yml up --build

# Shut down the stack
stop:
	$(CONTAINER_ENGINE_COMPOSE) -f docker-compose.yml down

# A helper to run tests
test:
	pipenv run pylint app
	pipenv run mypy app
	pipenv run pytest tests

# Creates an empty database
create_db:
	$(CONTAINER_ENGINE)  exec -it ${DB_CONTAINER_NAME} su postgres -c "createdb ${DB_NAME}" || exit 0

reset_db:
	$(CONTAINER_ENGINE)  exec -it ${DB_CONTAINER_NAME} su postgres -c "dropdb ${DB_NAME}"
	$(CONTAINER_ENGINE)  exec -it ${DB_CONTAINER_NAME} su postgres -c "createdb ${DB_NAME}" || exit 0
# CLI command for connecting to the database using podman

# CLI command for connecting to the database using podman
psql:
	$(CONTAINER_ENGINE)  exec -it ${DB_CONTAINER_NAME} psql postgresql://postgres:${POSTGRES_PASSWORD}@localhost/${DB_NAME}

# Dump the schema
pg_schema:
	$(CONTAINER_ENGINE)  exec -it ${DB_CONTAINER_NAME} pg_dump --schema-only postgresql://postgres:${POSTGRES_PASSWORD}@localhost/${DB_NAME}

install:
	pipenv install

install_dev:
	pipenv install -d

# Check that venv is activated/libraries installed
dev:
	uvicorn app.main:app --reload
# Migrations
#
migrate_head:
	$(CONTAINER_ENGINE)  exec -it gateway-server alembic upgrade head

migrate_auto:
	@echo "Enter migration message: ";
	@read line; \
	$(CONTAINER_ENGINE)  exec -u root -it gateway-server alembic revision --autogenerate -m "$$line"

migrate_down:
	$(CONTAINER_ENGINE)  exec -it gateway-server alembic downgrade base

migrate_plus:
	$(CONTAINER_ENGINE)  exec -it gateway-server alembic upgrade +1

migrate_minus:
	$(CONTAINER_ENGINE)  exec -it gateway-server alembic downgrade -1

migrate_status:
	$(CONTAINER_ENGINE)  exec -it gateway-server alembic current

# Build a podman image
build:
	$(CONTAINER_ENGINE)  build -t gateway-server-manual .

setup_dev:
	@echo "Starting containers to set up database"
	$(CONTAINER_ENGINE_COMPOSE)  -f docker-compose.yml up --build -d
	@echo "waiting for services to start up"
	sleep 5
	$(MAKE) create_db
	$(MAKE) migrate_head
	$(CONTAINER_ENGINE_COMPOSE)  -f docker-compose.yml down
