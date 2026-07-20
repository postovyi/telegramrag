from pydantic import BaseModel

class HyDEOutputSchema(BaseModel):
    hypothetical_document: str

class SelfRAGOutputSchema(BaseModel):
    query: str

class RAGInputSchema(BaseModel):
    query: str
    media: bytes | None = None