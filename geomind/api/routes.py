"""
API 路由

定义所有 API 端点。
"""

import base64
import tempfile
from io import BytesIO
from pathlib import Path
from typing import List

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from geomind import __version__
from geomind.api.app import get_agent
from geomind.api.models import (
    BatchGeolocateRequest,
    BatchPredictionResponse,
    ErrorResponse,
    GeolocateRequest,
    HealthResponse,
    PredictionResponse,
)
from geomind.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查 API 服务状态",
)
async def health_check():
    """健康检查端点"""
    agent = get_agent()
    
    return HealthResponse(
        status="healthy",
        version=__version__,
        agent_initialized=agent is not None,
    )


@router.post(
    "/geolocate",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "请求错误"},
        500: {"model": ErrorResponse, "description": "服务器错误"},
    },
    summary="图像地理定位",
    description="上传图像文件进行地理位置预测",
)
async def geolocate_upload(
    file: UploadFile = File(..., description="图像文件"),
    enable_iterations: bool = False,
):
    """
    上传图像进行地理定位
    
    支持的图像格式: JPEG, PNG, GIF, BMP
    """
    agent = get_agent()
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent 未初始化")
    
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="文件必须是图像格式")
    
    try:
        # 读取文件内容
        contents = await file.read()
        
        # 验证是否为有效图像
        try:
            Image.open(BytesIO(contents))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无效的图像文件: {e}")
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        try:
            # 执行地理定位
            logger.info("处理上传的图像", filename=file.filename)
            
            prediction = await agent.geolocate(tmp_path)
            
            logger.info(
                "地理定位完成",
                filename=file.filename,
                lat=prediction.lat,
                lon=prediction.lon,
                confidence=prediction.confidence,
            )
            
            return PredictionResponse(
                lat=prediction.lat,
                lon=prediction.lon,
                confidence=prediction.confidence,
                reasoning=prediction.reasoning,
                supporting_evidence=prediction.supporting_evidence or [],
                alternative_locations=prediction.alternative_locations or [],
            )
        
        finally:
            # 清理临时文件
            Path(tmp_path).unlink(missing_ok=True)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("地理定位失败", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"地理定位失败: {e}")


@router.post(
    "/geolocate/url",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="通过 URL 定位",
    description="通过图像 URL 进行地理位置预测",
)
async def geolocate_url(request: GeolocateRequest):
    """
    通过 URL 或 Base64 图像进行地理定位
    """
    agent = get_agent()
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent 未初始化")
    
    # 验证请求
    if not request.image_url and not request.image_base64:
        raise HTTPException(
            status_code=400,
            detail="必须提供 image_url 或 image_base64"
        )
    
    try:
        # 下载或解码图像
        if request.image_url:
            logger.info("从 URL 下载图像", url=request.image_url)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(request.image_url, timeout=30.0)
                response.raise_for_status()
                image_data = response.content
        
        elif request.image_base64:
            logger.info("解码 Base64 图像")
            image_data = base64.b64decode(request.image_base64)
        
        # 验证图像
        try:
            Image.open(BytesIO(image_data))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无效的图像: {e}")
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(image_data)
            tmp_path = tmp_file.name
        
        try:
            # 执行地理定位
            prediction = await agent.geolocate(
                tmp_path,
                enable_iterations=request.enable_iterations,
                max_iterations=request.max_iterations,
            )
            
            return PredictionResponse(
                lat=prediction.lat,
                lon=prediction.lon,
                confidence=prediction.confidence,
                reasoning=prediction.reasoning,
                supporting_evidence=prediction.supporting_evidence or [],
                alternative_locations=prediction.alternative_locations or [],
            )
        
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("地理定位失败", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"地理定位失败: {e}")


@router.post(
    "/geolocate/batch",
    response_model=BatchPredictionResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="批量地理定位",
    description="批量处理多个图像 URL",
)
async def batch_geolocate(request: BatchGeolocateRequest):
    """
    批量地理定位
    
    同时处理多个图像 URL
    """
    agent = get_agent()
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent 未初始化")
    
    if len(request.image_urls) > 10:
        raise HTTPException(
            status_code=400,
            detail="批量请求最多支持 10 个图像"
        )
    
    results = []
    success_count = 0
    
    async with httpx.AsyncClient() as client:
        for i, image_url in enumerate(request.image_urls, 1):
            logger.info(f"处理批量图像 {i}/{len(request.image_urls)}", url=image_url)
            
            try:
                # 下载图像
                response = await client.get(image_url, timeout=30.0)
                response.raise_for_status()
                image_data = response.content
                
                # 保存到临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    tmp_file.write(image_data)
                    tmp_path = tmp_file.name
                
                try:
                    # 执行地理定位
                    prediction = await agent.geolocate(tmp_path)
                    
                    results.append({
                        "image_url": image_url,
                        "success": True,
                        "prediction": {
                            "lat": prediction.lat,
                            "lon": prediction.lon,
                            "confidence": prediction.confidence,
                            "reasoning": prediction.reasoning,
                        }
                    })
                    
                    success_count += 1
                
                finally:
                    Path(tmp_path).unlink(missing_ok=True)
            
            except Exception as e:
                logger.warning(f"图像 {i} 处理失败", url=image_url, error=str(e))
                
                results.append({
                    "image_url": image_url,
                    "success": False,
                    "error": str(e),
                })
    
    return BatchPredictionResponse(
        results=results,
        success_count=success_count,
        total_count=len(request.image_urls),
    )


@router.get(
    "/",
    summary="API 根路径",
    description="返回 API 基本信息",
)
async def root():
    """API 根路径"""
    return {
        "name": "GeoMind API",
        "version": __version__,
        "description": "通用地理推理 Agent API",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
    }

