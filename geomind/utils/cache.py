"""
缓存工具

提供内存和 Redis 缓存功能。
"""

import hashlib
import json
import pickle
from abc import ABC, abstractmethod
from typing import Any, Optional

from geomind.config import get_settings
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


class BaseCache(ABC):
    """缓存基类"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """删除缓存"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass


class MemoryCache(BaseCache):
    """内存缓存实现"""

    def __init__(self, default_ttl: int = 3600):
        """
        初始化内存缓存

        Args:
            default_ttl: 默认 TTL（秒）
        """
        self.cache = {}
        self.default_ttl = default_ttl
        logger.debug("初始化内存缓存", default_ttl=default_ttl)

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        if key in self.cache:
            value, expiry = self.cache[key]
            # 检查是否过期（expiry 为 None 表示永不过期）
            if expiry is None or expiry > self._current_time():
                logger.debug("缓存命中", key=key)
                return value
            else:
                # 已过期，删除
                del self.cache[key]
                logger.debug("缓存过期", key=key)

        logger.debug("缓存未命中", key=key)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为 None 则使用默认值
        """
        if ttl is None:
            ttl = self.default_ttl

        expiry = None if ttl <= 0 else self._current_time() + ttl
        self.cache[key] = (value, expiry)
        logger.debug("设置缓存", key=key, ttl=ttl)

    def delete(self, key: str) -> None:
        """
        删除缓存

        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug("删除缓存", key=key)

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.debug("清空缓存")

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        return self.get(key) is not None

    @staticmethod
    def _current_time() -> float:
        """获取当前时间戳"""
        import time

        return time.time()


class RedisCache(BaseCache):
    """Redis 缓存实现"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        default_ttl: int = 3600,
        password: Optional[str] = None,
    ):
        """
        初始化 Redis 缓存

        Args:
            host: Redis 主机
            port: Redis 端口
            db: Redis 数据库编号
            default_ttl: 默认 TTL（秒）
            password: Redis 密码
        """
        try:
            import redis

            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,  # 使用字节串
            )
            self.default_ttl = default_ttl
            # 测试连接
            self.redis.ping()
            logger.info(
                "初始化 Redis 缓存",
                host=host,
                port=port,
                db=db,
                default_ttl=default_ttl,
            )
        except ImportError:
            raise ImportError("Redis 缓存需要安装 redis 包: pip install redis")
        except Exception as e:
            logger.error("连接 Redis 失败", error=str(e))
            raise

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在则返回 None
        """
        try:
            value = self.redis.get(key)
            if value is not None:
                logger.debug("缓存命中", key=key)
                return pickle.loads(value)
            logger.debug("缓存未命中", key=key)
            return None
        except Exception as e:
            logger.error("获取 Redis 缓存失败", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为 None 则使用默认值
        """
        try:
            if ttl is None:
                ttl = self.default_ttl

            serialized = pickle.dumps(value)
            if ttl > 0:
                self.redis.setex(key, ttl, serialized)
            else:
                self.redis.set(key, serialized)
            logger.debug("设置缓存", key=key, ttl=ttl)
        except Exception as e:
            logger.error("设置 Redis 缓存失败", key=key, error=str(e))

    def delete(self, key: str) -> None:
        """
        删除缓存

        Args:
            key: 缓存键
        """
        try:
            self.redis.delete(key)
            logger.debug("删除缓存", key=key)
        except Exception as e:
            logger.error("删除 Redis 缓存失败", key=key, error=str(e))

    def clear(self) -> None:
        """清空缓存（清空当前数据库）"""
        try:
            self.redis.flushdb()
            logger.debug("清空缓存")
        except Exception as e:
            logger.error("清空 Redis 缓存失败", error=str(e))

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            logger.error("检查 Redis 缓存键失败", key=key, error=str(e))
            return False


class Cache:
    """
    缓存管理器

    根据配置自动选择内存或 Redis 缓存。
    """

    _instance: Optional[BaseCache] = None

    @classmethod
    def get_instance(cls) -> BaseCache:
        """
        获取缓存实例（单例）

        Returns:
            缓存实例
        """
        if cls._instance is None:
            cls._instance = cls._create_cache()
        return cls._instance

    @classmethod
    def _create_cache(cls) -> BaseCache:
        """
        根据配置创建缓存实例

        Returns:
            缓存实例
        """
        try:
            settings = get_settings()
            cache_config = settings.cache

            if not cache_config.enable:
                logger.info("缓存已禁用，使用内存缓存（默认）")
                return MemoryCache(default_ttl=cache_config.ttl)

            if cache_config.backend.value == "redis":
                if cache_config.redis_host:
                    logger.info("使用 Redis 缓存")
                    return RedisCache(
                        host=cache_config.redis_host,
                        port=cache_config.redis_port,
                        db=cache_config.redis_db,
                        default_ttl=cache_config.ttl,
                    )
                else:
                    logger.warning("Redis 配置不完整，使用内存缓存")
                    return MemoryCache(default_ttl=cache_config.ttl)
            else:
                logger.info("使用内存缓存")
                return MemoryCache(default_ttl=cache_config.ttl)

        except Exception as e:
            logger.warning("创建缓存实例失败，使用默认内存缓存", error=str(e))
            return MemoryCache()

    @classmethod
    def reset(cls) -> None:
        """重置缓存实例（主要用于测试）"""
        cls._instance = None


# 便捷函数
def get_cache() -> BaseCache:
    """
    获取缓存实例

    Returns:
        缓存实例
    """
    return Cache.get_instance()


def cache_key(*args, **kwargs) -> str:
    """
    生成缓存键

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        缓存键（MD5 哈希）
    """
    # 构建键字符串
    parts = [str(arg) for arg in args]
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_str = ":".join(parts)

    # 生成 MD5 哈希
    return hashlib.md5(key_str.encode()).hexdigest()


# 导出主要接口
__all__ = [
    "BaseCache",
    "MemoryCache",
    "RedisCache",
    "Cache",
    "get_cache",
    "cache_key",
]

