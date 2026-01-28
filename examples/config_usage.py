"""
配置系统使用示例

演示如何使用 GeoMind 的配置管理系统。
"""

from pathlib import Path

from geomind.config import Settings, get_settings
from geomind.config.loader import ConfigLoader


def example_1_basic_usage():
    """示例 1: 基本使用"""
    print("=" * 50)
    print("示例 1: 基本使用")
    print("=" * 50)

    # 使用默认配置（从环境变量和 .env 文件加载）
    settings = get_settings()

    print(f"LLM Provider: {settings.llm.provider.value}")
    print(f"LLM Model: {settings.llm.model}")
    print(f"Agent Max Iterations: {settings.agent.max_iterations}")
    print(f"Agent Confidence Threshold: {settings.agent.confidence_threshold}")


def example_2_from_env_file():
    """示例 2: 从 .env 文件加载"""
    print("\n" + "=" * 50)
    print("示例 2: 从 .env 文件加载")
    print("=" * 50)

    # 从指定的 .env 文件加载
    env_file = Path(".env")
    if env_file.exists():
        settings = Settings.get_settings(env_file=env_file)
        print(f"从 {env_file} 加载配置")
        print(f"VLM Provider: {settings.vlm.provider.value}")
    else:
        print(f".env 文件不存在: {env_file}")


def example_3_from_yaml_file():
    """示例 3: 从 YAML 文件加载"""
    print("\n" + "=" * 50)
    print("示例 3: 从 YAML 文件加载")
    print("=" * 50)

    # 从 YAML 配置文件加载
    config_file = Path("config.yaml")
    if config_file.exists():
        settings = Settings.get_settings(config_file=config_file)
        print(f"从 {config_file} 加载配置")
        print(f"GeoCLIP Device: {settings.geoclip.device.value}")
        print(f"GeoCLIP Top-K: {settings.geoclip.top_k}")
    else:
        print(f"配置文件不存在: {config_file}")
        print("提示: 可以复制 config.example.yaml 为 config.yaml")


def example_4_custom_loader():
    """示例 4: 使用自定义加载器"""
    print("\n" + "=" * 50)
    print("示例 4: 使用自定义加载器")
    print("=" * 50)

    # 使用 ConfigLoader 自定义加载
    loader = ConfigLoader(
        env_file=Path(".env"),
        config_file=Path("config.yaml"),
    )
    settings = loader.load()

    print(f"Logging Level: {settings.logging.level.value}")
    print(f"Logging Format: {settings.logging.format.value}")
    print(f"Cache Backend: {settings.cache.backend.value}")


def example_5_access_nested_config():
    """示例 5: 访问嵌套配置"""
    print("\n" + "=" * 50)
    print("示例 5: 访问嵌套配置")
    print("=" * 50)

    settings = get_settings()

    # 访问 LLM 配置
    llm_config = settings.llm
    print(f"LLM Provider: {llm_config.provider.value}")
    print(f"LLM Model: {llm_config.model}")

    # 访问 Agent 配置
    agent_config = settings.agent
    print(f"Max Iterations: {agent_config.max_iterations}")
    print(f"Confidence Threshold: {agent_config.confidence_threshold}")

    # 访问 GeoCLIP 配置
    geoclip_config = settings.geoclip
    print(f"GeoCLIP Device: {geoclip_config.device.value}")
    print(f"GeoCLIP Model Path: {geoclip_config.model_path}")


def example_6_config_priority():
    """示例 6: 配置优先级演示"""
    print("\n" + "=" * 50)
    print("示例 6: 配置优先级")
    print("=" * 50)
    print("优先级: 环境变量 > YAML 配置文件 > .env 文件 > 默认值")
    print()

    # 显示当前配置值
    settings = get_settings()
    print(f"Agent Max Iterations: {settings.agent.max_iterations}")
    print(f"Agent Confidence Threshold: {settings.agent.confidence_threshold}")

    print("\n提示:")
    print("- 设置环境变量 AGENT_MAX_ITERATIONS 可以覆盖配置文件")
    print("- 在 YAML 文件中设置的值会覆盖 .env 文件")
    print("- .env 文件的值会覆盖默认值")


if __name__ == "__main__":
    print("GeoMind 配置系统使用示例\n")

    example_1_basic_usage()
    example_2_from_env_file()
    example_3_from_yaml_file()
    example_4_custom_loader()
    example_5_access_nested_config()
    example_6_config_priority()

    print("\n" + "=" * 50)
    print("示例完成！")
    print("=" * 50)

