"""Tests for performance utilities."""

import asyncio
import time

import pytest

from nanobot.utils.performance import AsyncCache, BatchProcessor, FileBuffer, LatencyTracker


class TestAsyncCache:
    """Test async cache with TTL support."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Test basic set and get operations."""
        cache = AsyncCache(max_size=10, ttl_seconds=60)

        await cache.set("key1", "value1")
        result = await cache.get("key1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_cache_ttl_expiry(self):
        """Test that cache entries expire after TTL."""
        cache = AsyncCache(max_size=10, ttl_seconds=0.1)

        await cache.set("key1", "value1")
        await asyncio.sleep(0.2)
        result = await cache.get("key1")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_max_size_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = AsyncCache(max_size=2, ttl_seconds=60)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")  # Should evict key1

        result1 = await cache.get("key1")
        result3 = await cache.get("key3")

        assert result1 is None  # Evicted
        assert result3 == "value3"

    @pytest.mark.asyncio
    async def test_cache_decorator(self):
        """Test cache decorator."""
        cache = AsyncCache(max_size=10, ttl_seconds=60)
        call_count = 0

        @cache.cached()
        async def get_data(key: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"data_{key}"

        # First call - cache miss
        result1 = await get_data("test")
        assert result1 == "data_test"
        assert call_count == 1

        # Second call - cache hit
        result2 = await get_data("test")
        assert result2 == "data_test"
        assert call_count == 1  # Should not increment

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test cache delete operation."""
        cache = AsyncCache(max_size=10, ttl_seconds=60)

        await cache.set("key1", "value1")
        deleted = await cache.delete("key1")
        result = await cache.get("key1")

        assert deleted is True
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Test cache clear operation."""
        cache = AsyncCache(max_size=10, ttl_seconds=60)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()

        result1 = await cache.get("key1")
        result2 = await cache.get("key2")

        assert result1 is None
        assert result2 is None


class TestFileBuffer:
    """Test buffered file reader."""

    @pytest.mark.asyncio
    async def test_read_file_cached(self, tmp_path):
        """Test file reading with caching."""
        buffer = FileBuffer(max_files=10, ttl_seconds=60)

        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        # First read - from disk
        content1 = await buffer.read_file(test_file)
        assert content1 == "Hello, World!"

        # Second read - from cache
        content2 = await buffer.read_file(test_file)
        assert content2 == "Hello, World!"

    @pytest.mark.asyncio
    async def test_read_file_mtime_invalidation(self, tmp_path):
        """Test cache invalidation on file modification."""
        buffer = FileBuffer(max_files=10, ttl_seconds=60)

        test_file = tmp_path / "test.txt"
        test_file.write_text("Version 1", encoding="utf-8")

        content1 = await buffer.read_file(test_file)
        assert content1 == "Version 1"

        # Modify file
        time.sleep(0.1)  # Ensure mtime changes
        test_file.write_text("Version 2", encoding="utf-8")

        content2 = await buffer.read_file(test_file)
        assert content2 == "Version 2"

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, tmp_path):
        """Test reading non-existent file."""
        buffer = FileBuffer(max_files=10, ttl_seconds=60)
        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            await buffer.read_file(test_file)

    def test_invalidate(self, tmp_path):
        """Test manual cache invalidation."""
        buffer = FileBuffer(max_files=10, ttl_seconds=60)

        test_file = tmp_path / "test.txt"
        test_file.write_text("Content", encoding="utf-8")

        # Read to cache
        asyncio.run(buffer.read_file(test_file))

        # Invalidate
        buffer.invalidate(test_file)

        # Cache should be empty for this file
        assert str(test_file) not in buffer._cache

    def test_clear(self, tmp_path):
        """Test clearing all cached files."""
        buffer = FileBuffer(max_files=10, ttl_seconds=60)

        test_file1 = tmp_path / "test1.txt"
        test_file2 = tmp_path / "test2.txt"
        test_file1.write_text("Content 1", encoding="utf-8")
        test_file2.write_text("Content 2", encoding="utf-8")

        # Read to cache
        asyncio.run(buffer.read_file(test_file1))
        asyncio.run(buffer.read_file(test_file2))

        # Clear
        buffer.clear()

        assert len(buffer._cache) == 0


class TestBatchProcessor:
    """Test batch processing with concurrency control."""

    @pytest.mark.asyncio
    async def test_process_batch_basic(self):
        """Test basic batch processing."""
        processor = BatchProcessor(batch_size=5, max_concurrency=3)

        async def process_item(item):
            await asyncio.sleep(0.01)
            return item * 2

        items = [1, 2, 3, 4, 5]
        results = await processor.process_batch(items, process_item)

        assert results == [2, 4, 6, 8, 10]

    @pytest.mark.asyncio
    async def test_process_batch_with_errors(self):
        """Test batch processing with some failures."""
        processor = BatchProcessor(batch_size=5, max_concurrency=3)

        async def process_item(item):
            if item == 3:
                raise ValueError("Error processing 3")
            return item * 2

        items = [1, 2, 3, 4, 5]
        results = await processor.process_batch(items, process_item)

        assert results[0] == 2
        assert results[1] == 4
        assert results[2] is None  # Failed
        assert results[3] == 8
        assert results[4] == 10

    @pytest.mark.asyncio
    async def test_process_batch_multiple_batches(self):
        """Test processing multiple batches."""
        processor = BatchProcessor(batch_size=2, max_concurrency=2)

        async def process_item(item):
            await asyncio.sleep(0.01)
            return item + 1

        items = [1, 2, 3, 4, 5]  # Will be processed in 3 batches
        results = await processor.process_batch(items, process_item)

        assert results == [2, 3, 4, 5, 6]


class TestLatencyTracker:
    """Test latency tracking utilities."""

    def test_record_and_average(self):
        """Test recording and averaging latencies."""
        tracker = LatencyTracker(window_size=100)

        tracker.record("operation1", 10.0)
        tracker.record("operation1", 20.0)
        tracker.record("operation1", 30.0)

        avg = tracker.get_average("operation1")
        assert avg == 20.0

    def test_window_size_limit(self):
        """Test that old records are discarded."""
        tracker = LatencyTracker(window_size=3)

        for i in range(10):
            tracker.record("operation1", float(i))

        stats = tracker.get_stats("operation1")
        assert stats["count"] == 3  # Only last 3
        assert stats["min"] == 7.0
        assert stats["max"] == 9.0

    def test_get_stats(self):
        """Test getting comprehensive stats."""
        tracker = LatencyTracker(window_size=100)

        tracker.record("operation1", 10.0)
        tracker.record("operation1", 20.0)
        tracker.record("operation1", 30.0)

        stats = tracker.get_stats("operation1")

        assert stats["min"] == 10.0
        assert stats["max"] == 30.0
        assert stats["avg"] == 20.0
        assert stats["count"] == 3

    def test_get_stats_empty(self):
        """Test getting stats for non-existent operation."""
        tracker = LatencyTracker(window_size=100)

        stats = tracker.get_stats("nonexistent")

        assert stats["min"] == 0
        assert stats["max"] == 0
        assert stats["avg"] == 0
        assert stats["count"] == 0

    def test_context_manager(self):
        """Test latency tracking context manager."""
        tracker = LatencyTracker(window_size=100)

        with tracker.track("operation1"):
            time.sleep(0.01)  # 10ms

        stats = tracker.get_stats("operation1")
        assert stats["count"] == 1
        assert stats["min"] >= 10  # At least 10ms

    def test_clear(self):
        """Test clearing all recorded latencies."""
        tracker = LatencyTracker(window_size=100)

        tracker.record("operation1", 10.0)
        tracker.record("operation2", 20.0)
        tracker.clear()

        stats1 = tracker.get_stats("operation1")
        stats2 = tracker.get_stats("operation2")

        assert stats1["count"] == 0
        assert stats2["count"] == 0
