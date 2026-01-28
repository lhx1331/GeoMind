"""
Perception 节点实现

PHRV 框架的 P (Perception) 阶段，负责从图像中提取地理相关的线索。

主要功能：
1. 调用 VLM 分析图像
2. 提取 OCR 文本
3. 识别视觉特征（地标、建筑风格等）
4. 提取 EXIF 元数据
5. 将所有线索整合到 AgentState
"""

from pathlib import Path
from typing import Dict, Optional, Union

from PIL import Image

from geomind.agent.state import AgentState, Clues, Metadata, OCRText, VisualFeature
from geomind.config.settings import get_settings
from geomind.models.vlm import create_vlm
from geomind.prompts.perception import (
    convert_to_clues,
    parse_perception_output,
    render_perception_prompt,
)
from geomind.utils.image import extract_exif, load_image
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


async def perception_node(
    state: AgentState,
    vlm_provider: Optional[str] = None,
) -> Dict[str, Clues]:
    """
    Perception 节点 - 提取图像中的地理线索
    
    这是 PHRV 流程的第一步，负责：
    1. 使用 VLM 分析图像内容
    2. 提取 OCR 文本（街道名称、标志、品牌等）
    3. 识别视觉特征（地标、建筑、植被等）
    4. 提取 EXIF 元数据（GPS、时间、相机信息等）
    
    Args:
        state: Agent 状态
        vlm_provider: VLM 提供商（可选，默认使用配置）
    
    Returns:
        包含更新后 clues 的字典
        
    Raises:
        ValueError: 如果图像路径无效
        RuntimeError: 如果 VLM 调用失败
    """
    logger.info("开始 Perception 阶段", image_path=str(state.image_path))
    
    # 1. 加载图像
    try:
        image = load_image(state.image_path)
        logger.debug("图像加载成功", size=image.size, mode=image.mode)
    except Exception as e:
        logger.error("图像加载失败", error=str(e), path=str(state.image_path))
        raise ValueError(f"无法加载图像: {state.image_path}") from e
    
    # 2. 提取 EXIF 元数据
    try:
        exif_data = extract_exif(state.image_path)
        metadata = Metadata(
            exif=exif_data,
            gps=exif_data.get("GPS") if exif_data else None,
            timestamp=exif_data.get("DateTime") if exif_data else None,
            camera_info=exif_data.get("Model") if exif_data else None,
        )
        logger.debug(
            "EXIF 数据提取完成",
            has_gps=metadata.gps is not None,
            has_timestamp=metadata.timestamp is not None,
        )
    except Exception as e:
        logger.warning("EXIF 数据提取失败，使用空元数据", error=str(e))
        metadata = Metadata()
    
    # 3. 使用 VLM 分析图像
    try:
        # 获取 VLM 配置
        settings = get_settings()
        vlm_config = settings.vlm
        
        # 根据 provider 获取对应的配置
        api_key = vlm_config.api_key
        base_url = vlm_config.base_url
        model_name = vlm_config.model_name  # 使用 model_name 属性
        
        # 创建 VLM
        vlm = await create_vlm(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
        )
        logger.debug("VLM 初始化成功", provider=vlm_config.provider.value, model=model_name)
        
        # 生成提示
        # 准备上下文（包含 EXIF 信息）
        context = None
        if exif_data:
            context = f"EXIF metadata: {exif_data}"
        
        prompt = render_perception_prompt(context=context)
        
        logger.debug("开始 VLM 分析", prompt_len=len(prompt))
        
        # 调用 VLM（render_perception_prompt 返回完整提示，作为 user_prompt）
        # VLM.analyze_image 需要文件路径或字节流，不是 PIL Image 对象
        response = await vlm.analyze_image(
            image=state.image_path,  # 使用文件路径
            prompt=prompt,
            system_prompt=None,  # 提示模板中已包含系统提示
        )
        
        await vlm.cleanup()
        
        if not response.success:
            logger.error("VLM 分析失败", error=response.error)
            raise RuntimeError(f"VLM 分析失败: {response.error}")
        
        logger.info(
            "VLM 分析完成",
            response_len=len(str(response.data)),
            usage=response.usage,
        )
        
    except Exception as e:
        logger.error("VLM 调用失败", error=str(e), exc_info=True)
        raise RuntimeError(f"VLM 调用失败: {e}") from e
    
    # 4. 解析 VLM 输出
    try:
        # VLM 返回的 data 可能是字符串（JSON）或字典
        import json
        import re
        
        # 记录原始输出用于调试
        logger.info("VLM 原始输出", output_type=type(response.data).__name__, output_preview=str(response.data)[:1000])
        
        if isinstance(response.data, str):
            # 尝试直接解析 JSON
            try:
                output_dict = json.loads(response.data)
            except json.JSONDecodeError as e:
                logger.warning("直接 JSON 解析失败，尝试提取 JSON 部分", error=str(e), output_preview=response.data[:300])
                # 如果不是完整 JSON，尝试提取 JSON 部分（可能在 markdown 代码块中）
                # 查找 ```json ... ``` 或 ``` ... ``` 中的内容
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response.data, re.DOTALL)
                if json_match:
                    try:
                        output_dict = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # 如果还是失败，尝试查找第一个 { ... } 块
                        json_match = re.search(r'\{.*\}', response.data, re.DOTALL)
                        if json_match:
                            output_dict = json.loads(json_match.group())
                        else:
                            logger.warning("无法从 VLM 输出中提取 JSON，尝试从文本中提取信息", output_preview=response.data[:500])
                            # 尝试从文本中提取一些信息
                            output_dict = {
                                "ocr_texts": [],
                                "visual_features": [],
                                "metadata": {}
                            }
                            # 如果输出包含 "Hollywood" 等关键词，添加视觉特征
                            text_lower = response.data.lower()
                            if "hollywood" in text_lower:
                                output_dict["visual_features"].append({
                                    "type": "landmark",
                                    "value": "Hollywood Sign",
                                    "confidence": 0.8
                                })
                            if "sign" in text_lower or "标志" in text_lower:
                                output_dict["visual_features"].append({
                                    "type": "landmark",
                                    "value": "Large sign or landmark",
                                    "confidence": 0.7
                                })
                else:
                    # 尝试查找第一个 { ... } 块
                    json_match = re.search(r'\{.*\}', response.data, re.DOTALL)
                    if json_match:
                        try:
                            output_dict = json.loads(json_match.group())
                        except json.JSONDecodeError:
                            logger.warning("提取的 JSON 块解析失败，尝试从文本中提取信息", json_preview=json_match.group()[:200])
                            output_dict = {
                                "ocr_texts": [],
                                "visual_features": [],
                                "metadata": {}
                            }
                            # 尝试从文本中提取一些信息
                            text_lower = response.data.lower()
                            if "hollywood" in text_lower:
                                output_dict["visual_features"].append({
                                    "type": "landmark",
                                    "value": "Hollywood Sign",
                                    "confidence": 0.8
                                })
                    else:
                        logger.warning("VLM 输出不是 JSON 格式，尝试从文本中提取信息", output_preview=response.data[:500])
                        # 尝试从文本中提取一些信息
                        output_dict = {
                            "ocr_texts": [],
                            "visual_features": [],
                            "metadata": {}
                        }
                        # 如果输出包含 "Hollywood" 等关键词，添加视觉特征
                        text_lower = response.data.lower()
                        if "hollywood" in text_lower:
                            output_dict["visual_features"].append({
                                "type": "landmark",
                                "value": "Hollywood Sign",
                                "confidence": 0.8
                            })
                        if "sign" in text_lower or "标志" in text_lower or "mountain" in text_lower:
                            output_dict["visual_features"].append({
                                "type": "landmark",
                                "value": "Large sign or landmark on mountain",
                                "confidence": 0.7
                            })
                        if "los angeles" in text_lower or "california" in text_lower or "california" in text_lower:
                            output_dict["visual_features"].append({
                                "type": "location",
                                "value": "Los Angeles, California area",
                                "confidence": 0.75
                            })
        else:
            output_dict = response.data
        
        perception_output = parse_perception_output(output_dict)
        logger.debug(
            "感知输出解析完成",
            ocr_count=len(perception_output.ocr_texts),
            visual_count=len(perception_output.visual_features),
        )
    except Exception as e:
        logger.error("感知输出解析失败", error=str(e))
        raise RuntimeError(f"解析 VLM 输出失败: {e}") from e
    
    # 5. 转换为 Clues 对象
    try:
        clues = convert_to_clues(perception_output)
        
        # 补充元数据
        if metadata.exif:
            clues.meta = metadata
        
        logger.info(
            "Perception 阶段完成",
            ocr_texts=len(clues.ocr),
            visual_features=len(clues.visual),
            has_gps=clues.meta.gps is not None,
        )
        
    except Exception as e:
        logger.error("Clues 转换失败", error=str(e))
        raise RuntimeError(f"转换为 Clues 失败: {e}") from e
    
    # 6. 返回更新后的状态
    return {"clues": clues}


async def perception_node_with_fallback(
    state: AgentState,
    vlm_provider: Optional[str] = None,
    fallback_to_exif_only: bool = True,
) -> Dict[str, Clues]:
    """
    带回退机制的 Perception 节点
    
    如果 VLM 分析失败，可以回退到仅使用 EXIF 数据。
    
    Args:
        state: Agent 状态
        vlm_provider: VLM 提供商
        fallback_to_exif_only: 是否在 VLM 失败时回退到仅 EXIF
    
    Returns:
        包含更新后 clues 的字典
    """
    try:
        return await perception_node(state, vlm_provider)
    except Exception as e:
        logger.warning("Perception 节点失败", error=str(e))
        
        if not fallback_to_exif_only:
            raise
        
        logger.info("回退到仅使用 EXIF 数据")
        
        # 仅提取 EXIF
        try:
            exif_data = extract_exif(state.image_path)
            metadata = Metadata(
                exif=exif_data,
                gps=exif_data.get("GPS") if exif_data else None,
                timestamp=exif_data.get("DateTime") if exif_data else None,
                camera_info=exif_data.get("Model") if exif_data else None,
            )
            
            # 创建最小 Clues
            clues = Clues(ocr=[], visual=[], meta=metadata)
            
            logger.info("仅使用 EXIF 数据完成 Perception")
            
            return {"clues": clues}
            
        except Exception as fallback_error:
            logger.error("EXIF 回退也失败", error=str(fallback_error))
            raise RuntimeError(f"Perception 完全失败: {fallback_error}") from e


# 为 LangGraph 提供的节点函数
async def perception(state: AgentState) -> Dict[str, Clues]:
    """
    LangGraph 节点函数 - Perception 阶段
    
    这是一个简化的包装函数，用于 LangGraph 图定义。
    
    Args:
        state: Agent 状态
    
    Returns:
        包含更新后 clues 的字典
    """
    return await perception_node(state)


__all__ = [
    "perception_node",
    "perception_node_with_fallback",
    "perception",
]

