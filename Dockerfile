# Dockerfile
FROM mambaorg/micromamba:1.5.9

USER root

# Run apt install
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
ENV PATH="/opt/env/bin:$PATH"

# Change work directory
WORKDIR /app 

# run the container as a non-root user
ENV USER=aaltorse
RUN groupadd -r $USER && useradd -r -g $USER $USER
USER $USER

# Copy application contents (this includes the frontend files, and only those)
COPY --chown=aaltorse:aaltorse ./app ./app
# Frontend needs to be compiled!
COPY --chown=aaltorse:aaltorse ./frontend/dist ./dist
COPY ./entrypoint.sh .

# Entrypoint
ENTRYPOINT ["./entrypoint.sh"]