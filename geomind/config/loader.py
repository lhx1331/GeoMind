"""
配置加载器

支持从环境变量、.env 文件和 YAML 配置文件加载配置。
优先级：环境变量 > YAML 配置文件 > .env 文件 > 默认值
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import ValidationError

from geomind.config.schema import AppSettings


class ConfigLoader:
    """配置加载器"""

    def __init__(
        self,
        env_file: Optional[Path] = None,
        config_file: Optional[Path] = None,
    ):
        """
        初始化配置加载器

        Args:
            env_file: .env 文件路径，默认为项目根目录的 .env
            config_file: YAML 配置文件路径，可选
        """
        self.env_file = env_file or self._find_env_file()
        self.config_file = config_file or self._find_config_file()

    @staticmethod
    def _find_env_file() -> Optional[Path]:
        """查找 .env 文件"""
        current_dir = Path.cwd()
        env_file = current_dir / ".env"
        if env_file.exists():
            return env_file
        return None

    @staticmethod
    def _find_config_file() -> Optional[Path]:
        """查找 YAML 配置文件"""
        current_dir = Path.cwd()
        # 按优先级查找配置文件
        config_files = [
            current_dir / "config.yaml",
            current_dir / "config.yml",
            current_dir / "config" / "config.yaml",
            current_dir / "config" / "config.yml",
        ]
        for config_file in config_files:
            if config_file.exists():
                return config_file
        return None

    def load_yaml_config(self) -> Dict[str, Any]:
        """
        从 YAML 文件加载配置

        Returns:
            配置字典，如果文件不存在则返回空字典
        """
        if self.config_file is None or not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 配置文件解析失败: {e}") from e
        except Exception as e:
            raise ValueError(f"读取 YAML 配置文件失败: {e}") from e

    def load_env_file(self) -> Dict[str, Any]:
        """
        从 .env 文件加载配置

        Returns:
            配置字典，如果文件不存在则返回空字典
        """
        if self.env_file is None or not self.env_file.exists():
            return {}

        env_vars = {}
        try:
            with open(self.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith("#"):
                        continue

                    # 解析 KEY=VALUE 格式
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # 移除引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        # 处理注释（在值后面的注释）
                        if "#" in value:
                            value = value.split("#")[0].strip()

                        env_vars[key] = value
        except Exception as e:
            raise ValueError(f"读取 .env 文件失败: {e}") from e

        return env_vars

    def merge_configs(
        self,
        yaml_config: Dict[str, Any],
        env_file_config: Dict[str, Any],
        env_vars: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        合并配置，按优先级：环境变量 > YAML > .env > 默认值

        Args:
            yaml_config: YAML 配置
            env_file_config: .env 文件配置
            env_vars: 环境变量配置

        Returns:
            合并后的配置字典
        """
        # 从默认值开始
        merged = {}

        # 1. 先加载 YAML 配置（优先级较低）
        self._deep_update(merged, yaml_config)

        # 2. 然后加载 .env 文件配置（优先级中等）
        self._deep_update(merged, env_file_config)

        # 3. 最后加载环境变量（优先级最高）
        self._deep_update(merged, env_vars)

        return merged

    @staticmethod
    def _deep_update(base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        深度更新字典，支持嵌套结构

        Args:
            base: 基础字典
            update: 更新字典
        """
        for key, value in update.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                ConfigLoader._deep_update(base[key], value)
            else:
                base[key] = value

    def load(self) -> AppSettings:
        """
        加载配置并返回 AppSettings 对象

        Returns:
            AppSettings 配置对象

        Raises:
            ValidationError: 配置验证失败
            ValueError: 配置文件读取失败
        """
        # 1. 加载 YAML 配置
        yaml_config = self.load_yaml_config()

        # 2. 加载 .env 文件配置
        env_file_config = self.load_env_file()

        # 3. 获取环境变量（优先级最高）
        # 注意：Pydantic Settings 会自动从环境变量读取，这里主要是为了合并逻辑
        env_vars = dict(os.environ)

        # 4. 合并配置
        merged_config = self.merge_configs(yaml_config, env_file_config, env_vars)

        # 5. 创建并验证配置对象
        try:
            settings = AppSettings(**merged_config)
            return settings
        except ValidationError as e:
            raise ValueError(f"配置验证失败: {e}") from e

    @classmethod
    def from_file(cls, config_file: Path) -> AppSettings:
        """
        从指定配置文件加载配置

        Args:
            config_file: 配置文件路径

        Returns:
            AppSettings 配置对象
        """
        loader = cls(config_file=config_file)
        return loader.load()

    @classmethod
    def from_env_file(cls, env_file: Path) -> AppSettings:
        """
        从指定 .env 文件加载配置

        Args:
            env_file: .env 文件路径

        Returns:
            AppSettings 配置对象
        """
        loader = cls(env_file=env_file)
        return loader.load()

    @classmethod
    def default(cls) -> AppSettings:
        """
        使用默认配置（仅从环境变量加载）

        Returns:
            AppSettings 配置对象
        """
        loader = cls()
        return loader.load()

