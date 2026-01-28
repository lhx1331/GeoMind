"""
FastAPI 应用

提供 REST API 来使用 GeoMind Agent。
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from geomind import __version__
from geomind.api.routes import router
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


# 全局 Agent 实例（在应用启动时创建）
_agent = None


def get_agent():
    """获取全局 Agent 实例"""
    return _agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("启动 GeoMind API 服务")
    
    global _agent
    from geomind import GeoMindAgent
    _agent = GeoMindAgent()
    
    logger.info("GeoMind Agent 初始化完成")
    
    yield
    
    # 关闭
    logger.info("关闭 GeoMind API 服务")
    _agent = None


def create_app(
    title: str = "GeoMind API",
    description: Optional[str] = None,
    enable_cors: bool = True,
) -> FastAPI:
    """
    创建 FastAPI 应用
    
    Args:
        title: API 标题
        description: API 描述
        enable_cors: 是否启用 CORS
    
    Returns:
        FastAPI 应用实例
    """
    if description is None:
        description = """
        GeoMind - 通用地理推理 Agent API
        
        基于 PHRV 框架的多模态地理位置推理系统。
        
        ## 主要功能
        
        * **图像地理定位** - 从图像预测拍摄位置
        * **批量处理** - 同时处理多个图像
        * **高准确性** - 使用先进的多模态模型
        
        ## 使用示例
        
        ```python
        import requests
        
        # 上传图像进行定位
        with open('photo.jpg', 'rb') as f:
            response = requests.post(
                'http://localhost:8000/api/v1/geolocate',
                files={'file': f}
            )
        
        result = response.json()
        print(f"位置: ({result['lat']}, {result['lon']})")
        print(f"置信度: {result['confidence']}")
        ```
        """
    
    app = FastAPI(
        title=title,
        description=description,
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # 添加 CORS 中间件
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 生产环境应该限制
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 注册路由
    app.include_router(router, prefix="/api/v1")
    
    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"未处理的异常", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "内部服务器错误",
                "detail": str(exc),
            }
        )
    
    return app


# 创建默认应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "geomind.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

