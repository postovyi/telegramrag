from atomic_agents import AgentConfig, AtomicAgent, BasicChatInputSchema
from atomic_agents.context import SystemPromptGenerator

from app.core.config import settings
from app.prompts import HYDE_PROMPT, OUTPUT_INSTRUCTIONS, SYSTEM_PROMPT
from app.repository import TelegramPostMediaRepository, TelegramPostRepository
from app.schemas import HyDEOutputSchema, RetrievedItemSchema
from app.services.rag.base import RAGStrategy
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.llm_client import build_llm_client


class HyDEStrategy(RAGStrategy):
    def __init__(self, post_repository: TelegramPostRepository, media_repository: TelegramPostMediaRepository) -> None:
        super().__init__(post_repository, media_repository)
        self.agent_config = AgentConfig(
            client=build_llm_client(),
            model=settings.rag.llm_model.split('/', 1)[-1],
            system_prompt_generator=SystemPromptGenerator(
                background=[SYSTEM_PROMPT], output_instructions=[OUTPUT_INSTRUCTIONS]
            ),
        )
        self.agent = AtomicAgent[BasicChatInputSchema, HyDEOutputSchema](self.agent_config)

    async def retrieve(self, query: str, media: bytes | None = None) -> list[RetrievedItemSchema]:
        hypothetical_document = await self.create_hypothetical_document(query)
        embedding_text = await EmbeddingService.embed_text(hypothetical_document)

        return await self._search(embedding_text.tolist())

    async def create_hypothetical_document(self, query: str) -> str:
        response = await self.agent.run_async(BasicChatInputSchema(chat_message=HYDE_PROMPT.format(query=query)))

        return response.hypothetical_document
