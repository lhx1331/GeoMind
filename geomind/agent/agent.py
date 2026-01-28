"""
GeoMind Agent 主类

通用地理推理 Agent，使用 PHRV 框架进行位置预测。

主要功能：
1. 初始化模型和工具
2. 运行 PHRV 工作流
3. 返回预测结果
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from geomind.agent.graph import (
    create_iterative_phrv_graph,
    create_simple_phrv_graph,
    run_phrv_workflow,
)
from geomind.agent.state import AgentState, FinalResult
from geomind.config.settings import get_settings
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


class GeoMindAgent:
    """
    GeoMind 地理推理 Agent
    
    这是主要的用户接口，封装了 PHRV 工作流的所有复杂性。
    
    示例:
        >>> agent = GeoMindAgent()
        >>> result = await agent.geolocate("photo.jpg")
        >>> print(f"位置: ({result.lat}, {result.lon})")
        >>> print(f"置信度: {result.confidence}")
    """
    
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        enable_iterations: bool = False,
        max_iterations: int = 2,
        **kwargs,
    ):
        """
        初始化 GeoMind Agent
        
        Args:
            config_path: 配置文件路径（可选）
            enable_iterations: 是否启用迭代优化
            max_iterations: 最大迭代次数
            **kwargs: 其他配置选项
        """
        logger.info("初始化 GeoMind Agent")
        
        # 加载配置
        self.settings = get_settings()
        
        # 配置选项
        self.enable_iterations = enable_iterations
        self.max_iterations = max_iterations
        self.config_options = kwargs
        
        # 创建工作流图
        if enable_iterations:
            self.graph = create_iterative_phrv_graph(max_iterations)
            logger.info("使用迭代式 PHRV 图", max_iterations=max_iterations)
        else:
            self.graph = create_simple_phrv_graph()
            logger.info("使用简单 PHRV 图")
        
        logger.info("GeoMind Agent 初始化完成")
    
    async def geolocate(
        self,
        image_path: Union[str, Path],
        return_full_state: bool = False,
        **kwargs,
    ) -> Union[FinalResult, AgentState]:
        """
        预测图像的地理位置
        
        这是主要的 API 方法，运行完整的 PHRV 工作流。
        
        Args:
            image_path: 输入图像路径
            return_full_state: 是否返回完整的 Agent 状态（默认只返回预测）
            **kwargs: 传递给工作流的额外参数
        
        Returns:
            FinalResult 对象（或完整的 AgentState，如果 return_full_state=True）
        
        Raises:
            FileNotFoundError: 如果图像文件不存在
            RuntimeError: 如果工作流执行失败
        
        示例:
            >>> agent = GeoMindAgent()
            >>> prediction = await agent.geolocate("photo.jpg")
            >>> print(f"纬度: {prediction.lat}, 经度: {prediction.lon}")
            >>> print(f"置信度: {prediction.confidence:.2%}")
        """
        # 验证图像路径
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error("图像文件不存在", path=str(image_path))
            raise FileNotFoundError(f"图像文件不存在: {image_path}")
        
        logger.info("开始地理定位", image_path=str(image_path))
        
        try:
            # 运行 PHRV 工作流
            config = {**self.config_options, **kwargs}
            
            final_state = await run_phrv_workflow(
                image_path=str(image_path),
                graph=self.graph,
                config=config,
            )
            
            # 检查是否有预测结果
            if final_state.final is None:
                logger.error("未能生成预测结果")
                raise RuntimeError("未能生成预测结果")
            
            final_result = final_state.final
            coords = final_result.coordinates or {}
            
            logger.info(
                "地理定位完成",
                lat=coords.get("lat"),
                lon=coords.get("lon"),
                confidence=final_result.confidence,
            )
            
            # 返回结果
            if return_full_state:
                return final_state
            else:
                return final_result
        
        except Exception as e:
            logger.error("地理定位失败", error=str(e), exc_info=True)
            raise RuntimeError(f"地理定位失败: {e}") from e
    
    async def batch_geolocate(
        self,
        image_paths: list[Union[str, Path]],
        **kwargs,
    ) -> list[FinalResult]:
        """
        批量预测多个图像的地理位置
        
        Args:
            image_paths: 图像路径列表
            **kwargs: 传递给 geolocate 的额外参数
        
        Returns:
            预测结果列表
        
        示例:
            >>> agent = GeoMindAgent()
            >>> predictions = await agent.batch_geolocate([
            ...     "photo1.jpg",
            ...     "photo2.jpg",
            ...     "photo3.jpg",
            ... ])
            >>> for pred in predictions:
            ...     print(f"位置: ({pred.lat}, {pred.lon})")
        """
        logger.info("开始批量地理定位", count=len(image_paths))
        
        predictions = []
        
        for i, image_path in enumerate(image_paths, 1):
            logger.debug(f"处理图像 {i}/{len(image_paths)}", path=str(image_path))
            
            try:
                prediction = await self.geolocate(image_path, **kwargs)
                predictions.append(prediction)
            except Exception as e:
                logger.warning(
                    f"图像 {i} 处理失败",
                    path=str(image_path),
                    error=str(e),
                )
                # 可以选择继续处理其他图像或抛出异常
                # 这里选择记录错误并继续
        
        logger.info("批量地理定位完成", success_count=len(predictions))
        
        return predictions
    
    def get_state_summary(self, state: AgentState) -> Dict[str, Any]:
        """
        获取状态摘要
        
        Args:
            state: Agent 状态
        
        Returns:
            状态摘要字典
        """
        summary = {
            "image_path": state.image_path,
            "clues": {
                "ocr_count": len(state.clues.ocr) if state.clues else 0,
                "visual_count": len(state.clues.visual) if state.clues else 0,
                "has_gps": state.clues.meta.gps is not None if state.clues and state.clues.meta else False,
            },
            "hypotheses": {
                "count": len(state.hypotheses) if state.hypotheses else 0,
                "top_confidence": state.hypotheses[0].confidence if state.hypotheses else 0,
            },
            "candidates": {
                "count": len(state.candidates) if state.candidates else 0,
                "top_score": state.candidates[0].score if state.candidates else 0,
            },
            "final": {
                "answer": state.final.answer if state.final else None,
                "lat": state.final.coordinates.get("lat") if state.final and state.final.coordinates else None,
                "lon": state.final.coordinates.get("lon") if state.final and state.final.coordinates else None,
                "confidence": state.final.confidence if state.final else 0,
            } if state.final else None,
        }
        
        return summary
    
    def __repr__(self) -> str:
        return (
            f"GeoMindAgent("
            f"enable_iterations={self.enable_iterations}, "
            f"max_iterations={self.max_iterations})"
        )


# 便捷函数
async def geolocate(
    image_path: Union[str, Path],
    enable_iterations: bool = False,
    **kwargs,
) -> FinalResult:
    """
    便捷函数：直接预测图像位置
    
    无需先创建 Agent 实例。
    
    Args:
        image_path: 图像路径
        enable_iterations: 是否启用迭代优化
        **kwargs: 其他配置选项
    
    Returns:
        预测结果
    
    示例:
        >>> from geomind.agent import geolocate
        >>> result = await geolocate("photo.jpg")
        >>> coords = result.coordinates or {}
        >>> print(f"位置: ({coords.get('lat')}, {coords.get('lon')})")
    """
    agent = GeoMindAgent(enable_iterations=enable_iterations, **kwargs)
    return await agent.geolocate(image_path)


__all__ = [
    "GeoMindAgent",
    "geolocate",
]

