import json
import logging
from typing import Any, Optional, List
import redis
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class CacheService:
    """
    Сервис для работы с Redis кешем.
    
    Предоставляет методы для получения, установки и удаления данных из кеша.
    Использует префиксы для ключей и поддерживает TTL.
    """
    
    # Префикс для всех ключей приложения
    KEY_PREFIX = getattr(settings, 'CACHE_KEY_PREFIX', 'wp')
    
    # TTL по умолчанию (в секундах)
    DEFAULT_TTL = getattr(settings, 'CACHE_TTL_DEFAULT', 300)
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected = False
        
    def _get_client(self) -> Optional[redis.Redis]:
        """Получение клиента Redis с ленивой инициализацией."""
        if self._client is not None:
            return self._client
            
        try:
            host = getattr(settings, 'REDIS_HOST', 'localhost')
            port = int(getattr(settings, 'REDIS_PORT', 6379))
            password = getattr(settings, 'REDIS_PASSWORD', None)
            
            if not password:
                logger.warning("Redis password not configured. Using insecure connection.")
            
            self._client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            
            # Проверка подключения
            self._client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {host}:{port}")
            
        except redis.ConnectionError as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache will be disabled.")
            self._connected = False
            self._client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self._connected = False
            self._client = None
            
        return self._client
    
    @property
    def is_available(self) -> bool:
        """Проверка доступности Redis."""
        if not self._connected or self._client is None:
            # Пытаемся подключиться снова
            self._get_client()
        return self._connected and self._client is not None
    
    def _make_key(self, key: str) -> str:
        """Создание полного ключа с префиксом."""
        return f"{self.KEY_PREFIX}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получение значения из кеша.
        
        Args:
            key: Ключ без префикса.
            
        Returns:
            Десериализованное значение или None если ключ не найден.
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            full_key = self._make_key(key)
            value = client.get(full_key)
            
            if value is None:
                return None
                
            # Пытаемся десериализовать JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except redis.RedisError as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Установка значения в кеш.
        
        Args:
            key: Ключ без префикса.
            value: Значение для сохранения (будет сериализовано в JSON).
            ttl: Время жизни в секундах (по умолчанию DEFAULT_TTL).
            
        Returns:
            True если успешно, False иначе.
        """
        client = self._get_client()
        if not client:
            return False
            
        try:
            full_key = self._make_key(key)
            serialized = json.dumps(value, default=str)
            effective_ttl = ttl if ttl is not None else self.DEFAULT_TTL
            
            client.setex(full_key, effective_ttl, serialized)
            logger.debug(f"Cache SET: {full_key} (TTL: {effective_ttl}s)")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Удаление ключа из кеша.
        
        Args:
            key: Ключ без префикса.
            
        Returns:
            True если ключ был удален, False иначе.
        """
        client = self._get_client()
        if not client:
            return False
            
        try:
            full_key = self._make_key(key)
            result = client.delete(full_key)
            logger.debug(f"Cache DEL: {full_key}")
            return result > 0
            
        except redis.RedisError as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    def delete_by_pattern(self, pattern: str) -> int:
        """
        Удаление ключей по паттерну.
        
        Args:
            pattern: Паттерн без префикса (поддерживает * wildcard).
            
        Returns:
            Количество удаленных ключей.
        """
        client = self._get_client()
        if not client:
            return 0
            
        try:
            full_pattern = self._make_key(pattern)
            keys = client.keys(full_pattern)
            
            if not keys:
                return 0
                
            # Используем pipeline для эффективного удаления
            pipe = client.pipeline()
            for key in keys:
                pipe.delete(key)
            results = pipe.execute()
            
            deleted_count = sum(results)
            logger.debug(f"Cache DEL by pattern '{pattern}': {deleted_count} keys")
            return deleted_count
            
        except redis.RedisError as e:
            logger.error(f"Redis DELETE by pattern error for pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Проверка существования ключа.
        
        Args:
            key: Ключ без префикса.
            
        Returns:
            True если ключ существует, False иначе.
        """
        client = self._get_client()
        if not client:
            return False
            
        try:
            full_key = self._make_key(key)
            return client.exists(full_key) > 0
        except redis.RedisError as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Получение оставшегося времени жизни ключа.
        
        Args:
            key: Ключ без префикса.
            
        Returns:
            TTL в секундах или None если ключ не существует.
        """
        client = self._get_client()
        if not client:
            return None
            
        try:
            full_key = self._make_key(key)
            return client.ttl(full_key)
        except redis.RedisError as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return None
    
    def clear_all(self) -> bool:
        """
        Очистка всех ключей с префиксом приложения.
        
        Returns:
            True если успешно, False иначе.
        """
        return self.delete_by_pattern("*") > 0


# Глобальный экземпляр сервиса
cache_service = CacheService()
