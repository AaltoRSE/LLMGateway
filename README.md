# LLMGateway

An API gateway for Aalto LLM deployment.

Implemented as a FastAPI app, served using gunicorn + uvicorn, and containerized using Docker.

## Run container locally

Build image and run container
```
docker build -t llmgateway . 
docker run -p 8000:8000 llmgateway
```

Test that connection
```
curl 0.0.0.0:8000
```
