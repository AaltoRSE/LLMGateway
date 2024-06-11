# LLMGateway

This is a front facing gateway for multiple LLMs. The idea, is that this server acts as a middle man between multiple
different LLMs providing OpenAI compatible APIS and the user. The gateway keeps track of users token usage (the current
state only tracks completion tokens), and handles access to the LLM servers (i.e. keeps the secrets that allow using them).

## Features

- Self service Auth via SAML
- Self service checkout for key generation
- Admin management via REST API
-

### TODO

Here are a few features which are currently on our TODO list:

- Admin Front End UI
- More fine grained Access key control (i.e. controlling what models can be accessed with a key)
- Proper Usage logging (including prompt tokens, currently restricted to completion tokens)

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

### Mongo DB

The Mongo database employed in this gateway is used for storing the logging information along with user data.

#### The `apikeys` collection:

```python
{
    "user" : str,  # User, this key belongs to
    "active": boolean, # whether the key is active
    "key": str, # the actual key
    "name": str # name given to the key
}
```

Likely future fields:
`authorization : [ str ]` to indicate which models a key is for.

#### The `logs` collection

```python
{
    "tokencount": int,  # This is the completion tokens
    "isprompt": boolean, # Whether this is for prompt or completion
    "model": str, # which model was used for this usage
    "source": str, # key or user who caused this usage
    "sourcetype": str # Whether the source is a "user" or an "apikey"
    "timestamp": datetime,  # Current timestamp in UTC
}
```

#### The `user` collection

```python
{
    "username": str,  # The identifier of the user - provided by the IdP
    "keys": [ str ], # The set of keys belonging to this user
}
```

Likely future fields:

- `"isAdmin" : boolean` indicator whether the user is an admin, default, false

### Redis

The redis database is mainly used for fast retrieval of authentication keys, and should thus be kept in sync with the mongo db keys.

## Logging / Usage

The way usage is currently logged and retrieved is potentially rather slow. If it becomes necessary to implement rate limits / daily or similar restrictions, it might be necessary, to implement a more efficient usage check methodology, than the retrieval from MongoDB, as that DB can become pretty crowded.
For daily max usage, an option could be to add usage to the redis db. It might also be necessary to add additional "costs" to each model in the future.

## Run gateway locally

You will need to set the LLM_DEFAULT_URL environment variable (including any port specification) for the container to point to the location of your LLM server.

You will need at least one LLM model running on your local machine. This model needs to accept requests on LLM_DEFAULT_URL/<model_id>/v1/..

The API of the model server needs to be compatible with the API provided by `llama-cpp-python[server]`

In the future, LLM endpoints will also have to provide an additional `/extras/tokenize/count` endpoint, which calculates prompt tokens based on either a single input string, or a full `ChatCompletionRequest`.

The `docker-compose.yml` included in this repo is an example on how to test locally. You will need to set up the keycloak installation for this to work and point the gateway saml authentication to that keycloak service.
