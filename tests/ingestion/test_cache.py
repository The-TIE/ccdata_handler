"""
Unit tests for caching layer in the unified data ingestion pipeline.

This module tests the CacheManager with comprehensive coverage of memory caching,
Redis caching, hybrid caching, TTL expiration, LRU eviction, cache warming,
and cache statistics.
"""

import pytest
import asyncio
import json
import pickle
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from src.ingestion.cache import (
    CacheManager,
    CacheBackend,
    SerializationFormat,
    CacheEntry,
    CacheStats,
)


class TestCacheEntry:
    """Test cases for CacheEntry."""

    def test_cache_entry_creation(self):
        """Test CacheEntry creation."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            expires_at=expires_at,
            metadata={"source": "test"},
        )

        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.created_at == now
        assert entry.expires_at == expires_at
        assert entry.access_count == 0
        assert entry.last_accessed is None
        assert entry.metadata["source"] == "test"

    def test_is_expired_false(self):
        """Test is_expired returns False for non-expired entry."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        entry = CacheEntry(
            key="test_key", value="test_value", created_at=now, expires_at=expires_at
        )

        assert not entry.is_expired()

    def test_is_expired_true(self):
        """Test is_expired returns True for expired entry."""
        now = datetime.now(timezone.utc)
        expires_at = now - timedelta(hours=1)  # Expired 1 hour ago

        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now - timedelta(hours=2),
            expires_at=expires_at,
        )

        assert entry.is_expired()

    def test_is_expired_no_expiration(self):
        """Test is_expired returns False when no expiration set."""
        now = datetime.now(timezone.utc)

        entry = CacheEntry(
            key="test_key", value="test_value", created_at=now, expires_at=None
        )

        assert not entry.is_expired()

    def test_touch(self):
        """Test touch method updates access statistics."""
        now = datetime.now(timezone.utc)

        entry = CacheEntry(key="test_key", value="test_value", created_at=now)

        assert entry.access_count == 0
        assert entry.last_accessed is None

        entry.touch()

        assert entry.access_count == 1
        assert entry.last_accessed is not None

        entry.touch()

        assert entry.access_count == 2


class TestCacheStats:
    """Test cases for CacheStats."""

    def test_cache_stats_creation(self):
        """Test CacheStats creation with default values."""
        stats = CacheStats()

        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
        assert stats.evictions == 0
        assert stats.errors == 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats()

        # No hits or misses
        assert stats.hit_rate == 0.0

        # Some hits and misses
        stats.hits = 80
        stats.misses = 20
        assert stats.hit_rate == 0.8

        # Only hits
        stats.misses = 0
        assert stats.hit_rate == 1.0

        # Only misses
        stats.hits = 0
        stats.misses = 100
        assert stats.hit_rate == 0.0


class TestCacheManager:
    """Test cases for CacheManager."""

    @pytest.fixture
    def memory_cache(self):
        """Create memory-based cache manager."""
        return CacheManager(
            backend=CacheBackend.MEMORY, default_ttl=3600, max_memory_entries=100
        )

    @pytest.fixture
    def redis_cache(self):
        """Create Redis-based cache manager."""
        return CacheManager(
            backend=CacheBackend.REDIS,
            redis_url="redis://localhost:6379",
            default_ttl=3600,
        )

    @pytest.fixture
    def hybrid_cache(self):
        """Create hybrid cache manager."""
        return CacheManager(
            backend=CacheBackend.HYBRID,
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            max_memory_entries=50,
        )

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        client = AsyncMock()
        client.ping = AsyncMock()
        client.get = AsyncMock()
        client.setex = AsyncMock()
        client.delete = AsyncMock()
        client.exists = AsyncMock()
        client.keys = AsyncMock()
        return client

    def test_init_memory_cache(self):
        """Test CacheManager initialization with memory backend."""
        cache = CacheManager(
            backend=CacheBackend.MEMORY,
            default_ttl=1800,
            max_memory_entries=500,
            serialization_format=SerializationFormat.PICKLE,
            key_prefix="test:",
        )

        assert cache.backend == CacheBackend.MEMORY
        assert cache.default_ttl == 1800
        assert cache.max_memory_entries == 500
        assert cache.serialization_format == SerializationFormat.PICKLE
        assert cache.key_prefix == "test:"
        assert isinstance(cache._memory_cache, dict)
        assert isinstance(cache._access_order, list)
        assert isinstance(cache.stats, CacheStats)

    def test_init_redis_cache(self):
        """Test CacheManager initialization with Redis backend."""
        cache = CacheManager(backend=CacheBackend.REDIS, redis_url="redis://test:6379")

        assert cache.backend == CacheBackend.REDIS
        assert cache._redis_url == "redis://test:6379"
        assert cache._redis_client is None

    def test_make_key(self, memory_cache):
        """Test key prefixing."""
        full_key = memory_cache._make_key("test_key")
        assert full_key == "ccdata_ingestion:test_key"

    def test_serialize_value_json(self, memory_cache):
        """Test JSON serialization."""
        memory_cache.serialization_format = SerializationFormat.JSON

        data = {"key": "value", "number": 123}
        serialized = memory_cache._serialize_value(data)

        assert isinstance(serialized, bytes)
        assert json.loads(serialized.decode("utf-8")) == data

    def test_serialize_value_pickle(self, memory_cache):
        """Test pickle serialization."""
        memory_cache.serialization_format = SerializationFormat.PICKLE

        data = {"key": "value", "complex": datetime.now()}
        serialized = memory_cache._serialize_value(data)

        assert isinstance(serialized, bytes)
        assert pickle.loads(serialized) == data

    def test_deserialize_value_json(self, memory_cache):
        """Test JSON deserialization."""
        memory_cache.serialization_format = SerializationFormat.JSON

        data = {"key": "value", "number": 123}
        serialized = json.dumps(data).encode("utf-8")
        deserialized = memory_cache._deserialize_value(serialized)

        assert deserialized == data

    def test_deserialize_value_pickle(self, memory_cache):
        """Test pickle deserialization."""
        memory_cache.serialization_format = SerializationFormat.PICKLE

        data = {"key": "value", "complex": datetime.now()}
        serialized = pickle.dumps(data)
        deserialized = memory_cache._deserialize_value(serialized)

        assert deserialized == data

    @pytest.mark.asyncio
    async def test_get_redis_client_success(self, redis_cache, mock_redis_client):
        """Test successful Redis client creation."""
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            client = await redis_cache._get_redis_client()

            assert client == mock_redis_client
            assert redis_cache._redis_client == mock_redis_client
            mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis_client_import_error(self, redis_cache):
        """Test Redis client creation with import error."""
        with patch(
            "redis.asyncio.from_url", side_effect=ImportError("redis not installed")
        ):
            client = await redis_cache._get_redis_client()

            assert client is None
            assert redis_cache.backend == CacheBackend.MEMORY

    @pytest.mark.asyncio
    async def test_get_redis_client_connection_error(
        self, redis_cache, mock_redis_client
    ):
        """Test Redis client creation with connection error."""
        mock_redis_client.ping.side_effect = Exception("Connection failed")

        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            client = await redis_cache._get_redis_client()

            assert client == mock_redis_client
            assert redis_cache.backend == CacheBackend.MEMORY

    @pytest.mark.asyncio
    async def test_memory_cache_set_and_get(self, memory_cache):
        """Test basic set and get operations with memory cache."""
        await memory_cache.set("test_key", "test_value", ttl=3600)

        value = await memory_cache.get("test_key")

        assert value == "test_value"
        assert memory_cache.stats.sets == 1
        assert memory_cache.stats.hits == 1

    @pytest.mark.asyncio
    async def test_memory_cache_get_default(self, memory_cache):
        """Test get with default value when key doesn't exist."""
        value = await memory_cache.get("nonexistent_key", default="default_value")

        assert value == "default_value"
        assert memory_cache.stats.misses == 1

    @pytest.mark.asyncio
    async def test_memory_cache_get_expired(self, memory_cache):
        """Test get with expired entry."""
        # Set entry with very short TTL
        await memory_cache.set("test_key", "test_value", ttl=1)

        # Wait for expiration
        await asyncio.sleep(1.1)

        value = await memory_cache.get("test_key", default="default")

        assert value == "default"
        assert memory_cache.stats.misses == 1

        # Entry should be removed from cache
        full_key = memory_cache._make_key("test_key")
        assert full_key not in memory_cache._memory_cache

    @pytest.mark.asyncio
    async def test_memory_cache_lru_eviction(self, memory_cache):
        """Test LRU eviction when cache is full."""
        memory_cache.max_memory_entries = 3

        # Fill cache to capacity
        await memory_cache.set("key1", "value1")
        await memory_cache.set("key2", "value2")
        await memory_cache.set("key3", "value3")

        # Access key1 to make it recently used
        await memory_cache.get("key1")

        # Add another key, should evict key2 (least recently used)
        await memory_cache.set("key4", "value4")

        assert await memory_cache.get("key1") == "value1"  # Still there
        assert await memory_cache.get("key2", "missing") == "missing"  # Evicted
        assert await memory_cache.get("key3") == "value3"  # Still there
        assert await memory_cache.get("key4") == "value4"  # New entry

        assert memory_cache.stats.evictions == 1

    @pytest.mark.asyncio
    async def test_memory_cache_delete(self, memory_cache):
        """Test delete operation with memory cache."""
        await memory_cache.set("test_key", "test_value")

        deleted = await memory_cache.delete("test_key")

        assert deleted is True
        assert memory_cache.stats.deletes == 1

        value = await memory_cache.get("test_key", "missing")
        assert value == "missing"

    @pytest.mark.asyncio
    async def test_memory_cache_delete_nonexistent(self, memory_cache):
        """Test delete operation with non-existent key."""
        deleted = await memory_cache.delete("nonexistent_key")

        assert deleted is False

    @pytest.mark.asyncio
    async def test_memory_cache_exists(self, memory_cache):
        """Test exists operation with memory cache."""
        await memory_cache.set("test_key", "test_value")

        exists = await memory_cache.exists("test_key")
        assert exists is True

        exists = await memory_cache.exists("nonexistent_key")
        assert exists is False

    @pytest.mark.asyncio
    async def test_memory_cache_exists_expired(self, memory_cache):
        """Test exists operation with expired entry."""
        await memory_cache.set("test_key", "test_value", ttl=1)

        # Wait for expiration
        await asyncio.sleep(1.1)

        exists = await memory_cache.exists("test_key")
        assert exists is False

        # Entry should be cleaned up
        full_key = memory_cache._make_key("test_key")
        assert full_key not in memory_cache._memory_cache

    @pytest.mark.asyncio
    async def test_memory_cache_clear_all(self, memory_cache):
        """Test clearing all entries from memory cache."""
        await memory_cache.set("key1", "value1")
        await memory_cache.set("key2", "value2")
        await memory_cache.set("key3", "value3")

        cleared = await memory_cache.clear()

        assert cleared == 3
        assert len(memory_cache._memory_cache) == 0
        assert len(memory_cache._access_order) == 0

    @pytest.mark.asyncio
    async def test_memory_cache_clear_pattern(self, memory_cache):
        """Test clearing entries by pattern from memory cache."""
        await memory_cache.set("user:1", "user1")
        await memory_cache.set("user:2", "user2")
        await memory_cache.set("product:1", "product1")

        cleared = await memory_cache.clear("user:*")

        assert cleared == 2
        assert await memory_cache.get("user:1", "missing") == "missing"
        assert await memory_cache.get("user:2", "missing") == "missing"
        assert await memory_cache.get("product:1") == "product1"

    @pytest.mark.asyncio
    async def test_redis_cache_operations(self, redis_cache, mock_redis_client):
        """Test Redis cache operations."""
        with patch.object(
            redis_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            # Test set
            await redis_cache.set("test_key", "test_value", ttl=3600)

            mock_redis_client.setex.assert_called_once()
            call_args = mock_redis_client.setex.call_args[0]
            assert call_args[0] == "ccdata_ingestion:test_key"
            assert call_args[1] == 3600

            # Test get
            mock_redis_client.get.return_value = json.dumps("test_value").encode(
                "utf-8"
            )
            value = await redis_cache.get("test_key")

            assert value == "test_value"
            mock_redis_client.get.assert_called_once_with("ccdata_ingestion:test_key")

    @pytest.mark.asyncio
    async def test_redis_cache_get_miss(self, redis_cache, mock_redis_client):
        """Test Redis cache get with cache miss."""
        mock_redis_client.get.return_value = None

        with patch.object(
            redis_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            value = await redis_cache.get("test_key", "default")

            assert value == "default"
            assert redis_cache.stats.misses == 1

    @pytest.mark.asyncio
    async def test_redis_cache_delete(self, redis_cache, mock_redis_client):
        """Test Redis cache delete operation."""
        mock_redis_client.delete.return_value = 1

        with patch.object(
            redis_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            deleted = await redis_cache.delete("test_key")

            assert deleted is True
            mock_redis_client.delete.assert_called_once_with(
                "ccdata_ingestion:test_key"
            )

    @pytest.mark.asyncio
    async def test_redis_cache_exists(self, redis_cache, mock_redis_client):
        """Test Redis cache exists operation."""
        mock_redis_client.exists.return_value = 1

        with patch.object(
            redis_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            exists = await redis_cache.exists("test_key")

            assert exists is True
            mock_redis_client.exists.assert_called_once_with(
                "ccdata_ingestion:test_key"
            )

    @pytest.mark.asyncio
    async def test_redis_cache_clear_all(self, redis_cache, mock_redis_client):
        """Test Redis cache clear all operation."""
        mock_redis_client.keys.return_value = [
            "ccdata_ingestion:key1",
            "ccdata_ingestion:key2",
        ]
        mock_redis_client.delete.return_value = 2

        with patch.object(
            redis_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            cleared = await redis_cache.clear()

            assert cleared == 2
            mock_redis_client.keys.assert_called_once_with("ccdata_ingestion:*")
            mock_redis_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_cache_clear_pattern(self, redis_cache, mock_redis_client):
        """Test Redis cache clear with pattern."""
        mock_redis_client.keys.return_value = [
            "ccdata_ingestion:user:1",
            "ccdata_ingestion:user:2",
        ]
        mock_redis_client.delete.return_value = 2

        with patch.object(
            redis_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            cleared = await redis_cache.clear("user:*")

            assert cleared == 2
            mock_redis_client.keys.assert_called_once_with("ccdata_ingestion:user:*")

    @pytest.mark.asyncio
    async def test_hybrid_cache_memory_hit(self, hybrid_cache, mock_redis_client):
        """Test hybrid cache with memory hit."""
        with patch.object(
            hybrid_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            # Set value (goes to both memory and Redis)
            await hybrid_cache.set("test_key", "test_value")

            # Get value (should hit memory cache first)
            value = await hybrid_cache.get("test_key")

            assert value == "test_value"
            assert hybrid_cache.stats.hits == 1

            # Redis get should not be called since memory cache hit
            mock_redis_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_hybrid_cache_redis_fallback(self, hybrid_cache, mock_redis_client):
        """Test hybrid cache with Redis fallback."""
        mock_redis_client.get.return_value = json.dumps("redis_value").encode("utf-8")

        with patch.object(
            hybrid_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            # Get value that's not in memory cache
            value = await hybrid_cache.get("test_key")

            assert value == "redis_value"
            assert hybrid_cache.stats.hits == 1

            # Should have called Redis
            mock_redis_client.get.assert_called_once()

            # Value should now be in memory cache too
            full_key = hybrid_cache._make_key("test_key")
            assert full_key in hybrid_cache._memory_cache

    @pytest.mark.asyncio
    async def test_hybrid_cache_delete_both(self, hybrid_cache, mock_redis_client):
        """Test hybrid cache delete from both backends."""
        mock_redis_client.delete.return_value = 1

        with patch.object(
            hybrid_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            # Set value in memory cache
            await hybrid_cache._set_memory_cache("test_key", "test_value", 3600)

            # Delete should remove from both
            deleted = await hybrid_cache.delete("test_key")

            assert deleted is True
            mock_redis_client.delete.assert_called_once()

            # Should be removed from memory cache
            full_key = hybrid_cache._make_key("test_key")
            assert full_key not in hybrid_cache._memory_cache

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, memory_cache):
        """Test get_or_set with cache hit."""
        await memory_cache.set("test_key", "cached_value")

        def value_func():
            return "computed_value"

        value = await memory_cache.get_or_set("test_key", value_func)

        assert value == "cached_value"
        # Function should not be called
        assert memory_cache.stats.hits == 2  # One from set, one from get_or_set

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, memory_cache):
        """Test get_or_set with cache miss."""

        def value_func():
            return "computed_value"

        value = await memory_cache.get_or_set("test_key", value_func, ttl=1800)

        assert value == "computed_value"
        assert memory_cache.stats.misses == 1
        assert memory_cache.stats.sets == 1

        # Value should now be cached
        cached_value = await memory_cache.get("test_key")
        assert cached_value == "computed_value"

    @pytest.mark.asyncio
    async def test_get_or_set_async_function(self, memory_cache):
        """Test get_or_set with async value function."""

        async def async_value_func():
            await asyncio.sleep(0.01)
            return "async_computed_value"

        value = await memory_cache.get_or_set("test_key", async_value_func)

        assert value == "async_computed_value"

    @pytest.mark.asyncio
    async def test_get_or_set_exception(self, memory_cache):
        """Test get_or_set with exception in value function."""

        def failing_func():
            raise Exception("Computation failed")

        with pytest.raises(Exception, match="Computation failed"):
            await memory_cache.get_or_set("test_key", failing_func)

        # Key should not be cached
        value = await memory_cache.get("test_key", "missing")
        assert value == "missing"

    @pytest.mark.asyncio
    async def test_warm_cache(self, memory_cache):
        """Test cache warming functionality."""
        warming_data = {"key1": "value1", "key2": "value2", "key3": "value3"}

        await memory_cache.warm_cache(warming_data, ttl=3600)

        # All keys should be cached
        for key, expected_value in warming_data.items():
            value = await memory_cache.get(key)
            assert value == expected_value

    @pytest.mark.asyncio
    async def test_warm_cache_with_functions(self, memory_cache):
        """Test cache warming with value functions."""

        def get_user_data(user_id):
            return f"user_data_{user_id}"

        warming_config = {
            "user:1": lambda: get_user_data(1),
            "user:2": lambda: get_user_data(2),
        }

        await memory_cache.warm_cache(warming_config)

        assert await memory_cache.get("user:1") == "user_data_1"
        assert await memory_cache.get("user:2") == "user_data_2"

    @pytest.mark.asyncio
    async def test_warm_single_key_exception(self, memory_cache):
        """Test cache warming with exception in single key."""

        def failing_func():
            raise Exception("Failed to get value")

        # Should not raise exception
        await memory_cache._warm_single_key("test_key", failing_func, 3600)

        # Key should not be cached
        value = await memory_cache.get("test_key", "missing")
        assert value == "missing"

    def test_add_invalidation_pattern(self, memory_cache):
        """Test adding invalidation patterns."""
        memory_cache.add_invalidation_pattern("user:*", ["user:1", "user:2", "user:3"])

        assert "user:*" in memory_cache._invalidation_patterns
        assert memory_cache._invalidation_patterns["user:*"] == {
            "user:1",
            "user:2",
            "user:3",
        }

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, memory_cache):
        """Test pattern-based invalidation."""
        # Set up cache entries
        await memory_cache.set("user:1", "data1")
        await memory_cache.set("user:2", "data2")
        await memory_cache.set("product:1", "product_data")

        # Set up invalidation pattern
        memory_cache.add_invalidation_pattern("user_update", ["user:1", "user:2"])

        # Invalidate pattern
        await memory_cache.invalidate_pattern("user_update")

        # User keys should be invalidated
        assert await memory_cache.get("user:1", "missing") == "missing"
        assert await memory_cache.get("user:2", "missing") == "missing"

        # Product key should remain
        assert await memory_cache.get("product:1") == "product_data"

    @pytest.mark.asyncio
    async def test_get_stats(self, memory_cache):
        """Test cache statistics retrieval."""
        # Perform some operations
        await memory_cache.set("key1", "value1")
        await memory_cache.set("key2", "value2")
        await memory_cache.get("key1")
        await memory_cache.get("nonexistent", "default")
        await memory_cache.delete("key2")

        stats = await memory_cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 2
        assert stats["deletes"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["total_keys"] == 1
        assert "memory_usage_bytes" in stats

    @pytest.mark.asyncio
    async def test_background_cleanup(self, memory_cache):
        """Test background cleanup task."""
        await memory_cache.start_background_cleanup()

        assert memory_cache._cleanup_task is not None
        assert not memory_cache._cleanup_task.done()

        await memory_cache.stop_background_cleanup()

        assert memory_cache._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, memory_cache):
        """Test cleanup of expired entries."""
        # Add entries with different TTLs
        await memory_cache.set("short_ttl", "value1", ttl=1)
        await memory_cache.set("long_ttl", "value2", ttl=3600)

        # Wait for short TTL to expire
        await asyncio.sleep(1.1)

        # Run cleanup
        await memory_cache._cleanup_expired_entries()

        # Short TTL entry should be removed
        assert await memory_cache.get("short_ttl", "missing") == "missing"

        # Long TTL entry should remain
        assert await memory_cache.get("long_ttl") == "value2"

    @pytest.mark.asyncio
    async def test_close(self, memory_cache):
        """Test cache cleanup on close."""
        await memory_cache.set("test_key", "test_value")
        await memory_cache.start_background_cleanup()

        await memory_cache.close()

        assert memory_cache._shutdown_event.is_set()
        if memory_cache._cleanup_task:
            assert memory_cache._cleanup_task.cancelled()

    @pytest.mark.asyncio
    async def test_error_handling_redis_unavailable(self, redis_cache):
        """Test error handling when Redis is unavailable."""
        with patch.object(redis_cache, "_get_redis_client", return_value=None):
            # Operations should not fail, just return defaults
            value = await redis_cache.get("test_key", "default")
            assert value == "default"

            success = await redis_cache.set("test_key", "value")
            assert success is True  # Should succeed even without Redis

            deleted = await redis_cache.delete("test_key")
            assert deleted is False

            exists = await redis_cache.exists("test_key")
            assert exists is False

    @pytest.mark.asyncio
    async def test_concurrent_access(self, memory_cache):
        """Test concurrent cache access."""

        async def set_values(start_idx):
            for i in range(start_idx, start_idx + 100):
                await memory_cache.set(f"key_{i}", f"value_{i}")

        async def get_values(start_idx):
            results = []
            for i in range(start_idx, start_idx + 100):
                value = await memory_cache.get(f"key_{i}", "missing")
                results.append(value)
            return results

        # Run concurrent operations
        await asyncio.gather(set_values(0), set_values(100), set_values(200))

        # Verify all values were set correctly
        results = await get_values(0)
        assert all(result != "missing" for result in results[:100])

    @pytest.mark.asyncio
    async def test_large_value_handling(self, memory_cache):
        """Test handling of large values."""
        # Create a large value (1MB string)
        large_value = "x" * (1024 * 1024)

        await memory_cache.set("large_key", large_value)

        retrieved_value = await memory_cache.get("large_key")
        assert retrieved_value == large_value
        assert memory_cache.stats.sets == 1
        assert memory_cache.stats.hits == 1

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, memory_cache):
        """Test cache behavior under memory pressure."""
        memory_cache.max_memory_entries = 10

        # Fill cache beyond capacity
        for i in range(20):
            await memory_cache.set(f"key_{i}", f"value_{i}")

        # Should have evicted older entries
        assert len(memory_cache._memory_cache) <= 10
        assert memory_cache.stats.evictions > 0

        # Most recent entries should still be there
        for i in range(15, 20):
            value = await memory_cache.get(f"key_{i}")
            assert value == f"value_{i}"

    @pytest.mark.asyncio
    async def test_ttl_edge_cases(self, memory_cache):
        """Test TTL edge cases."""
        # Test with TTL of 0 (should not expire)
        await memory_cache.set("no_expire", "value", ttl=0)

        # Wait a bit
        await asyncio.sleep(0.1)

        value = await memory_cache.get("no_expire")
        assert value == "value"

        # Test with negative TTL (should expire immediately)
        await memory_cache.set("immediate_expire", "value", ttl=-1)

        value = await memory_cache.get("immediate_expire", "missing")
        assert value == "missing"

    @pytest.mark.asyncio
    async def test_key_pattern_matching(self, memory_cache):
        """Test key pattern matching functionality."""
        await memory_cache.set("user:123:profile", "profile_data")
        await memory_cache.set("user:456:profile", "profile_data2")
        await memory_cache.set("product:789", "product_data")

        # Test pattern matching
        assert memory_cache._key_matches_pattern(
            "ccdata_ingestion:user:123:profile", "user:*:profile"
        )

        assert not memory_cache._key_matches_pattern(
            "ccdata_ingestion:product:789", "user:*:profile"
        )

    @pytest.mark.asyncio
    async def test_serialization_error_handling(self, memory_cache):
        """Test handling of serialization errors."""

        # Create an object that can't be JSON serialized
        class UnserializableObject:
            def __init__(self):
                self.func = lambda x: x

        obj = UnserializableObject()

        # Should handle serialization error gracefully
        success = await memory_cache.set("bad_key", obj)

        # With JSON serialization, this should fail
        if memory_cache.serialization_format == SerializationFormat.JSON:
            assert success is False
            assert memory_cache.stats.errors > 0

    @pytest.mark.asyncio
    async def test_cache_statistics_accuracy(self, memory_cache):
        """Test accuracy of cache statistics."""
        initial_stats = await memory_cache.get_stats()

        # Perform known operations
        await memory_cache.set("key1", "value1")  # +1 set
        await memory_cache.set("key2", "value2")  # +1 set
        await memory_cache.get("key1")  # +1 hit
        await memory_cache.get("key3", "default")  # +1 miss
        await memory_cache.delete("key2")  # +1 delete

        final_stats = await memory_cache.get_stats()

        assert final_stats["sets"] == initial_stats["sets"] + 2
        assert final_stats["hits"] == initial_stats["hits"] + 1
        assert final_stats["misses"] == initial_stats["misses"] + 1
        assert final_stats["deletes"] == initial_stats["deletes"] + 1

    @pytest.mark.asyncio
    async def test_cache_entry_metadata(self, memory_cache):
        """Test cache entry metadata handling."""
        metadata = {
            "source": "api",
            "version": "1.0",
            "tags": ["important", "user_data"],
        }

        await memory_cache.set("meta_key", "value", metadata=metadata)

        # Check that metadata is stored
        full_key = memory_cache._make_key("meta_key")
        entry = memory_cache._memory_cache[full_key]

        assert entry.metadata == metadata
        assert entry.metadata["source"] == "api"
        assert "important" in entry.metadata["tags"]

    @pytest.mark.asyncio
    async def test_access_tracking(self, memory_cache):
        """Test access count and timestamp tracking."""
        await memory_cache.set("tracked_key", "value")

        full_key = memory_cache._make_key("tracked_key")
        entry = memory_cache._memory_cache[full_key]

        initial_count = entry.access_count
        initial_time = entry.last_accessed

        # Access the key multiple times
        await memory_cache.get("tracked_key")
        await memory_cache.get("tracked_key")
        await memory_cache.get("tracked_key")

        assert entry.access_count == initial_count + 3
        assert entry.last_accessed > initial_time

    @pytest.mark.asyncio
    async def test_cache_warming_edge_cases(self, memory_cache):
        """Test cache warming edge cases."""
        # Test warming with empty data
        await memory_cache.warm_cache({})

        # Test warming with None values
        warming_data = {
            "null_key": None,
            "empty_string": "",
            "zero_value": 0,
            "false_value": False,
        }

        await memory_cache.warm_cache(warming_data)

        # All values should be cached, including falsy ones
        assert await memory_cache.get("null_key") is None
        assert await memory_cache.get("empty_string") == ""
        assert await memory_cache.get("zero_value") == 0
        assert await memory_cache.get("false_value") is False

    @pytest.mark.asyncio
    async def test_redis_connection_recovery(self, redis_cache, mock_redis_client):
        """Test Redis connection recovery after failure."""
        # Initially working Redis client
        with patch.object(
            redis_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            await redis_cache.set("test_key", "test_value")
            mock_redis_client.setex.assert_called_once()

        # Simulate Redis failure
        mock_redis_client.get.side_effect = Exception("Redis connection lost")

        with patch.object(
            redis_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            # Should handle error gracefully
            value = await redis_cache.get("test_key", "default")
            assert value == "default"
            assert redis_cache.stats.errors > 0

    @pytest.mark.asyncio
    async def test_hybrid_cache_consistency(self, hybrid_cache, mock_redis_client):
        """Test consistency between memory and Redis in hybrid cache."""
        with patch.object(
            hybrid_cache, "_get_redis_client", return_value=mock_redis_client
        ):
            # Set value
            await hybrid_cache.set("consistency_key", "original_value")

            # Modify only Redis value (simulate external change)
            mock_redis_client.get.return_value = json.dumps("modified_value").encode(
                "utf-8"
            )

            # Clear memory cache to force Redis lookup
            await hybrid_cache.clear()

            # Should get the modified value from Redis
            value = await hybrid_cache.get("consistency_key")
            assert value == "modified_value"

            # Value should now be in memory cache too
            memory_value = await hybrid_cache.get("consistency_key")
            assert memory_value == "modified_value"

            # Redis should not be called again (memory hit)
            mock_redis_client.get.assert_called_once()
