from langchain_ollama import OllamaLLM
from langchain_deepseek import ChatDeepSeek
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from django.conf import settings


class LLMModel:
    @staticmethod
    def get_ollama(
        model: str = "gpt-oss:120b-cloud",
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

    @staticmethod
    def get_anthropic(
        model: str = "gemini-3-flash",
        temperature: float = 0,
        max_tokens: int | None = None,
        timeout: int | None = None,
        max_retries: int = 2,
    ) -> ChatAnthropic:
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            anthropic_api_url="http://127.0.0.1:8045",
        )

    @staticmethod
    def get_openai(
        model: str = "deepseek-chat",
        temperature: float = 0,
        max_tokens: int | None = None,
        timeout: int | None = None,
        max_retries: int = 2,
        model_kwargs: dict | None = None,
    ) -> ChatOpenAI:
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            base_url="http://127.0.0.1:5001/v1",
            api_key=settings.OPENAI_API_KEY,
            streaming=False,
            model_kwargs=model_kwargs or {},
        )
