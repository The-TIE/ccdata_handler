"""
Caching layer for the unified data ingestion pipeline.

This module provides a comprehensive caching system with Redis-compatible caching,
TTL support, cache warming strategies, and cache invalidation patterns to improve
performance and reduce API calls for frequently accessed metadata.
"""

import asyncio
import json
import pickle
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import threading
from collections import defaultdict
import logging

from ..logger_config import setup_logger


logger = setup_logger(__name__)


class CacheBackend(Enum):
    """Supported cache backends."""

    MEMORY = "memory"
    REDIS = "redis"
    HYBRID = "hybrid"


class SerializationFormat(Enum):
    """Supported serialization formats."""

    JSON = "json"
    PICKLE = "pickle"


@dataclass
class CacheEntry:
    """Represents a cache entry."""

    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def touch(self):
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)


@dataclass
class CacheStats:
    """Cache statistics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    errors: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheManager:
    """
    Comprehensive cache manager for frequently accessed metadata.

    Supports multiple backends (memory, Redis), TTL-based expiration,
    cache warming, and intelligent invalidation patterns.
    """

    def __init__(
        self,
        backend: CacheBackend = CacheBackend.MEMORY,
        default_ttl: int = 3600,  # 1 hour
        max_memory_entries: int = 10000,
        serialization_format: SerializationFormat = SerializationFormat.JSON,
        redis_url: Optional[str] = None,
        key_prefix: str = "ccdata_ingestion:",
    ):
        """
        Initialize the cache manager.

        Args:
            backend: Cache backend to use
            default_ttl: Default TTL in seconds
            max_memory_entries: Maximum entries for memory cache
            serialization_format: Serialization format for values
            redis_url: Redis connection URL (if using Redis backend)
            key_prefix: Prefix for all cache keys
        """
        self.backend = backend
        self.default_ttl = default_ttl
        self.max_memory_entries = max_memory_entries
        self.serialization_format = serialization_format
        self.key_prefix = key_prefix
        self.logger = logger

        # Memory cache storage
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU eviction

        # Redis client (initialized lazily)
        self._redis_client = None
        self._redis_url = redis_url

        # Statistics
        self.stats = CacheStats()

        # Thread safety
        self._lock = threading.RLock()

        # Cache warming and invalidation
        self._warming_tasks: Dict[str, asyncio.Task] = {}
        self._invalidation_patterns: Dict[str, Set[str]] = defaultdict(set)

        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        self.logger.info(f"CacheManager initialized with backend: {backend.value}")

    async def _get_redis_client(self):
        """Get or create Redis client."""
        if self._redis_client is None and self._redis_url:
            try:
                import redis.asyncio as redis

                self._redis_client = redis.from_url(self._redis_url)
                await self._redis_client.ping()
                self.logger.info("Redis client connected successfully")
            except ImportError:
                self.logger.error(
                    "redis package not installed, falling back to memory cache"
                )
                self.backend = CacheBackend.MEMORY
            except Exception as e:
                self.logger.error(
                    f"Failed to connect to Redis: {e}, falling back to memory cache"
                )
                self.backend = CacheBackend.MEMORY

        return self._redis_client

    def _make_key(self, key: str) -> str:
        """Create a full cache key with prefix."""
        return f"{self.key_prefix}{key}"

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize a value for storage."""
        if self.serialization_format == SerializationFormat.JSON:
            return json.dumps(value, default=str).encode("utf-8")
        else:
            return pickle.dumps(value)

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize a value from storage."""
        if self.serialization_format == SerializationFormat.JSON:
            return json.loads(data.decode("utf-8"))
        else:
            return pickle.loads(data)

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        full_key = self._make_key(key)

        try:
            if (
                self.backend == CacheBackend.MEMORY
                or self.backend == CacheBackend.HYBRID
            ):
                # Try memory cache first
                with self._lock:
                    if full_key in self._memory_cache:
                        entry = self._memory_cache[full_key]

                        if entry.is_expired():
                            # Remove expired entry
                            del self._memory_cache[full_key]
                            if full_key in self._access_order:
                                self._access_order.remove(full_key)
                            self.stats.misses += 1
                            return default

                        # Update access statistics
                        entry.touch()

                        # Update LRU order
                        if full_key in self._access_order:
                            self._access_order.remove(full_key)
                        self._access_order.append(full_key)

                        self.stats.hits += 1
                        return entry.value

            if (
                self.backend == CacheBackend.REDIS
                or self.backend == CacheBackend.HYBRID
            ):
                # Try Redis cache
                redis_client = await self._get_redis_client()
                if redis_client:
                    data = await redis_client.get(full_key)
                    if data:
                        value = self._deserialize_value(data)
                        self.stats.hits += 1

                        # If hybrid, also store in memory cache
                        if self.backend == CacheBackend.HYBRID:
                            await self._set_memory_cache(key, value, self.default_ttl)

                        return value

            self.stats.misses += 1
            return default

        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {e}")
            self.stats.errors += 1
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for default)
            metadata: Optional metadata for the cache entry

        Returns:
            True if successful, False otherwise
        """
        if ttl is None:
            ttl = self.default_ttl

        full_key = self._make_key(key)

        try:
            if (
                self.backend == CacheBackend.MEMORY
                or self.backend == CacheBackend.HYBRID
            ):
                await self._set_memory_cache(key, value, ttl, metadata)

            if (
                self.backend == CacheBackend.REDIS
                or self.backend == CacheBackend.HYBRID
            ):
                redis_client = await self._get_redis_client()
                if redis_client:
                    serialized_value = self._serialize_value(value)
                    await redis_client.setex(full_key, ttl, serialized_value)

            self.stats.sets += 1
            return True

        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {e}")
            self.stats.errors += 1
            return False

    async def _set_memory_cache(
        self,
        key: str,
        value: Any,
        ttl: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Set a value in the memory cache."""
        full_key = self._make_key(key)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl) if ttl > 0 else None

        entry = CacheEntry(
            key=full_key,
            value=value,
            created_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        with self._lock:
            # Add/update entry
            self._memory_cache[full_key] = entry

            # Update access order
            if full_key in self._access_order:
                self._access_order.remove(full_key)
            self._access_order.append(full_key)

            # Evict if necessary
            await self._evict_if_necessary()

    async def _evict_if_necessary(self):
        """Evict entries if cache is full (LRU eviction)."""
        while len(self._memory_cache) > self.max_memory_entries:
            if not self._access_order:
                break

            # Remove least recently used entry
            lru_key = self._access_order.pop(0)
            if lru_key in self._memory_cache:
                del self._memory_cache[lru_key]
                self.stats.evictions += 1

    async def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        full_key = self._make_key(key)

        try:
            deleted = False

            if (
                self.backend == CacheBackend.MEMORY
                or self.backend == CacheBackend.HYBRID
            ):
                with self._lock:
                    if full_key in self._memory_cache:
                        del self._memory_cache[full_key]
                        deleted = True
                    if full_key in self._access_order:
                        self._access_order.remove(full_key)

            if (
                self.backend == CacheBackend.REDIS
                or self.backend == CacheBackend.HYBRID
            ):
                redis_client = await self._get_redis_client()
                if redis_client:
                    result = await redis_client.delete(full_key)
                    deleted = deleted or result > 0

            if deleted:
                self.stats.deletes += 1

            return deleted

        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {e}")
            self.stats.errors += 1
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and is not expired, False otherwise
        """
        full_key = self._make_key(key)

        try:
            if (
                self.backend == CacheBackend.MEMORY
                or self.backend == CacheBackend.HYBRID
            ):
                with self._lock:
                    if full_key in self._memory_cache:
                        entry = self._memory_cache[full_key]
                        if not entry.is_expired():
                            return True
                        else:
                            # Clean up expired entry
                            del self._memory_cache[full_key]
                            if full_key in self._access_order:
                                self._access_order.remove(full_key)

            if (
                self.backend == CacheBackend.REDIS
                or self.backend == CacheBackend.HYBRID
            ):
                redis_client = await self._get_redis_client()
                if redis_client:
                    return await redis_client.exists(full_key) > 0

            return False

        except Exception as e:
            self.logger.error(f"Error checking cache key existence {key}: {e}")
            self.stats.errors += 1
            return False

    async def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries.

        Args:
            pattern: Optional pattern to match keys (None clears all)

        Returns:
            Number of keys cleared
        """
        cleared = 0

        try:
            if (
                self.backend == CacheBackend.MEMORY
                or self.backend == CacheBackend.HYBRID
            ):
                with self._lock:
                    if pattern:
                        # Clear matching keys
                        keys_to_remove = [
                            k
                            for k in self._memory_cache.keys()
                            if self._key_matches_pattern(k, pattern)
                        ]
                        for key in keys_to_remove:
                            del self._memory_cache[key]
                            if key in self._access_order:
                                self._access_order.remove(key)
                            cleared += 1
                    else:
                        # Clear all
                        cleared = len(self._memory_cache)
                        self._memory_cache.clear()
                        self._access_order.clear()

            if (
                self.backend == CacheBackend.REDIS
                or self.backend == CacheBackend.HYBRID
            ):
                redis_client = await self._get_redis_client()
                if redis_client:
                    if pattern:
                        # Use Redis pattern matching
                        search_pattern = self._make_key(pattern)
                        keys = await redis_client.keys(search_pattern)
                        if keys:
                            deleted = await redis_client.delete(*keys)
                            cleared += deleted
                    else:
                        # Clear all keys with our prefix
                        search_pattern = f"{self.key_prefix}*"
                        keys = await redis_client.keys(search_pattern)
                        if keys:
                            deleted = await redis_client.delete(*keys)
                            cleared += deleted

            return cleared

        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            self.stats.errors += 1
            return 0

    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if a key matches a pattern (simple wildcard matching)."""
        import fnmatch

        return fnmatch.fnmatch(key, self._make_key(pattern))

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Get a value from cache or set it using a factory function.

        Args:
            key: Cache key
            factory: Function to generate value if not in cache
            ttl: Time to live in seconds
            metadata: Optional metadata for the cache entry

        Returns:
            Cached or generated value
        """
        # Try to get from cache first
        value = await self.get(key)
        if value is not None:
            return value

        # Generate value using factory
        try:
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()

            # Store in cache
            await self.set(key, value, ttl, metadata)
            return value

        except Exception as e:
            self.logger.error(f"Error in cache factory for key {key}: {e}")
            raise

    async def warm_cache(
        self,
        warming_functions: Dict[str, Callable[[], Any]],
        ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Warm the cache with frequently accessed data.

        Args:
            warming_functions: Dictionary mapping cache keys to functions that generate values
            ttl: Time to live for warmed entries

        Returns:
            Dictionary mapping keys to their cached values
        """
        self.logger.info(f"Starting cache warming for {len(warming_functions)} keys")

        tasks = []
        keys = list(warming_functions.keys())
        for key, factory in warming_functions.items():
            task = asyncio.create_task(self._warm_single_key(key, factory, ttl))
            tasks.append(task)
            self._warming_tasks[key] = task

        # Wait for all warming tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful

        self.logger.info(
            f"Cache warming completed: {successful} successful, {failed} failed"
        )

        # Clean up completed tasks
        for key in list(self._warming_tasks.keys()):
            if self._warming_tasks[key].done():
                del self._warming_tasks[key]

        # Return the results mapped to keys
        result_dict = {}
        for i, key in enumerate(keys):
            if i < len(results) and not isinstance(results[i], Exception):
                result_dict[key] = results[i]
            else:
                result_dict[key] = None

        return result_dict

    async def _warm_single_key(
        self, key: str, factory: Callable[[], Any], ttl: Optional[int]
    ) -> Any:
        """Warm a single cache key."""
        try:
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()

            await self.set(key, value, ttl)
            self.logger.debug(f"Cache warmed for key: {key}")
            return value

        except Exception as e:
            self.logger.error(f"Error warming cache key {key}: {e}")
            raise

    def add_invalidation_pattern(self, pattern: str, keys: List[str]):
        """
        Add an invalidation pattern.

        When any key matching the pattern is updated, all associated keys will be invalidated.

        Args:
            pattern: Pattern to match against
            keys: Keys to invalidate when pattern matches
        """
        self._invalidation_patterns[pattern].update(keys)

    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys associated with a pattern.

        Args:
            pattern: Pattern to invalidate
        """
        if pattern in self._invalidation_patterns:
            keys_to_invalidate = self._invalidation_patterns[pattern]

            tasks = [self.delete(key) for key in keys_to_invalidate]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = sum(1 for r in results if r is True)
            self.logger.info(f"Invalidated {successful} keys for pattern: {pattern}")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        memory_size = 0
        memory_entries = 0

        if self.backend == CacheBackend.MEMORY or self.backend == CacheBackend.HYBRID:
            with self._lock:
                memory_entries = len(self._memory_cache)
                # Estimate memory usage (rough approximation)
                memory_size = sum(
                    len(str(entry.key)) + len(str(entry.value)) + 200  # overhead
                    for entry in self._memory_cache.values()
                )

        return {
            "backend": self.backend.value,
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": self.stats.hit_rate,
            "sets": self.stats.sets,
            "deletes": self.stats.deletes,
            "evictions": self.stats.evictions,
            "errors": self.stats.errors,
            "memory_entries": memory_entries,
            "memory_size_bytes": memory_size,
            "total_keys": memory_entries,  # Alias for backward compatibility
            "memory_usage_bytes": memory_size,  # Alias for backward compatibility
            "total_entries": memory_entries,  # Another common alias
            "max_memory_entries": self.max_memory_entries,
            "warming_tasks": len(self._warming_tasks),
            "invalidation_patterns": len(self._invalidation_patterns),
        }

    async def start_background_cleanup(self):
        """Start background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self.logger.warning("Background cleanup already running")
            return

        self._shutdown_event.clear()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Background cache cleanup started")

    async def stop_background_cleanup(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._shutdown_event.set()
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._cleanup_task.cancel()
            self.logger.info("Background cache cleanup stopped")

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while not self._shutdown_event.is_set():
            try:
                await self._cleanup_expired_entries()
                await asyncio.sleep(300)  # Run every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cache cleanup loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired_entries(self):
        """Clean up expired entries from memory cache."""
        if self.backend == CacheBackend.MEMORY or self.backend == CacheBackend.HYBRID:
            expired_keys = []

            with self._lock:
                for key, entry in self._memory_cache.items():
                    if entry.is_expired():
                        expired_keys.append(key)

                for key in expired_keys:
                    del self._memory_cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)

            if expired_keys:
                self.logger.debug(
                    f"Cleaned up {len(expired_keys)} expired cache entries"
                )

    async def close(self):
        """Close the cache manager and clean up resources."""
        # Stop background tasks
        await self.stop_background_cleanup()

        # Cancel warming tasks
        for task in self._warming_tasks.values():
            if not task.done():
                task.cancel()

        # Close Redis connection
        if self._redis_client:
            await self._redis_client.close()

        self.logger.info("CacheManager closed")


# Convenience functions for common caching patterns


async def cache_exchange_list(
    cache_manager: CacheManager, api_client: Any
) -> List[str]:
    """Cache and return list of exchanges."""
    return await cache_manager.get_or_set(
        "exchanges:all",
        lambda: api_client.get_all_exchanges(),
        ttl=3600,  # 1 hour
    )


async def cache_top_assets(
    cache_manager: CacheManager, api_client: Any, limit: int = 100
) -> List[str]:
    """Cache and return top assets."""
    return await cache_manager.get_or_set(
        f"assets:top:{limit}",
        lambda: api_client.get_top_assets(limit=limit),
        ttl=1800,  # 30 minutes
    )


async def cache_instrument_metadata(
    cache_manager: CacheManager,
    exchange: str,
    instrument: str,
    metadata: Dict[str, Any],
) -> bool:
    """Cache instrument metadata."""
    return await cache_manager.set(
        f"instrument:{exchange}:{instrument}",
        metadata,
        ttl=7200,  # 2 hours
    )


async def get_cached_instrument_metadata(
    cache_manager: CacheManager,
    exchange: str,
    instrument: str,
) -> Optional[Dict[str, Any]]:
    """Get cached instrument metadata."""
    return await cache_manager.get(f"instrument:{exchange}:{instrument}")
