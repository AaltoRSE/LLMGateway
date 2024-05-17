# LLMGateway

This is a front facing gateway for multiple LLMs. The idea, is that this server acts as a middle man between multiple
different LLMs. The gateway keeps track of users token usage (the current state only tracks completion tokens), and handles 
access to the LLM servers (i.e. keeps the secrets that allow using them).


## Architecture

The gateway has two dependencies, a redis server and a mongodb. The redis server is used for faster authorization
evaluation, while the mongo db is used for logging and persistence. The concept is to run this server on a kubernetes 
platform  

## Run gateway locally

You will need to set the LLM_DEFAULT_URL environment variable (including any port specification) for the container to point to the location of your LLM server.
You will need at least one LLM model running on your local machine. This model needs to accept requests on LLM_DEFAULT_URL/<model_id>/v1/..
The API of the model server needs to be compatible with the API provided by OpenAI and also have an additional encpoint /extras/tokenize/count, which calculates
prompt tokens based on either a single input string, or a full ChatCompletionRequest. 


