from typing import Callable

from langchain_anthropic import ChatAnthropic

from config import Config

def get_anthropic_llm(
    callback_handler: Callable,
    model_name : str = Config.ANTHROPIC_MODEL_NAME, 
    api_key : str = Config.ANTHROPIC_API_KEY, 
    temperature : float = 0.7, 
    max_tokens : int = 4000
):
    return ChatAnthropic(
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=True,
        callbacks=[callback_handler]
    )