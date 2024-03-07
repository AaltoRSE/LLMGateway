# shared_module.py
import threading
from fastapi import HTTPException, status
import tiktoken


def num_tokens_from_messages(messages):
    """Return the number of tokens used by a list of messages."""
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens_per_message = 3
    tokens_per_name = 1
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


endpoints = {
    "gpt4": {
        "endpoint": "https://aalto-openai-apigw.azure-api.net/v1/openai/gpt4-1106-preview/chat/completions",
        "prompt": 0.01 / 1000,
        "completion": 0.028 / 1000,
    },
    "gpt3": {
        "endpoint": "https://aalto-openai-apigw.azure-api.net/v1/chat",
        "prompt": 0.0005 / 1000,
        "completion": 0.0014 / 1000,
    },
}


class Quota:
    def __init__(self, initial_value=0):
        self.cost = initial_value
        self.lock = threading.Lock()

    def get_price(self):
        with self.lock:
            return self.cost

    def set_price(self, new_value):
        with self.lock:
            self.cost = new_value

    def add_price(self, new_value):
        with self.lock:
            self.cost += new_value

    def get_endpoint(self):
        current_price = self.get_price()
        if current_price < 10:
            return endpoints["gpt4"]["endpoint"]
        elif current_price < 30:
            return endpoints["gpt3"]["endpoint"]
        else:
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="Quota exceeded"
            )

    def update_price(self, token_number: int, is_prompt: bool):
        """This function updates the price of the prompt based on the current endpoint.
        the number of tokens is used and the type of token (whether prompt or completion)
        is used to calculate the price.
        """
        self.add_price(self.calculate_request_price(token_number, is_prompt))

    def calculate_request_price(self, token_number: int, is_prompt: bool):
        """This function retrieves the price of the prompt based on the current endpoint.
        the number of tokens is used and the type of token (whether prompt or completion)
        is used to calculate the price.
        """
        endpoint = self.get_endpoint()
        cost = (
            endpoints[endpoint]["prompt"]
            if is_prompt
            else endpoints[endpoint]["completion"]
        )
        return cost * token_number


import schedule
import time
import threading

server_quota = Quota()


def set_value():
    # Replace this with your logic to set the value
    new_value = server_quota.set_price(0)
    server_quota.set_value(new_value)
    print(f"Setting value to: {new_value}")


def job():
    # Schedule the job every 24 hours
    schedule.every(24).hours.do(set_value)

    while True:
        # Run pending scheduled jobs
        schedule.run_pending()
        time.sleep(1)  # Adjust the sleep time as needed


# Start the job in a separate thread when the module is imported
job_thread = threading.Thread(target=job)
job_thread.start()
