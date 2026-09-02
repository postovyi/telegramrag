import instructor

from app.core.config import settings


def build_llm_client() -> instructor.AsyncInstructor:
    provider = settings.rag.llm_provider

    if provider == 'openai':
        if not settings.rag.llm_api_key:
            raise ValueError('LLM_API_KEY is required when LLM_PROVIDER=openai')
        return instructor.from_provider(
            f'openai/{settings.rag.llm_model}',
            async_client=True,
            mode=instructor.Mode.JSON,
            api_key=settings.rag.llm_api_key,
        )

    if provider == 'google':
        if not settings.rag.llm_api_key:
            raise ValueError('LLM_API_KEY is required when LLM_PROVIDER=google')
        return instructor.from_provider(
            f'google/{settings.rag.llm_model}',
            async_client=True,
            mode=instructor.Mode.JSON,
            api_key=settings.rag.llm_api_key,
        )

    if provider == 'openai_compatible':
        if not settings.rag.llm_base_url:
            raise ValueError('LLM_BASE_URL is required when LLM_PROVIDER=openai_compatible')
        return instructor.from_provider(
            model=settings.rag.llm_model,
            async_client=True,
            mode=instructor.Mode.JSON,
            base_url=settings.rag.llm_base_url,
        )

    raise ValueError(f'Unsupported LLM_PROVIDER: {provider!r}')
