import instructor
from atomic_agents import AgentConfig, AtomicAgent, BasicChatInputSchema
from atomic_agents.context import SystemPromptGenerator

from app.core.config import settings
from app.prompts import OUTPUT_INSTRUCTIONS, SELF_RAG_PROMPT, SYSTEM_PROMPT
from app.repository import TelegramPostMediaRepository, TelegramPostRepository
from app.schemas import SelfRAGOutputSchema, TelegramPostSchema
from app.services.rag.base import RAGStrategy
from app.services.rag.embeddings import EmbeddingService


class SelfRAGStrategy(RAGStrategy):
    def __init__(
        self, post_repository: TelegramPostRepository, post_media_repository: TelegramPostMediaRepository
    ) -> None:
        super().__init__(post_repository, post_media_repository)
        self.agent_config = AgentConfig(
            client=instructor.from_provider(
                model=settings.rag.llm_model,
                async_client=True,
                mode=instructor.Mode.JSON,
                base_url=settings.rag.llm_base_url,
            ),
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
        post_embedding = await self._build_query_embedding(embedding_text, media)

        posts = await self.post_repository.find_by_embedding(post_embedding.tolist())
        return await self._to_post_schemas(posts)
