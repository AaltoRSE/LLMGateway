# LLMGateway

This branch is a simple gateway for an azure subscription.
It allows you to provide an azure subscription to users without having to provide them the actual key and kets you set up a key that they can use to route their requests through this gateway.
At the moment, only the chat/completion api is available.

## Setup

The Server uses a redis database for fast access to api keys and a mongo database to save logging information about the amount

## Capabilities

The current server is based on FastAPI, and alows you to set up the following:

- The llm key used for the endpoint.
  Build image and run container

```
docker build -t llmgateway .
docker run -p 8000:8000 llmgateway
```

Test the connection

```
curl 0.0.0.0:8000
```
