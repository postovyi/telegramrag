from atomic_agents import AgentConfig, AtomicAgent, BasicChatInputSchema
from atomic_agents.context import SystemPromptGenerator
from app.core.config import settings
from app.repository import TelegramPostMediaRepository, TelegramPostRepository
from app.schemas import SelfRAGOutputSchema, TelegramPostSchema
from app.services.rag.embeddings import EmbeddingService
from app.prompts import SYSTEM_PROMPT, SELF_RAG_PROMPT, OUTPUT_INSTRUCTIONS
import instructor
import numpy as np


class SelfRAGStrategy:
    def __init__(self, post_repository: TelegramPostRepository, post_media_repository: TelegramPostMediaRepository) -> None:
        self.post_repository = post_repository
        self.post_media_repository = post_media_repository
        self.agent_config = AgentConfig(
            client=instructor.from_provider(
                model=settings.rag.llm_model,
                async_client=True,
                mode=instructor.Mode.JSON,
            ), 
            system_prompt_generator=SystemPromptGenerator(background=[SYSTEM_PROMPT], output_instructions=[OUTPUT_INSTRUCTIONS]),
        )
        self.agent = AtomicAgent[BasicChatInputSchema, SelfRAGOutputSchema](self.agent_config)

    async def retrieve(self, query: str, media: bytes | None = None) -> list[TelegramPostSchema]:
        refined_query = await self.agent.run_async(SELF_RAG_PROMPT.format(query=query))

        embedding_text = await EmbeddingService.embed_text(refined_query)
        if media:
            embedding_media = await EmbeddingService.embed_image(media)
        else:
            embedding_media = np.zeros(settings.rag.embedding_n_dim)

        post_embedding = embedding_text + embedding_media

        posts = await self.post_repository.find_by_embedding(post_embedding.tolist())
        return [
            TelegramPostSchema.model_validate(post, extra="ignore")
            for post in posts
        ]