"""
配置数据模型定义

使用 Pydantic 定义所有配置项的数据模型，提供类型验证和默认值。
"""

from enum import Enum
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    """LLM 提供商枚举"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    LOCAL = "local"


class VLMProvider(str, Enum):
    """VLM 提供商枚举"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"  # Claude 3 系列支持视觉
    GOOGLE = "google"  # Gemini Pro Vision
    QWEN = "qwen"  # 阿里云通义千问 VL
    GLM = "glm"  # 智谱 GLM-4V
    LOCAL = "local"


class Device(str, Enum):
    """设备类型枚举"""

    CUDA = "cuda"
    CPU = "cpu"


class LogLevel(str, Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogFormat(str, Enum):
    """日志格式枚举"""

    JSON = "json"
    TEXT = "text"


class LocationPrecision(str, Enum):
    """地理位置精度枚举"""

    EXACT = "exact"
    CITY = "city"
    REGION = "region"
    COUNTRY = "country"


class SandboxProvider(str, Enum):
    """沙盒提供商枚举"""

    E2B = "e2b"
    LOCAL = "local"
    DOCKER = "docker"


class CacheBackend(str, Enum):
    """缓存后端枚举"""

    MEMORY = "memory"
    REDIS = "redis"


class GeocodeProvider(str, Enum):
    """地理编码服务提供商枚举"""

    GOOGLE = "google"
    BING = "bing"
    MAPBOX = "mapbox"
    NOMINATIM = "nominatim"  # OpenStreetMap (免费)


class POIProvider(str, Enum):
    """POI 搜索服务提供商枚举"""

    GOOGLE = "google"
    BING = "bing"
    MAPBOX = "mapbox"
    NOMINATIM = "nominatim"  # OpenStreetMap (免费)
    OVERPASS = "overpass"  # OpenStreetMap Overpass API (免费)


class LLMConfig(BaseSettings):
    """LLM 配置"""

    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="LLM 提供商")
    model: str = Field(default="gpt-4-turbo-preview", description="模型名称")

    # OpenAI 配置
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API Base URL"
    )

    # Anthropic 配置
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API Key"
    )
    anthropic_model: str = Field(
        default="claude-3-opus-20240229", description="Anthropic 模型名称"
    )

    # DeepSeek 配置
    deepseek_api_key: Optional[str] = Field(
        default=None, description="DeepSeek API Key"
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", description="DeepSeek API Base URL"
    )
    deepseek_model: str = Field(
        default="deepseek-chat", description="DeepSeek 模型名称"
    )

    # 本地 LLM 配置
    local_llm_base_url: Optional[str] = Field(
        default=None, description="本地 LLM Base URL"
    )
    local_llm_api_key: Optional[str] = Field(
        default=None, description="本地 LLM API Key"
    )
    local_llm_model: Optional[str] = Field(
        default=None, description="本地 LLM 模型名称"
    )

    # 通用配置
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=4096, ge=1, description="最大 token 数")

    @property
    def api_key(self) -> Optional[str]:
        """根据 provider 返回对应的 API Key"""
        if self.provider == LLMProvider.OPENAI:
            return self.openai_api_key
        elif self.provider == LLMProvider.ANTHROPIC:
            return self.anthropic_api_key
        elif self.provider == LLMProvider.DEEPSEEK:
            return self.deepseek_api_key
        elif self.provider == LLMProvider.LOCAL:
            return self.local_llm_api_key
        return None

    @property
    def base_url(self) -> Optional[str]:
        """根据 provider 返回对应的 Base URL"""
        if self.provider == LLMProvider.OPENAI:
            return self.openai_base_url
        elif self.provider == LLMProvider.DEEPSEEK:
            return self.deepseek_base_url
        elif self.provider == LLMProvider.LOCAL:
            return self.local_llm_base_url
        return None

    class Config:
        env_prefix = ""
        case_sensitive = False


class VLMConfig(BaseSettings):
    """VLM 配置"""

    provider: VLMProvider = Field(default=VLMProvider.OPENAI, description="VLM 提供商")
    
    # OpenAI Vision 配置
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API Base URL"
    )
    openai_model: str = Field(
        default="gpt-4o", description="OpenAI Vision 模型名称"
    )
    
    # Anthropic Claude 3 配置
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API Key")
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com", description="Anthropic API Base URL"
    )
    anthropic_model: str = Field(
        default="claude-3-opus-20240229", description="Claude 3 模型名称"
    )
    
    # Google Gemini 配置
    google_api_key: Optional[str] = Field(default=None, description="Google API Key")
    google_base_url: str = Field(
        default="https://generativelanguage.googleapis.com", description="Google API Base URL"
    )
    google_model: str = Field(
        default="gemini-pro-vision", description="Gemini 模型名称"
    )
    
    # 阿里云通义千问 VL 配置
    qwen_api_key: Optional[str] = Field(default=None, description="Qwen API Key")
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1", description="Qwen API Base URL"
    )
    qwen_model: str = Field(
        default="qwen-vl-max", description="Qwen VL 模型名称"
    )
    
    # 智谱 GLM-4V 配置
    glm_api_key: Optional[str] = Field(default=None, description="GLM API Key")
    glm_base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4", description="GLM API Base URL"
    )
    glm_model: str = Field(
        default="glm-4v", description="GLM 模型名称"
    )
    
    # 本地 VLM 配置
    local_base_url: Optional[str] = Field(default=None, description="本地 VLM Base URL")
    local_api_key: Optional[str] = Field(default=None, description="本地 VLM API Key")
    local_model: Optional[str] = Field(default=None, description="本地 VLM 模型名称")
    
    # 通用配置
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=4096, ge=1, description="最大 token 数")
    
    @property
    def api_key(self) -> Optional[str]:
        """根据 provider 返回对应的 API Key"""
        if self.provider == VLMProvider.OPENAI:
            return self.openai_api_key
        elif self.provider == VLMProvider.ANTHROPIC:
            return self.anthropic_api_key
        elif self.provider == VLMProvider.GOOGLE:
            return self.google_api_key
        elif self.provider == VLMProvider.QWEN:
            return self.qwen_api_key
        elif self.provider == VLMProvider.GLM:
            return self.glm_api_key
        elif self.provider == VLMProvider.LOCAL:
            return self.local_api_key
        return None
    
    @property
    def base_url(self) -> Optional[str]:
        """根据 provider 返回对应的 Base URL"""
        if self.provider == VLMProvider.OPENAI:
            return self.openai_base_url
        elif self.provider == VLMProvider.ANTHROPIC:
            return self.anthropic_base_url
        elif self.provider == VLMProvider.GOOGLE:
            return self.google_base_url
        elif self.provider == VLMProvider.QWEN:
            return self.qwen_base_url
        elif self.provider == VLMProvider.GLM:
            return self.glm_base_url
        elif self.provider == VLMProvider.LOCAL:
            return self.local_base_url
        return None
    
    @property
    def model_name(self) -> str:
        """根据 provider 返回对应的模型名称"""
        if self.provider == VLMProvider.OPENAI:
            return self.openai_model
        elif self.provider == VLMProvider.ANTHROPIC:
            return self.anthropic_model
        elif self.provider == VLMProvider.GOOGLE:
            return self.google_model
        elif self.provider == VLMProvider.QWEN:
            return self.qwen_model
        elif self.provider == VLMProvider.GLM:
            return self.glm_model
        elif self.provider == VLMProvider.LOCAL:
            return self.local_model or "local-vlm"
        return "gpt-4o"

    class Config:
        env_prefix = "VLM_"
        case_sensitive = False


class GeoCLIPConfig(BaseSettings):
    """GeoCLIP 配置"""

    model_path: Path = Field(
        default=Path("./models/geoclip"), description="GeoCLIP 模型路径"
    )
    device: Device = Field(default=Device.CUDA, description="运行设备")
    top_k: int = Field(default=5, ge=1, le=100, description="Top-K 检索数量")
    cache_embeddings: bool = Field(
        default=True, description="是否缓存嵌入向量"
    )

    @field_validator("model_path")
    @classmethod
    def validate_model_path(cls, v: Path) -> Path:
        """验证模型路径"""
        return Path(v).expanduser().resolve()

    class Config:
        env_prefix = "GEOCLIP_"
        case_sensitive = False


class MCPConfig(BaseSettings):
    """MCP 工具配置"""

    server_url: str = Field(
        default="http://localhost:8002", description="MCP 服务器 URL"
    )
    api_key: Optional[str] = Field(default=None, description="MCP API Key")
    timeout: int = Field(default=30, ge=1, description="请求超时时间（秒）")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    backoff_factor: float = Field(default=2.0, ge=1.0, description="重试退避因子")

    class Config:
        env_prefix = "MCP_"
        case_sensitive = False


class GeocodeConfig(BaseSettings):
    """地理编码服务配置"""

    provider: GeocodeProvider = Field(
        default=GeocodeProvider.NOMINATIM, description="地理编码服务提供商"
    )
    timeout: int = Field(default=10, ge=1, description="请求超时时间（秒）")
    
    # 付费服务配置
    google_api_key: Optional[str] = Field(default=None, description="Google API Key")
    bing_api_key: Optional[str] = Field(default=None, description="Bing API Key")
    mapbox_api_key: Optional[str] = Field(default=None, description="Mapbox API Key")
    
    # Nominatim 配置 (免费)
    nominatim_url: str = Field(
        default="https://nominatim.openstreetmap.org/search",
        description="Nominatim 搜索 URL"
    )
    nominatim_reverse_url: str = Field(
        default="https://nominatim.openstreetmap.org/reverse",
        description="Nominatim 反向地理编码 URL"
    )

    class Config:
        env_prefix = "GEOCODE_"
        case_sensitive = False


class POISearchConfig(BaseSettings):
    """POI 搜索服务配置"""

    provider: POIProvider = Field(
        default=POIProvider.OVERPASS, description="POI 搜索服务提供商"
    )
    timeout: int = Field(default=15, ge=1, description="请求超时时间（秒）")
    
    # 付费服务配置
    api_key: Optional[str] = Field(default=None, description="POI 搜索 API Key (Google/Bing/Mapbox)")
    
    # Overpass API 配置 (免费)
    overpass_url: str = Field(
        default="https://overpass-api.de/api/interpreter",
        description="Overpass API URL"
    )
    
    # Nominatim 配置 (免费备用)
    nominatim_search_url: str = Field(
        default="https://nominatim.openstreetmap.org/search",
        description="Nominatim 搜索 URL"
    )

    class Config:
        env_prefix = "POI_SEARCH_"
        case_sensitive = False


class AgentConfig(BaseSettings):
    """Agent 流程配置"""

    max_iterations: int = Field(
        default=5, ge=1, le=20, description="最大迭代次数"
    )
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="置信度阈值"
    )
    enable_sandbox: bool = Field(
        default=True, description="是否启用沙盒"
    )
    enable_verification: bool = Field(
        default=True, description="是否启用验证"
    )

    class Config:
        env_prefix = "AGENT_"
        case_sensitive = False


class SandboxConfig(BaseSettings):
    """沙盒配置"""

    provider: SandboxProvider = Field(
        default=SandboxProvider.LOCAL, description="沙盒提供商"
    )
    timeout: int = Field(default=60, ge=1, description="超时时间（秒）")
    memory_limit: int = Field(
        default=512, ge=128, description="内存限制（MB）"
    )
    disable_network: bool = Field(
        default=True, description="是否禁用网络访问"
    )
    
    # E2B 配置
    e2b_api_key: Optional[str] = Field(default=None, description="E2B API Key")
    e2b_template: str = Field(default="Python3", description="E2B 沙盒模板")
    
    # Docker 配置
    docker_image: str = Field(
        default="python:3.10-slim", description="Docker 镜像名称"
    )
    docker_network_mode: str = Field(
        default="none", description="Docker 网络模式（none 表示禁用网络）"
    )
    
    # 本地沙盒配置
    local_working_dir: Path = Field(
        default=Path(".sandbox"), description="本地沙盒工作目录"
    )

    model_config = {"env_prefix": "SANDBOX_", "case_sensitive": False}


class LoggingConfig(BaseSettings):
    """日志配置"""

    level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    format: LogFormat = Field(default=LogFormat.JSON, description="日志格式")
    file: Optional[Path] = Field(
        default=Path("logs/geomind.log"), description="日志文件路径"
    )
    console_output: bool = Field(default=True, description="是否输出到控制台")

    @field_validator("file")
    @classmethod
    def validate_log_file(cls, v: Optional[Path]) -> Optional[Path]:
        """验证日志文件路径"""
        if v is None:
            return None
        log_path = Path(v).expanduser().resolve()
        # 确保日志目录存在
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path

    class Config:
        env_prefix = "LOG_"
        case_sensitive = False


class PrivacyConfig(BaseSettings):
    """隐私保护配置"""

    location_precision: LocationPrecision = Field(
        default=LocationPrecision.CITY, description="地理位置精度"
    )
    allow_exact_coordinates: bool = Field(
        default=False, description="是否允许输出精确坐标"
    )
    filter_sensitive_locations: bool = Field(
        default=True, description="是否过滤敏感场所"
    )

    class Config:
        env_prefix = "PRIVACY_"
        case_sensitive = False


class PerformanceConfig(BaseSettings):
    """性能配置"""

    max_concurrent_requests: int = Field(
        default=5, ge=1, le=100, description="最大并发请求数"
    )
    request_timeout: int = Field(
        default=60, ge=1, description="请求超时时间（秒）"
    )
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    retry_backoff_factor: float = Field(
        default=2.0, ge=1.0, description="重试退避因子"
    )

    class Config:
        env_prefix = ""
        case_sensitive = False


class CacheConfig(BaseSettings):
    """缓存配置"""

    enabled: bool = Field(default=True, description="是否启用缓存")
    ttl: int = Field(default=3600, ge=1, description="缓存 TTL（秒）")
    backend: CacheBackend = Field(
        default=CacheBackend.MEMORY, description="缓存后端"
    )

    # Redis 配置
    redis_host: Optional[str] = Field(default=None, description="Redis 主机")
    redis_port: int = Field(default=6379, ge=1, le=65535, description="Redis 端口")
    redis_db: int = Field(default=0, ge=0, description="Redis 数据库编号")
    
    @property
    def enable(self) -> bool:
        """向后兼容的属性"""
        return self.enabled

    class Config:
        env_prefix = "CACHE_"
        case_sensitive = False


class AppSettings(BaseSettings):
    """应用主配置类，包含所有子配置"""

    # 子配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    vlm: VLMConfig = Field(default_factory=VLMConfig)
    geoclip: GeoCLIPConfig = Field(default_factory=GeoCLIPConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    geocode: GeocodeConfig = Field(default_factory=GeocodeConfig)
    poi_search: POISearchConfig = Field(default_factory=POISearchConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

