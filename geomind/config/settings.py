"""
配置设置模块

提供全局配置单例和便捷的配置访问接口。
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from geomind.config.loader import ConfigLoader
from geomind.config.schema import AppSettings


class Settings:
    """
    配置设置类

    提供全局配置单例，支持从环境变量、.env 文件和 YAML 配置文件加载。
    """

    _instance: Optional[AppSettings] = None
    _loader: Optional[ConfigLoader] = None

    def __init__(
        self,
        env_file: Optional[Path] = None,
        config_file: Optional[Path] = None,
        reload: bool = False,
    ):
        """
        初始化配置

        Args:
            env_file: .env 文件路径，默认为项目根目录的 .env
            config_file: YAML 配置文件路径，可选
            reload: 是否重新加载配置（忽略缓存）
        """
        if reload or self._instance is None:
            self._loader = ConfigLoader(env_file=env_file, config_file=config_file)
            self._instance = self._loader.load()

    @property
    def config(self) -> AppSettings:
        """
        获取配置对象

        Returns:
            AppSettings 配置对象
        """
        if self._instance is None:
            self._instance = ConfigLoader().load()
        return self._instance

    @classmethod
    def get_settings(
        cls,
        env_file: Optional[Path] = None,
        config_file: Optional[Path] = None,
    ) -> AppSettings:
        """
        获取配置对象（类方法）

        Args:
            env_file: .env 文件路径
            config_file: YAML 配置文件路径

        Returns:
            AppSettings 配置对象
        """
        loader = ConfigLoader(env_file=env_file, config_file=config_file)
        return loader.load()

    @classmethod
    def reload(cls) -> AppSettings:
        """
        重新加载配置

        Returns:
            AppSettings 配置对象
        """
        cls._instance = None
        loader = ConfigLoader()
        cls._instance = loader.load()
        return cls._instance

    def __getattr__(self, name: str):
        """代理属性访问到配置对象"""
        return getattr(self.config, name)


# 全局配置单例
@lru_cache(maxsize=1)
def get_settings(
    env_file: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> AppSettings:
    """
    获取全局配置单例（带缓存）

    Args:
        env_file: .env 文件路径
        config_file: YAML 配置文件路径

    Returns:
        AppSettings 配置对象
    """
    loader = ConfigLoader(env_file=env_file, config_file=config_file)
    return loader.load()


# 便捷访问函数
def get_llm_config():
    """获取 LLM 配置"""
    return get_settings().llm


def get_vlm_config():
    """获取 VLM 配置"""
    return get_settings().vlm


def get_geoclip_config():
    """获取 GeoCLIP 配置"""
    return get_settings().geoclip


def get_agent_config():
    """获取 Agent 配置"""
    return get_settings().agent


def get_logging_config():
    """获取日志配置"""
    return get_settings().logging

