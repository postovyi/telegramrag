from atomic_agents import AgentConfig, AtomicAgent, BasicChatInputSchema
from atomic_agents.context import SystemPromptGenerator

from app.core.config import settings
from app.prompts import OUTPUT_INSTRUCTIONS, SELF_RAG_PROMPT, SYSTEM_PROMPT
from app.repository import TelegramPostRepository
from app.schemas import SelfRAGOutputSchema, TelegramPostSchema
from app.services.rag.base import RAGStrategy
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.llm_client import build_llm_client


class SelfRAGStrategy(RAGStrategy):
    def __init__(self, post_repository: TelegramPostRepository) -> None:
        super().__init__(post_repository)
        self.agent_config = AgentConfig(
            client=build_llm_client(),
            model=settings.rag.llm_model.split('/', 1)[-1],
            system_prompt_generator=SystemPromptGenerator(
                background=[SYSTEM_PROMPT], output_instructions=[OUTPUT_INSTRUCTIONS]
            ),
        )
        self.agent = AtomicAgent[BasicChatInputSchema, SelfRAGOutputSchema](self.agent_config)

    async def retrieve(self, query: str, media: bytes | None = None) -> list[TelegramPostSchema]:
        refined_query = await self.agent.run_async(
            BasicChatInputSchema(chat_message=SELF_RAG_PROMPT.format(query=query))
        )

        embedding_text = await EmbeddingService.embed_text(refined_query.query)

        posts = await self.post_repository.find_by_embedding(embedding_text.tolist())
        return await self._to_post_schemas(posts)
