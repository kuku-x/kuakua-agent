from typing import Optional

from llama_index.core import VectorStoreIndex, Document
from llama_index.llms.openai import OpenAI

from kuakua_agent.config import settings
from kuakua_agent.core.logging import get_logger

logger = get_logger(__name__)


class VectorStoreManager:
    def __init__(self):
        self.milestone_index: Optional[VectorStoreIndex] = None
        self._initialized = False
        self._llm = None
        self._embed_model = None

    def _ensure_llm(self):
        """Lazy load LLM with OpenAI-compatible interface for DeepSeek."""
        if self._llm is None:
            # Try deepseek module first, fall back to OpenAI-compatible
            try:
                from llama_index.llms.deepseek import DeepSeek
                self._llm = DeepSeek(
                    api_key=settings.llm_api_key,
                    model=settings.llm_model_id
                )
                logger.info("Using DeepSeek LLM")
            except ImportError:
                self._llm = OpenAI(
                    api_key=settings.llm_api_key,
                    model=settings.llm_model_id,
                    base_url=settings.llm_base_url
                )
                logger.info("Using OpenAI-compatible LLM with DeepSeek endpoint")
        return self._llm

    def _ensure_embed_model(self):
        """Lazy load embedding model with OpenAI-compatible interface for DeepSeek."""
        if self._embed_model is None:
            # Try deepseek module first, fall back to OpenAI-compatible
            try:
                from llama_index.embeddings.deepseek import DeepSeekEmbedding
                self._embed_model = DeepSeekEmbedding(
                    api_key=settings.llm_api_key,
                    model="deepseek-embed"
                )
                logger.info("Using DeepSeek Embedding")
            except ImportError:
                from llama_index.embeddings.openai import OpenAIEmbedding
                self._embed_model = OpenAIEmbedding(
                    model="deepseek-embed",
                    api_key=settings.llm_api_key,
                    base_url=f"{settings.llm_base_url}/embeddings"
                )
                logger.info("Using OpenAI-compatible Embedding with DeepSeek endpoint")
        return self._embed_model

    def build_milestone_index(self, milestones: list[dict]):
        """Build vector index from milestones."""
        docs = [
            Document(
                text=f"时间：{m.get('occurred_at', 'unknown')} | 类型：{m.get('event_type', 'unknown')} | 成就：{m.get('description', '')}",
                metadata={"id": m.get("id"), "type": m.get("event_type", "unknown")}
            )
            for m in milestones
        ]
        embed_model = self._ensure_embed_model()
        self.milestone_index = VectorStoreIndex.from_documents(docs, embed_model=embed_model)
        self._initialized = True
        logger.info(f"Built milestone index with {len(docs)} documents")

    def retrieve_similar_milestones(self, milestone_type: str, top_k: int = 3) -> list[dict]:
        """Retrieve similar milestones by type."""
        if not self.milestone_index:
            return []

        retriever = self.milestone_index.as_retriever(similarity_top_k=top_k)
        query = f"用户达成了{milestone_type}类型的成就"
        nodes = retriever.retrieve(query)
        return [
            {
                "id": n.metadata.get("id"),
                "text": n.text,
                "score": n.score if hasattr(n, 'score') else None
            }
            for n in nodes
        ]

    def build_praise_context(self, current: dict, recent: list[dict]) -> str:
        """Build context string including historical similar achievements."""
        similar = self.retrieve_similar_milestones(current.get("event_type", ""), top_k=2)

        parts = []
        if recent:
            parts.append(f"用户最近的成就：\n" + "\n".join([f"- {m.get('description', '')}" for m in recent[:5]]))
        if similar:
            parts.append(f"\n用户过去的类似成就：\n" + "\n".join([f"- {s['text']}" for s in similar]))
        parts.append(f"\n当前成就：{current.get('description', '')}")

        return "\n".join(parts)