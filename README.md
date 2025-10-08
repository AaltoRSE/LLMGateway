# LLMGateway

This is a front facing gateway for multiple LLMs. The idea, is that this server acts
as a middle man between multiple different LLMs providing OpenAI compatible APIS and
the user. The gateway keeps track of users token usage and associated cost (according to the model specs)

## Features

- Self service Auth via SAML
- Self service key generation
- Admin management via REST API and UI.

## Tech used

The server is written in python using [FastAPI](https://fastapi.tiangolo.com/).
SAML is implemented using the [SAML-Toolkits python3-saml](https://github.com/SAML-Toolkits/python3-saml) library.

### TODO

Here are a few features which are currently on our TODO list:

- Improved usage visualisation UI on frontend.
- More fine grained Access key control (i.e. controlling what models can be accessed with a key)

Nice to have features, but not necessary for now

- Optional use of mongodb as alternative database backend.

## Dependencies

A Detailed description of the dependencies can be found in the [DEPENDENCIES.md](DEPENDENCIES.md) file.

## Architecture

### Postgresql

We use postgresql via sqlalchemy to store persistent data.

### Redis

Redis is used in two places:

## Logging / Usage

The way usage is currently logged and retrieved is potentially rather slow. If it becomes necessary to implement rate limits / daily or similar restrictions, it might be necessary, to implement a more efficient usage check methodology, than the retrieval from MongoDB, as that DB can become pretty crowded.
For daily max usage, an option could be to add usage to the redis db. It might also be necessary to add additional "costs" to each model in the future.

## Run gateway locally

You will need to set the LLM_DEFAULT_URL environment variable (including any port specification) for the container to point to the location of your LLM server.

You will need at least one LLM model running on your local machine. This model needs to accept requests on LLM_DEFAULT_URL/<model_id>/v1/..

The API of the model server needs to be compatible with the API provided by `llama-cpp-python[server]`

In the future, LLM endpoints will also have to provide an additional `/extras/tokenize/count` endpoint, which calculates prompt tokens based on either a single input string, or a full `ChatCompletionRequest`.

The `docker-compose.yml` included in this repo is an example on how to test locally. You will need to set up the keycloak installation for this to work and point the gateway saml authentication to that keycloak service.

## Balance handling

Usage/Balance is handled in a two fashioned way:
Persistent databases contain the actual usage, with time stamps, prompt amounts and costs, a Redis database is being used for balance. The values in this db can be restored from the data in the usage database.
