FROM node:22.13.0 AS frontend-builder

ARG LOGIN_URL=https://ai-gateway.k8s.aalto.fi/saml/login
ARG LOGOUT_URL=https://ai-gateway.k8s.aalto.fi/saml/logout
ARG BUILD=build
ENV VITE_LOGIN_URL=${LOGIN_URL}
ENV VITE_LOGOUT_URL=${LOGOUT_URL}

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run ${BUILD}

FROM docker.io/oz123/pipenv:3.11-v2023-6-26 AS builder

# Tell pipenv to create venv in the current directory
ENV PIPENV_VENV_IN_PROJECT=1

ARG ENV=production

# Pipfile contains requests
ADD Pipfile.lock Pipfile /usr/src/

WORKDIR /usr/src

# NOTE: If you install binary packages required for a python module, you need
# to install them again in the runtime. For example, if you need to install pycurl
# you need to have pycurl build dependencies libcurl4-gnutls-dev and libcurl3-gnutls
# In the runtime container you need only libcurl3-gnutls

# RUN apt install -y libcurl3-gnutls libcurl4-gnutls-dev

ENV PATH="/root/.local/bin:$PATH"

RUN if [ "$ENV" = "production" ]; then \
    pipenv sync ; \
    else \
    pipenv sync -d ; \
    fi

# Unnecessary
# RUN /usr/src/.venv/bin/python -c "import requests; print(requests.__version__)"

# This is the runtime container, no pipenv installed there.

# Dockerfile
# Could be changed at some point to something slimmer
FROM docker.io/python:3.11 AS runtime

# Create user to run the server with
RUN useradd -ms /bin/bash aaltoai

RUN mkdir -v /usr/src/.venv

COPY --from=builder /usr/src/.venv/ /usr/src/.venv/

# If something odd happens uncomment to see if versions match
# RUN /usr/src/.venv/bin/python -c "import requests; print(requests.__version__)"

WORKDIR /usr/src/app

COPY app ./app

# For imgrations
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
COPY run.sh ./run.sh

COPY --from=frontend-builder /frontend/dist ./frontend/dist
# Change user
USER aaltoai

ENV PATH="/usr/src/.venv/bin:$PATH"

CMD ["./run.sh"]

