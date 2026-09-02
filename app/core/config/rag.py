from pydantic import Field

from .base import BaseConfig


class RAGConfig(BaseConfig):
    embedding_model: str = Field(..., alias='EMBEDDING_MODEL')
    embedding_n_dim: int = Field(..., alias='EMBEDDING_N_DIM')
    rag_strategy: str = Field(default='naive', alias='RAG_STRATEGY')
    top_k: int = Field(default=5, alias='TOP_K')
    llm_model: str = Field(default='ollama/gemma4', alias='LLM_MODEL')
    llm_base_url: str = Field(default='http://localhost:11434/v1', alias='LLM_BASE_URL')
    llm_provider: str = Field(default='openai_compatible', alias='LLM_PROVIDER')
    llm_api_key: str | None = Field(default=None, alias='LLM_API_KEY')
    embedding_provider: str = Field(default='sentence_transformers', alias='EMBEDDING_PROVIDER')
    embedding_api_key: str | None = Field(default=None, alias='EMBEDDING_API_KEY')
