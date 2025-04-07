import json
import os
from datetime import datetime, timedelta
import hashlib

class CacheProvider:
    """Base class for cache providers"""
    def get(self, key):
        """Get value from cache"""
        raise NotImplementedError
    
    def set(self, key, value, expire_minutes=60):
        """Set value in cache"""
        raise NotImplementedError
    
    def delete(self, key):
        """Delete value from cache"""
        raise NotImplementedError
    
    @staticmethod
    def generate_key(method_name, repo_name, **kwargs):
        """Generate a unique cache key for a repository and method."""
        key_parts = [method_name, repo_name]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        key_string = "_".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


class MemoryCache(CacheProvider):
    """In-memory cache implementation"""
    def __init__(self):
        self._cache = {}
    
    def get(self, key):
        if key in self._cache:
            cached_data = self._cache[key]
            cache_time = cached_data['timestamp']
            expiry_minutes = cached_data['expiry_minutes']
            
            # Check if cache has expired
            if datetime.now() - cache_time < timedelta(minutes=expiry_minutes):
                return cached_data['data']
        return None
    
    def set(self, key, value, expire_minutes=60):
        self._cache[key] = {
            'data': value,
            'timestamp': datetime.now(),
            'expiry_minutes': expire_minutes
        }
    
    def delete(self, key):
        if key in self._cache:
            del self._cache[key]


class RedisCache(CacheProvider):
    """Redis-based cache implementation"""
    def __init__(self, redis_client=None):
        try:
            if redis_client:
                self.redis = redis_client
            else:
                # Try to import Redis and connect
                import redis
                redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
                self.redis = redis.from_url(redis_url)
                # Test connection
                self.redis.ping()
                print("Connected to Redis server successfully")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            print("Falling back to in-memory cache")
            # Fallback to memory cache if Redis is not available
            self._fallback = MemoryCache()
            self.redis = None
    
    def get(self, key):
        if not self.redis:
            return self._fallback.get(key)
        
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key, value, expire_minutes=60):
        if not self.redis:
            return self._fallback.set(key, value, expire_minutes)
        
        try:
            self.redis.setex(
                key,
                timedelta(minutes=expire_minutes),
                json.dumps(value, default=str)
            )
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def delete(self, key):
        if not self.redis:
            return self._fallback.delete(key)
        
        try:
            self.redis.delete(key)
        except Exception as e:
            print(f"Redis delete error: {e}")


def get_cache_provider():
    """Factory function to get the appropriate cache provider based on configuration"""
    use_redis = os.environ.get('USE_REDIS', 'false').lower() in ('true', '1', 't')
    
    if use_redis:
        try:
            return RedisCache()
        except Exception:
            print("Failed to initialize Redis cache, falling back to memory cache")
    
    return MemoryCache()

# Default cache instance
cache = get_cache_provider()