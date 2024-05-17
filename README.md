# LLMGateway

This is a front facing gateway for multiple LLMs. The idea, is that this server acts as a middle man between multiple
different LLMs. The gateway keeps track of users token usage (the current state only tracks completion tokens), and handles 
access to the LLM servers (i.e. keeps the secrets that allow using them).


## Architecture

The gateway has two dependencies, a redis server and a mongodb. The redis server is used for faster authorization
evaluation, while the mongo db is used for logging and persitence. The concept is to run this server on a kubernetes 
platform  

## Run container locally

Build image and run container
```
docker build -t llmgateway . 
docker run -p 8000:8000 llmgateway
```

Test the connection
```
curl 0.0.0.0:8000
```
