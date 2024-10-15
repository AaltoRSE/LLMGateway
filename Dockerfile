FROM node:21.5.0 AS frontend-builder

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


FROM mambaorg/micromamba:1.5.9 AS environment-builder

USER root

RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install gcc g++ \
    cmake \
    git \
    ninja-build \
    libopenblas-dev \
    build-essential \
    pkg-config -y 

# Don't write .pyc files into image to reduce image size 
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install conda environment to /opt/env/ and prepend to PATH
COPY environment.yml /opt/

# Install copy of llama-cpp-python with streaming option
WORKDIR /llama_cpp
RUN git clone https://github.com/tpfau/llama-cpp-python.git && cd llama-cpp-python && git checkout stream_testing && git submodule init && git submodule update

RUN micromamba create -f /opt/environment.yml -p /opt/env/


# Dockerfile
# Could be changed at some point to something slimmer
FROM mambaorg/micromamba:1.5.9

USER root
# run the container as a non-root user
ENV USER=aaltorse
RUN groupadd -r $USER && useradd -r -g $USER $USER
USER $USER

COPY --from=environment-builder --chown=aaltorse:aaltorse /opt/env/ /opt/env/

ENV PATH="/opt/env/bin:$PATH"

WORKDIR /app 
# Copy application contents (this includes the frontend files, and only those)
COPY --chown=aaltorse:aaltorse ./app ./app
# Frontend needs to be compiled!
COPY --chown=aaltorse:aaltorse --from=frontend-builder /frontend/dist ./dist

# Entrypoint
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:3000", "-k", "uvicorn.workers.UvicornWorker", "--workers", "6" ]
