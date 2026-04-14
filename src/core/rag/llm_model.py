from langchain_ollama import OllamaLLM
from langchain_deepseek import ChatDeepSeek
from django.conf import settings


class LLMModel:
    @staticmethod
    def get_ollama(
        model: str = "qwen3.5:cloud",
        temperature: float = 0,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
    ) -> OllamaLLM:
        llm = OllamaLLM(
            model=model,
            temperature=temperature,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
        )
        return llm

    @staticmethod
    def get_deepseek(
        model: str = "deepseek-chat",
        temperature: float = 0,
        max_tokens: int | None = None,
        timeout: int | None = None,
        max_retries: int = 2,
    ) -> ChatDeepSeek:
        return ChatDeepSeek(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            api_key=settings.DEEPSEEK_API_KEY,
        )
