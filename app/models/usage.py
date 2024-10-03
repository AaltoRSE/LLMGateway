from pydantic import BaseModel


class Usage(BaseModel):
    prompt_tokens: int
    total_tokens: int
    completion_tokens: int
    cost: int  # in Euros
