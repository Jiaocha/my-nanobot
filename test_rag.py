import asyncio
import os
import sys

from nanobot.agent.vector_memory import VectorMemoryStore
from nanobot.config.loader import load_config

sys.path.append(os.getcwd())

async def test_rag():
    config = load_config()
    vs = VectorMemoryStore(config.agents.defaults.vector_memory)

    # 模拟注入
    test_memory = "[2026-02-23] 用户询问关于 DeepSeek-V3 本地部署，建议包括量化。"
    print("Injecting test memory...")
    await vs.add_memory(test_memory, metadata={"date": "2026-02-23"})

    # 注入系统状态声明
    status_memory = "系统公告：向量搜索和 Reranker 已在 2026-03-02 22:56 完美启用。"
    await vs.add_memory(status_memory, metadata={"type": "status"})

    print("Searching for '上周的问题'...")
    results = await vs.search("上周的问题", top_k=2)

    print("Search Results:")
    for r in results:
        print(f"Match: {r}")

    if results:
        print("SUCCESS: RAG pipeline is functional!")
    else:
        print("FAILED: No results found.")

if __name__ == "__main__":
    asyncio.run(test_rag())
