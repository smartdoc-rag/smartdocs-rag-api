from langchain_ollama import OllamaLLM
from langchain_deepseek import ChatDeepSeek
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from django.conf import settings


class _ProxyCompatibleChatOpenAI(ChatOpenAI):
    """
    Fix tương thích với proxy port 5001.

    Vấn đề: with_structured_output() mặc định nhờ OpenAI SDK parse message.content
    thay vì tool_calls[0].function.arguments.

    Giải pháp: Override with_structured_output() — dùng bind_tools để gửi tool schema,
    sau đó tự parse tool_calls[0]["args"] thành Pydantic object.
    Format trả về khi include_raw=True phải đúng chuẩn LangChain:
    {"raw": AIMessage, "parsed": <PydanticObj>, "parsing_error": None/Exception}
    """

    def with_structured_output(self, schema, *, include_raw=False, **kwargs):
        llm_with_tools = self.bind_tools([schema])

        def parse(ai_message):
            try:
                tool_calls = ai_message.tool_calls
                if not tool_calls:
                    raise ValueError("No tool calls in response")
                args = tool_calls[0]["args"]
                parsed = schema(**args)
                if include_raw:
                    return {"raw": ai_message, "parsed": parsed, "parsing_error": None}
                return parsed
            except Exception as e:
                if include_raw:
                    return {"raw": ai_message, "parsed": None, "parsing_error": e}
                raise

        return llm_with_tools | RunnableLambda(parse)


class LLMModel:
    @staticmethod
    def get_ollama(
        model: str = "deepseek-v3.1:671b-cloud",
        temperature: float = 0,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
    ) -> OllamaLLM:
        return OllamaLLM(
            model=model,
            temperature=temperature,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
        )

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
    ) -> _ProxyCompatibleChatOpenAI:
        return _ProxyCompatibleChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            base_url="http://127.0.0.1:5001/v1",
            api_key=settings.OPENAI_API_KEY,
            streaming=False,
        )


class LLMModel:
    @staticmethod
    def get_ollama(
        model: str = "qwen2.5:3b",
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
        temperature: float = 0.5,
        max_tokens: int | None = None,
        timeout: int | None = None,
        max_retries: int = 2,
    ) -> _ProxyCompatibleChatOpenAI:
        return _ProxyCompatibleChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            base_url="http://127.0.0.1:5001/v1",
            api_key=settings.OPENAI_API_KEY,
            streaming=False,
        )
