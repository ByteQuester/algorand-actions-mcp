"""
Cache Manager - Intelligent caching and performance optimization for data pipeline
Supports multiple cache backends with TTL, LRU, and advanced cache strategies
"""

import asyncio
import json
import logging
import time
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import OrderedDict, defaultdict
import threading
import weakref
import os
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheBackend(Enum):
    MEMORY = "memory"
    REDIS = "redis"
    FILE = "file"
    HYBRID = "hybrid"


class EvictionPolicy(Enum):
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    FIFO = "fifo"


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    timestamp: datetime
    ttl: Optional[float] = None
    access_count: int = 0
    last_accessed: datetime = None
    size_bytes: int = 0

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp

        # Calculate approximate size
        if self.size_bytes == 0:
            try:
                self.size_bytes = len(pickle.dumps(self.value))
            except:
                self.size_bytes = len(str(self.value))

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl is None:
            return False

        return (datetime.now() - self.timestamp).total_seconds() > self.ttl

    def touch(self):
        """Update access information"""
        self.access_count += 1
        self.last_accessed = datetime.now()


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    avg_access_time: float = 0.0


class MemoryCache:
    """In-memory cache implementation with LRU and TTL support"""

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100,
                 eviction_policy: EvictionPolicy = EvictionPolicy.LRU):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.eviction_policy = eviction_policy

        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats()
        self.lock = threading.RLock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        start_time = time.time()

        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                return None

            entry = self.cache[key]

            # Check expiration
            if entry.is_expired():
                del self.cache[key]
                self.stats.misses += 1
                self.stats.evictions += 1
                return None

            # Update access info
            entry.touch()

            # Move to end for LRU
            if self.eviction_policy == EvictionPolicy.LRU:
                self.cache.move_to_end(key)

            self.stats.hits += 1
            self._update_hit_rate()
            self._update_access_time(time.time() - start_time)

            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in cache"""
        try:
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=datetime.now(),
                ttl=ttl
            )

            with self.lock:
                # Remove existing entry if present
                if key in self.cache:
                    old_entry = self.cache.pop(key)
                    self.stats.size_bytes -= old_entry.size_bytes

                # Check memory limits
                if (self.stats.size_bytes + entry.size_bytes > self.max_memory_bytes or
                    len(self.cache) >= self.max_size):
                    await self._evict_entries()

                # Add new entry
                self.cache[key] = entry
                self.stats.size_bytes += entry.size_bytes
                self.stats.entry_count = len(self.cache)

            return True

        except Exception as e:
            logger.error(f"Failed to set cache entry {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache.pop(key)
                self.stats.size_bytes -= entry.size_bytes
                self.stats.entry_count = len(self.cache)
                return True
            return False

    async def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.stats = CacheStats()

    async def _evict_entries(self):
        """Evict entries based on eviction policy"""
        entries_to_remove = []

        if self.eviction_policy == EvictionPolicy.LRU:
            # Remove oldest accessed entries
            while (len(self.cache) >= self.max_size or
                   self.stats.size_bytes >= self.max_memory_bytes):
                if not self.cache:
                    break
                key, entry = self.cache.popitem(last=False)
                entries_to_remove.append(entry)
                self.stats.size_bytes -= entry.size_bytes

        elif self.eviction_policy == EvictionPolicy.LFU:
            # Remove least frequently used entries
            sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].access_count)
            while (len(self.cache) >= self.max_size or
                   self.stats.size_bytes >= self.max_memory_bytes):
                if not sorted_entries:
                    break
                key, entry = sorted_entries.pop(0)
                if key in self.cache:
                    del self.cache[key]
                    entries_to_remove.append(entry)
                    self.stats.size_bytes -= entry.size_bytes

        elif self.eviction_policy == EvictionPolicy.TTL:
            # Remove expired entries first
            current_time = datetime.now()
            expired_keys = []

            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                entry = self.cache.pop(key)
                entries_to_remove.append(entry)
                self.stats.size_bytes -= entry.size_bytes

        elif self.eviction_policy == EvictionPolicy.FIFO:
            # Remove oldest entries by timestamp
            while (len(self.cache) >= self.max_size or
                   self.stats.size_bytes >= self.max_memory_bytes):
                if not self.cache:
                    break
                key, entry = self.cache.popitem(last=False)
                entries_to_remove.append(entry)
                self.stats.size_bytes -= entry.size_bytes

        self.stats.evictions += len(entries_to_remove)
        self.stats.entry_count = len(self.cache)

    def _update_hit_rate(self):
        """Update cache hit rate"""
        total_requests = self.stats.hits + self.stats.misses
        if total_requests > 0:
            self.stats.hit_rate = self.stats.hits / total_requests

    def _update_access_time(self, access_time: float):
        """Update average access time"""
        # Simple moving average
        alpha = 0.1
        self.stats.avg_access_time = (alpha * access_time +
                                    (1 - alpha) * self.stats.avg_access_time)

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self.lock:
            return CacheStats(
                hits=self.stats.hits,
                misses=self.stats.misses,
                evictions=self.stats.evictions,
                size_bytes=self.stats.size_bytes,
                entry_count=self.stats.entry_count,
                hit_rate=self.stats.hit_rate,
                avg_access_time=self.stats.avg_access_time
            )


class FileCache:
    """File-based cache implementation"""

    def __init__(self, cache_dir: Optional[str] = None, max_files: int = 10000):
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "algorand_cache")
        self.max_files = max_files
        self.stats = CacheStats()

        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        """Get file path for cache key"""
        # Use hash to create safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")

    def _get_metadata_path(self, key: str) -> str:
        """Get metadata file path for cache key"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.meta")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from file cache"""
        start_time = time.time()

        try:
            file_path = self._get_file_path(key)
            meta_path = self._get_metadata_path(key)

            if not os.path.exists(file_path) or not os.path.exists(meta_path):
                self.stats.misses += 1
                return None

            # Load metadata
            with open(meta_path, 'r') as f:
                metadata = json.load(f)

            # Check expiration
            if metadata.get('ttl'):
                created_time = datetime.fromisoformat(metadata['timestamp'])
                if (datetime.now() - created_time).total_seconds() > metadata['ttl']:
                    # Remove expired files
                    os.remove(file_path)
                    os.remove(meta_path)
                    self.stats.misses += 1
                    self.stats.evictions += 1
                    return None

            # Load value
            with open(file_path, 'rb') as f:
                value = pickle.load(f)

            # Update access info in metadata
            metadata['access_count'] = metadata.get('access_count', 0) + 1
            metadata['last_accessed'] = datetime.now().isoformat()

            with open(meta_path, 'w') as f:
                json.dump(metadata, f)

            self.stats.hits += 1
            self._update_hit_rate()
            self._update_access_time(time.time() - start_time)

            return value

        except Exception as e:
            logger.error(f"Failed to get from file cache {key}: {e}")
            self.stats.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in file cache"""
        try:
            file_path = self._get_file_path(key)
            meta_path = self._get_metadata_path(key)

            # Check file count limit
            await self._cleanup_if_needed()

            # Save value
            with open(file_path, 'wb') as f:
                pickle.dump(value, f)

            # Save metadata
            metadata = {
                'key': key,
                'timestamp': datetime.now().isoformat(),
                'ttl': ttl,
                'access_count': 0,
                'last_accessed': datetime.now().isoformat(),
                'size_bytes': os.path.getsize(file_path)
            }

            with open(meta_path, 'w') as f:
                json.dump(metadata, f)

            return True

        except Exception as e:
            logger.error(f"Failed to set file cache {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete entry from file cache"""
        try:
            file_path = self._get_file_path(key)
            meta_path = self._get_metadata_path(key)

            removed = False
            if os.path.exists(file_path):
                os.remove(file_path)
                removed = True

            if os.path.exists(meta_path):
                os.remove(meta_path)
                removed = True

            return removed

        except Exception as e:
            logger.error(f"Failed to delete from file cache {key}: {e}")
            return False

    async def clear(self):
        """Clear all cache files"""
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if filename.endswith(('.cache', '.meta')):
                    os.remove(file_path)

            self.stats = CacheStats()

        except Exception as e:
            logger.error(f"Failed to clear file cache: {e}")

    async def _cleanup_if_needed(self):
        """Clean up old files if needed"""
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.cache')]

            if len(cache_files) >= self.max_files:
                # Get file modification times
                file_times = []
                for cache_file in cache_files:
                    file_path = os.path.join(self.cache_dir, cache_file)
                    mtime = os.path.getmtime(file_path)
                    file_times.append((mtime, cache_file))

                # Sort by modification time and remove oldest
                file_times.sort()
                files_to_remove = len(cache_files) - self.max_files + 100  # Remove extra files

                for _, cache_file in file_times[:files_to_remove]:
                    file_path = os.path.join(self.cache_dir, cache_file)
                    meta_file = cache_file.replace('.cache', '.meta')
                    meta_path = os.path.join(self.cache_dir, meta_file)

                    if os.path.exists(file_path):
                        os.remove(file_path)
                    if os.path.exists(meta_path):
                        os.remove(meta_path)

                    self.stats.evictions += 1

        except Exception as e:
            logger.error(f"Failed to cleanup file cache: {e}")

    def _update_hit_rate(self):
        """Update cache hit rate"""
        total_requests = self.stats.hits + self.stats.misses
        if total_requests > 0:
            self.stats.hit_rate = self.stats.hits / total_requests

    def _update_access_time(self, access_time: float):
        """Update average access time"""
        alpha = 0.1
        self.stats.avg_access_time = (alpha * access_time +
                                    (1 - alpha) * self.stats.avg_access_time)

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return CacheStats(
            hits=self.stats.hits,
            misses=self.stats.misses,
            evictions=self.stats.evictions,
            size_bytes=self.stats.size_bytes,
            entry_count=len([f for f in os.listdir(self.cache_dir) if f.endswith('.cache')]),
            hit_rate=self.stats.hit_rate,
            avg_access_time=self.stats.avg_access_time
        )


class CacheManager:
    """
    Main cache manager that coordinates multiple cache backends
    """

    def __init__(self, backend: CacheBackend = CacheBackend.HYBRID,
                 memory_cache_size: int = 1000,
                 memory_cache_mb: int = 100,
                 file_cache_dir: Optional[str] = None,
                 file_cache_max_files: int = 10000):

        self.backend = backend
        self.memory_cache = MemoryCache(memory_cache_size, memory_cache_mb)
        self.file_cache = FileCache(file_cache_dir, file_cache_max_files)

        # Cache key patterns for intelligent routing
        self.hot_patterns = [
            "price:",
            "account:",
            "market:",
            "yield:"
        ]

        self.cold_patterns = [
            "history:",
            "archive:",
            "backup:"
        ]

        # Performance monitoring
        self.performance_stats = defaultdict(list)

    async def initialize(self):
        """Initialize cache manager"""
        logger.info(f"Cache Manager initialized with backend: {self.backend.value}")

    async def shutdown(self):
        """Shutdown cache manager"""
        logger.info("Cache Manager shutdown complete")

    def _should_use_memory_cache(self, key: str) -> bool:
        """Determine if key should use memory cache"""
        if self.backend == CacheBackend.MEMORY:
            return True
        elif self.backend == CacheBackend.FILE:
            return False
        elif self.backend == CacheBackend.HYBRID:
            # Use memory for hot data, file for cold data
            for pattern in self.hot_patterns:
                if key.startswith(pattern):
                    return True
            return False

        return True

    async def get(self, key: str) -> Optional[Any]:
        """Get value from appropriate cache backend"""
        start_time = time.time()

        try:
            if self._should_use_memory_cache(key):
                # Try memory cache first
                value = await self.memory_cache.get(key)
                if value is not None:
                    self._record_performance('memory_get', time.time() - start_time)
                    return value

                # Try file cache if hybrid
                if self.backend == CacheBackend.HYBRID:
                    value = await self.file_cache.get(key)
                    if value is not None:
                        # Promote to memory cache
                        await self.memory_cache.set(key, value)
                        self._record_performance('file_get_promoted', time.time() - start_time)
                        return value
            else:
                # Use file cache
                value = await self.file_cache.get(key)
                if value is not None:
                    self._record_performance('file_get', time.time() - start_time)
                    return value

            self._record_performance('cache_miss', time.time() - start_time)
            return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in appropriate cache backend"""
        start_time = time.time()

        try:
            success = False

            if self._should_use_memory_cache(key):
                success = await self.memory_cache.set(key, value, ttl)
                self._record_performance('memory_set', time.time() - start_time)

                # Also set in file cache for persistence if hybrid
                if self.backend == CacheBackend.HYBRID and success:
                    await self.file_cache.set(key, value, ttl)
            else:
                success = await self.file_cache.set(key, value, ttl)
                self._record_performance('file_set', time.time() - start_time)

            return success

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete from all cache backends"""
        memory_deleted = await self.memory_cache.delete(key)
        file_deleted = await self.file_cache.delete(key)
        return memory_deleted or file_deleted

    async def clear(self):
        """Clear all caches"""
        await self.memory_cache.clear()
        await self.file_cache.clear()
        self.performance_stats.clear()

    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values efficiently"""
        results = {}

        # Batch get from memory cache
        memory_keys = [key for key in keys if self._should_use_memory_cache(key)]
        file_keys = [key for key in keys if not self._should_use_memory_cache(key)]

        # Get from memory cache
        memory_tasks = [self.memory_cache.get(key) for key in memory_keys]
        if memory_tasks:
            memory_results = await asyncio.gather(*memory_tasks, return_exceptions=True)
            for i, key in enumerate(memory_keys):
                if not isinstance(memory_results[i], Exception) and memory_results[i] is not None:
                    results[key] = memory_results[i]

        # Get from file cache
        file_tasks = [self.file_cache.get(key) for key in file_keys]
        if file_tasks:
            file_results = await asyncio.gather(*file_tasks, return_exceptions=True)
            for i, key in enumerate(file_keys):
                if not isinstance(file_results[i], Exception) and file_results[i] is not None:
                    results[key] = file_results[i]

        return results

    async def set_multiple(self, data: Dict[str, Any], ttl: Optional[float] = None) -> Dict[str, bool]:
        """Set multiple values efficiently"""
        results = {}

        # Separate by cache type
        memory_data = {k: v for k, v in data.items() if self._should_use_memory_cache(k)}
        file_data = {k: v for k, v in data.items() if not self._should_use_memory_cache(k)}

        # Set in memory cache
        memory_tasks = [self.memory_cache.set(k, v, ttl) for k, v in memory_data.items()]
        if memory_tasks:
            memory_results = await asyncio.gather(*memory_tasks, return_exceptions=True)
            for i, key in enumerate(memory_data.keys()):
                results[key] = not isinstance(memory_results[i], Exception) and memory_results[i]

        # Set in file cache
        file_tasks = [self.file_cache.set(k, v, ttl) for k, v in file_data.items()]
        if file_tasks:
            file_results = await asyncio.gather(*file_tasks, return_exceptions=True)
            for i, key in enumerate(file_data.keys()):
                results[key] = not isinstance(file_results[i], Exception) and file_results[i]

        return results

    def _record_performance(self, operation: str, duration: float):
        """Record performance metrics"""
        self.performance_stats[operation].append(duration)

        # Keep only recent measurements
        if len(self.performance_stats[operation]) > 1000:
            self.performance_stats[operation] = self.performance_stats[operation][-500:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}

        for operation, durations in self.performance_stats.items():
            if durations:
                stats[operation] = {
                    'count': len(durations),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations)
                }

        return stats

    def get_cache_stats(self) -> Dict[str, CacheStats]:
        """Get cache statistics from all backends"""
        return {
            'memory': self.memory_cache.get_stats(),
            'file': self.file_cache.get_stats()
        }

    async def warm_cache(self, warm_data: Dict[str, Any]):
        """Warm cache with initial data"""
        logger.info(f"Warming cache with {len(warm_data)} entries")

        results = await self.set_multiple(warm_data)
        successful = sum(1 for success in results.values() if success)

        logger.info(f"Cache warming complete: {successful}/{len(warm_data)} successful")

    async def optimize_cache(self):
        """Optimize cache performance"""
        # Analyze access patterns
        memory_stats = self.memory_cache.get_stats()
        file_stats = self.file_cache.get_stats()

        logger.info(f"Cache optimization - Memory hit rate: {memory_stats.hit_rate:.2%}, "
                   f"File hit rate: {file_stats.hit_rate:.2%}")

        # Could implement more sophisticated optimization logic here
        # such as adjusting cache sizes based on usage patterns


# Singleton instance
_cache_manager_instance: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get singleton cache manager instance"""
    global _cache_manager_instance

    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
        await _cache_manager_instance.initialize()

    return _cache_manager_instance


async def close_cache_manager():
    """Close singleton cache manager instance"""
    global _cache_manager_instance

    if _cache_manager_instance:
        await _cache_manager_instance.shutdown()
        _cache_manager_instance = None


if __name__ == "__main__":
    async def test_cache():
        """Test cache manager functionality"""
        cache_manager = CacheManager(backend=CacheBackend.HYBRID)
        await cache_manager.initialize()

        try:
            # Test basic operations
            await cache_manager.set("test_key", {"data": "test_value"}, ttl=60)
            value = await cache_manager.get("test_key")
            print(f"Retrieved: {value}")

            # Test batch operations
            test_data = {
                "price:ALGO": {"price": 0.25, "timestamp": "2023-01-01"},
                "account:test123": {"balance": 1000},
                "history:old_data": {"data": "archived"}
            }

            await cache_manager.set_multiple(test_data)
            results = await cache_manager.get_multiple(list(test_data.keys()))
            print(f"Batch results: {len(results)} items")

            # Performance stats
            perf_stats = cache_manager.get_performance_stats()
            cache_stats = cache_manager.get_cache_stats()

            print(f"Performance: {perf_stats}")
            print(f"Cache stats: {cache_stats}")

        finally:
            await cache_manager.shutdown()

    asyncio.run(test_cache())