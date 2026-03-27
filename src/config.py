"""LLM provider configuration factory."""


def get_llm(provider: str, model: str | None = None):
    """Create a chat model instance for the given provider.

    Args:
        provider: One of "ollama", "openai", "anthropic".
        model: Optional model name override. Falls back to sensible defaults.

    Returns:
        A LangChain BaseChatModel instance.
    """
    match provider:
        case "openai":
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise ImportError(
                    "Install langchain-openai to use the OpenAI provider: "
                    "uv add langchain-openai"
                )
            return ChatOpenAI(model=model or "gpt-4o-mini", temperature=0)

        case "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError:
                raise ImportError(
                    "Install langchain-anthropic to use the Anthropic provider: "
                    "uv add langchain-anthropic"
                )
            return ChatAnthropic(model=model or "claude-haiku-4-5-20251001", temperature=0)

        case "ollama":
            try:
                from langchain_ollama import ChatOllama
            except ImportError:
                raise ImportError(
                    "Install langchain-ollama to use the Ollama provider: "
                    "uv add langchain-ollama"
                )
            return ChatOllama(model=model or "gpt-oss:20b", temperature=0)

        case _:
            raise ValueError(
                f"Unknown provider '{provider}'. "
                "Supported providers: ollama, openai, anthropic"
            )
