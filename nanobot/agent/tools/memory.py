"""Memory search tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nanobot.agent.tools.registry import Tool

if TYPE_CHECKING:
    from nanobot.agent.memory import MemoryStore


class SearchMemoryTool(Tool):
    """Tool for semantic search in agent's long-term memory."""

    name = "search_memory"
    description = (
        "Search through the agent's long-term memory and history log using semantic search. "
        "Use this when you need to recall past events, decisions, or user preferences "
        "that are not in the current context."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query (e.g., 'What did the user say about deep learning?')",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default: 5).",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    def __init__(self, memory: MemoryStore):
        self.memory = memory

    async def execute(self, query: str, top_k: int = 5) -> str:
        if not self.memory.vector_store:
            return (
                "Vector memory is not enabled in the current configuration. "
                "Falling back to keyword search is not implemented yet. "
                "Please check if memory_mode is set to 'vector'."
            )

        try:
            results = await self.memory.vector_store.search(query, top_k=top_k)
            if not results:
                return f"No memories found for query: '{query}'"

            output = [f"Found {len(results)} relevant memories from long-term history (Semantic Search):"]
            for i, res in enumerate(results, 1):
                output.append(f"Result {i}: {res}")

            output.append("\nNotes: These results are the most relevant context found across all past sessions. Do not perform redundant searches if these provide the necessary info.")
            return "\n\n".join(output)
        except Exception as e:
            return f"Error searching memory: {str(e)}"
