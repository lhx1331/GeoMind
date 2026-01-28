"""
重试装饰器

提供函数重试功能，支持指数退避。
"""

import asyncio
import functools
import time
from typing import Callable, Optional, Tuple, Type

from geomind.config import get_settings
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


def retry(
    max_retries: Optional[int] = None,
    backoff_factor: Optional[float] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数，默认从配置读取
        backoff_factor: 退避因子，默认从配置读取
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数，接收 (attempt, exception) 参数

    Returns:
        装饰器函数

    Example:
        @retry(max_retries=3, backoff_factor=2)
        def my_function():
            # 可能失败的操作
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 从配置获取默认值
            nonlocal max_retries, backoff_factor
            if max_retries is None or backoff_factor is None:
                try:
                    settings = get_settings()
                    perf_config = settings.performance
                    max_retries = max_retries or perf_config.max_retries
                    backoff_factor = backoff_factor or perf_config.retry_backoff_factor
                except Exception:
                    max_retries = max_retries or 3
                    backoff_factor = backoff_factor or 2.0

            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        # 计算等待时间（指数退避）
                        wait_time = backoff_factor**attempt
                        logger.warning(
                            "函数执行失败，准备重试",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            wait_time=wait_time,
                            error=str(e),
                        )

                        # 调用回调（如果有）
                        if on_retry:
                            on_retry(attempt + 1, e)

                        # 等待后重试
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            "函数执行失败，已达最大重试次数",
                            function=func.__name__,
                            max_retries=max_retries,
                            error=str(e),
                        )

            # 所有重试都失败，抛出最后一个异常
            raise last_exception

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 从配置获取默认值
            nonlocal max_retries, backoff_factor
            if max_retries is None or backoff_factor is None:
                try:
                    settings = get_settings()
                    perf_config = settings.performance
                    max_retries = max_retries or perf_config.max_retries
                    backoff_factor = backoff_factor or perf_config.retry_backoff_factor
                except Exception:
                    max_retries = max_retries or 3
                    backoff_factor = backoff_factor or 2.0

            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        # 计算等待时间（指数退避）
                        wait_time = backoff_factor**attempt
                        logger.warning(
                            "异步函数执行失败，准备重试",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            wait_time=wait_time,
                            error=str(e),
                        )

                        # 调用回调（如果有）
                        if on_retry:
                            on_retry(attempt + 1, e)

                        # 等待后重试
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            "异步函数执行失败，已达最大重试次数",
                            function=func.__name__,
                            max_retries=max_retries,
                            error=str(e),
                        )

            # 所有重试都失败，抛出最后一个异常
            raise last_exception

        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry_on_exception(
    exception_type: Type[Exception] = Exception,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
):
    """
    针对特定异常类型的重试装饰器

    Args:
        exception_type: 异常类型
        max_retries: 最大重试次数
        backoff_factor: 退避因子

    Returns:
        装饰器函数
    """
    return retry(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        exceptions=(exception_type,),
    )


# 导出主要接口
__all__ = [
    "retry",
    "retry_on_exception",
]

