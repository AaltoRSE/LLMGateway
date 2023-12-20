# Dockerfile
FROM mambaorg/micromamba:latest

USER root

# Run apt install
RUN apt-get update -y && apt-get upgrade -y

# Don't write .pyc files into image to reduce image size 
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install conda environment to /opt/env/ and prepend to PATH
COPY environment.yml /opt/
RUN micromamba create -f /opt/environment.yml -p /opt/env/
ENV PATH="/opt/env/bin:$PATH"

# Change work directory
WORKDIR /app 

# Copy application contents
COPY ./app .
COPY ./entrypoint.sh .

# run the container as a non-root user
ENV USER=aaltorse
RUN groupadd -r $USER && useradd -r -g $USER $USER
USER $USER

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]