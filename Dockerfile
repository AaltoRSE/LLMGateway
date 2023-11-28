# https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker
# https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker/blob/master/docker-images/python3.11.dockerfile
FROM tiangolo/uvicorn-gunicorn:python3.11

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./app /app