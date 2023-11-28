# Dockerfile
FROM mambaorg/micromamba:latest

USER root

# run apt install
RUN apt-get update -y && apt-get upgrade -y

# don't write .pyc files into image to reduce image size 
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# install conda environment to /opt/env/ and prepend to PATH
COPY environment.yml /opt/
RUN micromamba create -f /opt/environment.yml -p /opt/env/
ENV PATH="/opt/env/bin:$PATH"

# change work directory
WORKDIR / 

# copy application contents
COPY . .

# run the container as a non-root user
ENV USER=aaltorse
RUN groupadd -r $USER && useradd -r -g $USER $USER
USER $USER

# entrypoint
ENTRYPOINT ["/entrypoint.sh"]