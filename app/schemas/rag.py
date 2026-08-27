from atomic_agents import BaseIOSchema
from pydantic import BaseModel


class HyDEOutputSchema(BaseIOSchema):
    """
    Use this schema for HyDE
    """

    hypothetical_document: str


class SelfRAGOutputSchema(BaseIOSchema):
    """
    Use this schema for Self-RAG
    """

    query: str


class RAGInputSchema(BaseModel):
    query: str
    media: bytes | None = None
