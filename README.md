# LLMGateway

This is a front facing gateway for multiple LLMs. The idea, is that this server acts as a middle man between multiple
different LLMs. The gateway keeps track of users token usage (the current state only tracks completion tokens), and handles 
access to the LLM servers (i.e. keeps the secrets that allow using them).


## Requirements and dependencies

- Kubernetes
  - Certbot Letsencrypt plugin 
  - Set up secrets for Admin key and LLM API key
  - MongoDB and Redis deployed on the cluster.
- Security
  - The current authenticaion scheme for the user API is based on session cookies and SAML authentication.
    - This means, you need an existing IdP which has the gateway setup as a service provider. 
    - You will need to update the auth saml router endpoints to conform with what the kind of access you want to allow
  - The current assumption is that any key can be used with any model and that there is no use restriction. 
    - If you want to implement this kind of restriction, you should add another dependency on the llm endpoints.
- Python dependencies:
  - General:
    - fastapi
    - gunicorn
    - uvicorn
    - redis-py
    - pymongo
    - schedule
    - httpx
    - sse-starlette
    - itsdangerous (for session managment)
    - python-multipart
    - python-jose
  - For SAML:
    - python3-saml

## Architecture

The Gateway uses two databases Redis and MongoDB. Redis is used for fast key retrieval/checks, while Mongo is used for usage permanent storage. 
Each model accessible by the gateway has to be hosted separeately and provide an OpenAI compatible API. The models all have to be hosted in a way that they are accessible at the same URL only changing the path (e.g. https://your.llm.server/<model-id1>/v1). Simplest is to host them on the same kubernetes cluster.


## Logging / Usage 

The way usage is currently logged and retrieved is potentially rather slow. If it becomes necessary to implement rate limits / daily or similar restrictions, it might be necessary, to implement a more efficient usage check methodology, than the retrieval from MongoDB, as that DB can become pretty crowded.
For daily max usage, an option could be to add usage to the redis db. It might also be necessary to add additional "costs" to each model in the future. 

## Run gateway locally

You will need to set the LLM_DEFAULT_URL environment variable (including any port specification) for the container to point to the location of your LLM server.
You will need at least one LLM model running on your local machine. This model needs to accept requests on LLM_DEFAULT_URL/<model_id>/v1/..
The API of the model server needs to be compatible with the API provided by OpenAI and also have an additional encpoint /extras/tokenize/count, which calculates
prompt tokens based on either a single input string, or a full ChatCompletionRequest. 


