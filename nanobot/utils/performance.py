"""
Performance optimization utilities for nanobot.

Provides caching, buffering, and async optimization tools.
"""

from __future__ import annotations

import asyncio
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

from loguru import logger

T = TypeVar('T')


class AsyncCache:
    """
    Async-safe LRU cache with TTL support.

    Usage:
        cache = AsyncCache(max_size=100, ttl_seconds=300)

        @cache.cached()
        async def get_data(key: str) -> str:
            return await fetch_from_db(key)
    """

    def __init__(self, max_size: int = 100, ttl_seconds: float = 300):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get value from cache, returns None if expired or not found."""
        async with self._lock:
            if key not in self._cache:
                return None

            timestamp, value = self._cache[key]
            if time.time() - timestamp > self._ttl:
                del self._cache[key]
                return None

            return value

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache with automatic eviction if full."""
        async with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest_key]

            self._cache[key] = (time.time(), value)

    async def delete(self, key: str) -> bool:
        """Delete key from cache, returns True if existed."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()

    def cached(self, key_func: Callable[..., str] | None = None):
        """Decorator for caching async function results."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate cache key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    # Default: use function name + args
                    key = f"{func.__name__}:{args}:{kwargs}"

                # Try cache first
                cached_value = await self.get(key)
                if cached_value is not None:
                    logger.debug("Cache hit for {}", key)
                    return cached_value

                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                await self.set(key, result)
                logger.debug("Cache miss, stored {}", key)

                return result

            return wrapper
        return decorator


class FileBuffer:
    """
    Buffered file reader with automatic cache invalidation.

    Usage:
        buffer = FileBuffer()
        content = await buffer.read_file(path)
    """

    def __init__(self, max_files: int = 50, ttl_seconds: float = 60):
        self._cache: dict[str, tuple[float, str]] = {}
        self._max_files = max_files
        self._ttl = ttl_seconds

    async def read_file(self, path: Path) -> str:
        """Read file with buffering and mtime-based invalidation."""
        path_str = str(path)

        # Check if file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Get file modification time
        mtime = path.stat().st_mtime

        # Check cache
        if path_str in self._cache:
            cached_mtime, content = self._cache[path_str]
            if cached_mtime == mtime and time.time() - cached_mtime < self._ttl:
                return content

        # Read from disk
        content = path.read_text(encoding="utf-8")

        # Update cache (evict oldest if needed)
        if len(self._cache) >= self._max_files and path_str not in self._cache:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]

        self._cache[path_str] = (mtime, content)
        return content

    def invalidate(self, path: Path) -> None:
        """Invalidate cache for specific file."""
        path_str = str(path)
        if path_str in self._cache:
            del self._cache[path_str]

    def clear(self) -> None:
        """Clear all cached files."""
        self._cache.clear()


class BatchProcessor:
    """
    Process items in batches for better performance.

    Usage:
        async def process_item(item):
            return await expensive_operation(item)

        processor = BatchProcessor(batch_size=10)
        results = await processor.process_batch(items, process_item)
    """

    def __init__(self, batch_size: int = 10, max_concurrency: int = 5):
        self._batch_size = batch_size
        self._max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def process_batch(
        self,
        items: list[Any],
        processor: Callable[[Any], Any],
    ) -> list[Any]:
        """Process items in batches with concurrency limit."""
        results = []

        for i in range(0, len(items), self._batch_size):
            batch = items[i:i + self._batch_size]

            # Process batch with concurrency limit
            async def process_with_semaphore(item):
                async with self._semaphore:
                    return await processor(item)

            batch_results = await asyncio.gather(
                *[process_with_semaphore(item) for item in batch],
                return_exceptions=True,
            )

            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error("Batch processing error: {}", result)
                    results.append(None)
                else:
                    results.append(result)

        return results


class LatencyTracker:
    """
    Track and report operation latencies.

    Usage:
        tracker = LatencyTracker()

        async with tracker.track("database_query"):
            result = await db.query()

        print(f"Average latency: {tracker.get_average('database_query')}")
    """

    def __init__(self, window_size: int = 100):
        self._latencies: dict[str, list[float]] = {}
        self._window_size = window_size

    def track(self, operation: str):
        """Context manager for tracking operation latency."""
        return LatencyContext(self, operation)

    def record(self, operation: str, latency_ms: float) -> None:
        """Record latency for an operation."""
        if operation not in self._latencies:
            self._latencies[operation] = []

        latencies = self._latencies[operation]
        latencies.append(latency_ms)

        # Keep only recent window
        if len(latencies) > self._window_size:
            latencies.pop(0)

    def get_average(self, operation: str) -> float:
        """Get average latency for an operation."""
        latencies = self._latencies.get(operation, [])
        if not latencies:
            return 0.0
        return sum(latencies) / len(latencies)

    def get_stats(self, operation: str) -> dict[str, float]:
        """Get latency statistics for an operation."""
        latencies = self._latencies.get(operation, [])
        if not latencies:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}

        return {
            "min": min(latencies),
            "max": max(latencies),
            "avg": sum(latencies) / len(latencies),
            "count": len(latencies),
        }

    def clear(self) -> None:
        """Clear all recorded latencies."""
        self._latencies.clear()


class LatencyContext:
    """Context manager for latency tracking."""

    def __init__(self, tracker: LatencyTracker, operation: str):
        self._tracker = tracker
        self._operation = operation
        self._start_time: float = 0

    def __enter__(self) -> 'LatencyContext':
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        elapsed_ms = (time.perf_counter() - self._start_time) * 1000
        self._tracker.record(self._operation, elapsed_ms)


# Global instances for common use cases
bootstrap_cache = AsyncCache(max_size=10, ttl_seconds=60)
file_buffer = FileBuffer(max_files=50, ttl_seconds=60)
latency_tracker = LatencyTracker(window_size=100)
