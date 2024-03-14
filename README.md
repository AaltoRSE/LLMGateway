# LLMGateway

This branch is a simple gateway for an azure subscription.
It allows you to provide an azure subscription to users without having to provide them the actual key and kets you set up a key that they can use to route their requests through this gateway.
At the moment, only the chat/completion api is available.

## Requirements

You will need to have a redis and mongo db running, we suggest using docker to wrap this.
We have added two docker compose files, one for the gateway and one for the databases, which should work for a testing environment.
In a production environment please update the environment variables used.

In production, this should also be put behind a nginx or other reverse proxy, for https support, as the server currently does not provide https out of the box.

## Setup

The Server uses a redis database for fast access to api keys and a mongo database to save logging information about the usage of the server.
As such, it requires the following environment variables to be set:

- `MONGOUSER`, the user name of the mongo DB
- `MONGOPASSWORD`, the password for the mongo db
- `MONGOHOST`, the hostname of the mongo db
- `REDISHOST`, the host of the redis memory
- `REDISPORT`, the port of the redis memory

For redis make sure, that only your server can access the db, as the redis docker containers are shipped without password protection.

To indicate where to post the requests to, you will further need to specify a `LLM_BASE_URL` variable which points to the base url (before the before the `/chat/completions`) path.

Finally you need to set an `ADMIN_KEY` variable which is used to define the access key for the admin endpoints.

## Access

There are two distinct Headers for API Keys that can be used on the API.

1. The `AdminKey` header is the header for all endpoints under `/admin` and the key needs to be defined at startup.
2. An `Authorization: Bearer` authentication scheme for all llm endpoints to be compatible with the OpenAI API.

## Capabilities

The current gateway server is based on FastAPI, and allows you to set up the following while running:

- The llm key used for the azure subscription (via the `admin/setllmkey` endpoint)
- Set Keys for the llm endpoint on this gateway (via the `admin/addapikey` endpoint)
- Set the primary system prompt for all requests (via the `admin/setprompt` endpoint), this prompt will be injected into all requests posted to the api. This can help to avoid misuse but will likely increase costs if the prompt is large.

Additional endpoints and request formats can be found on the `/docs` end point.
