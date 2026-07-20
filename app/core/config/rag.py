from .base import BaseConfig
from pydantic import Field

class RAGConfig(BaseConfig):
    embedding_model: str = Field(..., alias="EMBEDDING_MODEL")
    embedding_n_dim: int = Field(..., alias="EMBEDDING_N_DIM")
    rag_strategy: str = Field(default="hyde", alias="RAG_STRATEGY")
    top_k: int = Field(default=5, alias="TOP_K")
    llm_model: str = Field(default="ollama/gemma4", alias="LLM_MODEL")