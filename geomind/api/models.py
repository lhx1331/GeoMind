"""
API 数据模型

定义请求和响应的 Pydantic 模型。
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """预测响应模型"""
    
    lat: float = Field(..., description="纬度")
    lon: float = Field(..., description="经度")
    confidence: float = Field(..., ge=0, le=1, description="置信度 (0-1)")
    reasoning: str = Field(..., description="推理过程")
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="支持证据列表"
    )
    alternative_locations: List[Dict] = Field(
        default_factory=list,
        description="备选位置列表"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 48.8584,
                "lon": 2.2945,
                "confidence": 0.92,
                "reasoning": "图像显示埃菲尔铁塔，位于法国巴黎",
                "supporting_evidence": [
                    "OCR 识别到 'Eiffel Tower'",
                    "建筑风格匹配法国标志性建筑",
                ],
                "alternative_locations": [
                    {"name": "Louvre Museum", "lat": 48.8606, "lon": 2.3376, "score": 0.75}
                ],
            }
        }


class GeolocateRequest(BaseModel):
    """地理定位请求模型（用于 URL 或 base64 图像）"""
    
    image_url: Optional[str] = Field(None, description="图像 URL")
    image_base64: Optional[str] = Field(None, description="Base64 编码的图像")
    enable_iterations: bool = Field(False, description="是否启用迭代优化")
    max_iterations: int = Field(2, ge=1, le=5, description="最大迭代次数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/photo.jpg",
                "enable_iterations": False,
                "max_iterations": 2,
            }
        }


class BatchGeolocateRequest(BaseModel):
    """批量地理定位请求模型"""
    
    image_urls: List[str] = Field(..., min_length=1, description="图像 URL 列表")
    enable_iterations: bool = Field(False, description="是否启用迭代优化")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_urls": [
                    "https://example.com/photo1.jpg",
                    "https://example.com/photo2.jpg",
                ],
                "enable_iterations": False,
            }
        }


class BatchPredictionResponse(BaseModel):
    """批量预测响应模型"""
    
    results: List[Dict] = Field(..., description="预测结果列表")
    success_count: int = Field(..., description="成功数量")
    total_count: int = Field(..., description="总数量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "image_url": "https://example.com/photo1.jpg",
                        "success": True,
                        "prediction": {
                            "lat": 48.8584,
                            "lon": 2.2945,
                            "confidence": 0.92,
                        }
                    },
                    {
                        "image_url": "https://example.com/photo2.jpg",
                        "success": False,
                        "error": "无法加载图像",
                    }
                ],
                "success_count": 1,
                "total_count": 2,
            }
        }


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    agent_initialized: bool = Field(..., description="Agent 是否已初始化")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "agent_initialized": True,
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    
    error: str = Field(..., description="错误类型")
    detail: str = Field(..., description="错误详情")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "detail": "图像文件格式不支持",
            }
        }

