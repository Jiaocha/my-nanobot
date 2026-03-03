"""Vector-based memory storage with local Qdrant support and Aging mechanism."""

from __future__ import annotations

import asyncio
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

import httpx
from loguru import logger

from nanobot.utils.helpers import ensure_dir

if TYPE_CHECKING:
    from nanobot.config.schema import VectorMemoryConfig


class VectorMemoryStore:
    """Memory store using Qdrant (Local Mode) with Memory Aging and Metadata."""

    def __init__(self, config: VectorMemoryConfig):
        self.config = config
        self.db_path = str(Path(config.db_path).expanduser().resolve())
        ensure_dir(Path(self.db_path))
        self._client = None
        self._collection_name = config.collection_name
        self._http_client = None
        self._lock = asyncio.Lock()

    def set_http_client(self, client: httpx.AsyncClient):
        """Inject shared HTTP client."""
        self._http_client = client

    def _get_http_client(self):
        return self._http_client if self._http_client else httpx.AsyncClient(timeout=20.0)

    async def warmup(self):
        """Async entry point to initialize the DB in background."""
        await self._init_db()

    async def _init_db(self):
        """Initialize Qdrant with thread-safe lock."""
        if self._client is not None: return
        async with self._lock:
            if self._client is not None: return # Double check after lock

            # Offload synchronous Qdrant init to a thread to avoid blocking the event loop
            def _sync_init():
                from qdrant_client import QdrantClient
                from qdrant_client.http import models
                client = QdrantClient(path=self.db_path)
                collections = client.get_collections().collections
                if not any(c.name == self._collection_name for c in collections):
                    client.create_collection(
                        collection_name=self._collection_name,
                        vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
                    )
                    client.create_payload_index(self._collection_name, "timestamp", models.PayloadSchemaType.KEYWORD)
                return client

            try:
                self._client = await asyncio.to_thread(_sync_init)
                logger.info("🚀 Vector DB Warmup Complete: Qdrant ready at {}", self.db_path)
            except Exception as e:
                logger.error("Vector DB initialization failed: {}", e)

    async def get_embedding(self, text: str) -> List[float] | None:
        client = self._get_http_client()
        try:
            r = await client.post(self.config.embedding_api_url, json={"input": text, "model": "bge-base"}, timeout=3.0)
            r.raise_for_status()
            return r.json()["data"][0]["embedding"]
        except Exception as e:
            logger.warning("Embedding request failed: {}", e)
            return None

    async def _keyword_fallback(self, query: str) -> List[str]:
        import subprocess
        history_path = Path.home() / ".nanobot" / "workspace" / "memory" / "HISTORY.md"
        if not history_path.exists():
            return []
        try:
            cmd = f'findstr /i /c:"{query}" "{str(history_path)}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
            return [line.strip() for line in result.stdout.splitlines() if line.strip()][-10:]
        except Exception as e:
            logger.warning("Keyword fallback failed: {}", e)
            return []

    async def add_memory(self, content: str, metadata: Dict[str, Any] | None = None):
        try:
            embedding = await self.get_embedding(content)
            if not embedding:
                return
            await self._init_db()
            from qdrant_client.http import models
            payload = {
                "content": content,
                "timestamp": int(time.time()),
                "source": metadata.get("source", "conversation") if metadata else "conversation",
                "is_permanent": "[Summary]" in content or "[Fact]" in content
            }

            def _do_upsert():
                self._client.upsert(
                    collection_name=self._collection_name,
                    points=[models.PointStruct(id=str(uuid.uuid4()), vector=embedding, payload=payload)]
                )
            await asyncio.to_thread(_do_upsert)
        except Exception as e:
            logger.warning("Memory addition failed: {}", e)

    async def search(self, query: str, top_k: int | None = None) -> List[str]:
        query_embedding = await self.get_embedding(query)
        if not query_embedding:
            return await self._keyword_fallback(query)
        try:
            await self._init_db()
            def _do_search():
                if hasattr(self._client, "query_points"):
                    res = self._client.query_points(collection_name=self._collection_name, query=query_embedding, limit=40)
                    return res.points
                else:
                    return self._client.search(collection_name=self._collection_name, query_vector=query_embedding, limit=40)

            results = await asyncio.to_thread(_do_search)
            if not results:
                return []
            processed = []
            for hit in results:
                payload = dict(hit.payload or {})
                age_days = (time.time() - payload.get("timestamp", 0)) / 86400
                boost = 1.2 if payload.get("is_permanent") else 1.0
                age_penalty = 0.8 if age_days > 14 else 1.0
                processed.append((hit.score * boost * age_penalty, payload.get("content", "")))
            processed.sort(key=lambda x: x[0], reverse=True)
            return await self.rerank(query, [p[1] for p in processed[:20]])
        except Exception as e:
            logger.warning("Vector search failed: {}", e)
            return await self._keyword_fallback(query)

    async def cleanup_old_memories(self, days: int = 30):
        await self._init_db()
        from qdrant_client.http import models
        threshold = int(time.time()) - (days * 86400)

        def _do_cleanup():
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=models.Filter(must=[
                    models.FieldCondition(key="timestamp", range=models.Range(lt=threshold)),
                    models.FieldCondition(key="is_permanent", match=models.MatchValue(value=False))
                ])
            )
        await asyncio.to_thread(_do_cleanup)

    async def rerank(self, query: str, documents: List[str]) -> List[str]:
        if not documents:
            return []
        client = self._get_http_client()
        try:
            r = await client.post(self.config.rerank_api_url, json={"query": query, "documents": documents, "top_n": self.config.top_k}, timeout=5.0)
            r.raise_for_status()
            return [documents[res["index"]] for res in r.json().get("results", [])]
        except Exception as e:
            logger.warning("Rerank failed: {}", e)
            return documents[:self.config.top_k]

    def get_memory_context(self, query: str | None = None) -> str:
        return "Vector memory active with Aging & Connection Pooling."
