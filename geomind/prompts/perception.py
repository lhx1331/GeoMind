"""
Perception 阶段提示模板

提供用于图像感知和线索提取的提示模板和辅助函数。
"""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError

from geomind.agent.state import Clues, OCRText, VisualFeature, Metadata
from geomind.prompts.base import PromptTemplate, load_template, render_template
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


# Perception 输出数据模型（用于验证 VLM 输出）
class PerceptionOCRText(BaseModel):
    """OCR 文本输出模型"""
    text: str = Field(description="识别的文本内容")
    bbox: Optional[list[float]] = Field(default=None, description="边界框坐标")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")
    language: Optional[str] = Field(default=None, description="语言代码")


class PerceptionVisualFeature(BaseModel):
    """视觉特征输出模型"""
    type: str = Field(description="特征类型")
    value: str = Field(description="特征描述")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")
    bbox: Optional[list[float]] = Field(default=None, description="边界框坐标")


class PerceptionMetadata(BaseModel):
    """感知元数据输出模型"""
    time_of_day: Optional[str] = Field(default=None, description="一天中的时间")
    season: Optional[str] = Field(default=None, description="季节")
    weather: Optional[str] = Field(default=None, description="天气")
    dominant_colors: Optional[list[str]] = Field(default=None, description="主要颜色")
    scene_type: Optional[str] = Field(default=None, description="场景类型")
    notes: Optional[str] = Field(default=None, description="其他备注")


class PerceptionOutput(BaseModel):
    """Perception 阶段完整输出模型"""
    ocr_texts: list[PerceptionOCRText] = Field(default_factory=list, description="OCR 文本列表")
    visual_features: list[PerceptionVisualFeature] = Field(default_factory=list, description="视觉特征列表")
    metadata: PerceptionMetadata = Field(default_factory=PerceptionMetadata, description="元数据")


def get_perception_template() -> PromptTemplate:
    """
    获取 Perception 提示模板
    
    Returns:
        PromptTemplate: Perception 阶段的提示模板
    """
    return load_template("perception")


def render_perception_prompt(context: Optional[str] = None) -> str:
    """
    渲染 Perception 阶段的提示
    
    Args:
        context: 额外的上下文信息（可选）
    
    Returns:
        str: 渲染后的完整提示
    """
    template = get_perception_template()
    
    # 准备上下文行
    if context:
        context_line = f"额外上下文：{context}"
    else:
        context_line = ""  # 空字符串，Python Template 会保留 ${context_line} 为空
    
    # 使用模板的 render 方法
    prompt = template.safe_render(context_line=context_line)
    
    logger.debug(f"Rendered perception prompt (context={'provided' if context else 'none'})")
    return prompt


def parse_perception_output(output: Dict[str, Any]) -> PerceptionOutput:
    """
    解析并验证 Perception 阶段的输出
    
    Args:
        output: VLM 返回的原始输出字典
    
    Returns:
        PerceptionOutput: 验证后的 Perception 输出
    
    Raises:
        ValidationError: 如果输出格式不符合 schema
    """
    try:
        result = PerceptionOutput(**output)
        logger.info(f"Parsed perception output: {len(result.ocr_texts)} OCR texts, {len(result.visual_features)} features")
        return result
    except ValidationError as e:
        logger.error(f"Failed to parse perception output: {e}")
        raise


def convert_to_clues(perception_output: PerceptionOutput, exif_metadata: Optional[Dict[str, Any]] = None) -> Clues:
    """
    将 Perception 输出转换为 Clues 对象
    
    Args:
        perception_output: Perception 阶段的输出
        exif_metadata: EXIF 元数据（可选）
    
    Returns:
        Clues: 转换后的线索对象
    """
    # 转换 OCR 文本
    ocr_texts = [
        OCRText(
            text=ocr.text,
            bbox=[int(b * 1000) for b in (ocr.bbox or [0, 0, 0, 0])],  # 转换为整数像素坐标
            confidence=ocr.confidence,
            lang=ocr.language
        )
        for ocr in perception_output.ocr_texts
    ]
    
    # 转换视觉特征
    visual_features = [
        VisualFeature(
            type=vf.type,
            value=vf.value,
            confidence=vf.confidence,
            bbox=vf.bbox
        )
        for vf in perception_output.visual_features
    ]
    
    # 转换元数据
    metadata_dict = perception_output.metadata.model_dump(exclude_none=True)
    
    # 合并 EXIF 数据
    if exif_metadata:
        metadata_dict.update(exif_metadata)
    
    metadata = Metadata(**metadata_dict)
    
    clues = Clues(
        ocr=ocr_texts,
        visual=visual_features,
        meta=metadata
    )
    
    logger.info(f"Converted perception output to clues: {len(ocr_texts)} OCR, {len(visual_features)} features")
    return clues


def create_perception_prompt_with_image(
    image_path: Optional[str] = None,
    context: Optional[str] = None
) -> tuple[str, Optional[str]]:
    """
    创建包含图像路径的完整 Perception 提示
    
    Args:
        image_path: 图像文件路径（可选）
        context: 额外的上下文信息（可选）
    
    Returns:
        tuple[str, Optional[str]]: (prompt, image_path)
    """
    prompt = render_perception_prompt(context)
    
    if image_path:
        logger.debug(f"Created perception prompt for image: {image_path}")
    
    return prompt, image_path


# 便捷函数
def get_perception_schema() -> Dict[str, Any]:
    """
    获取 Perception 输出的 JSON Schema
    
    Returns:
        Dict[str, Any]: JSON Schema 字典
    """
    return PerceptionOutput.model_json_schema()


def validate_perception_output(output: Dict[str, Any]) -> bool:
    """
    验证输出是否符合 Perception Schema
    
    Args:
        output: 要验证的输出字典
    
    Returns:
        bool: 是否有效
    """
    try:
        PerceptionOutput(**output)
        return True
    except ValidationError as e:
        logger.warning(f"Perception output validation failed: {e}")
        return False


# 导出
__all__ = [
    "PerceptionOCRText",
    "PerceptionVisualFeature",
    "PerceptionMetadata",
    "PerceptionOutput",
    "get_perception_template",
    "render_perception_prompt",
    "parse_perception_output",
    "convert_to_clues",
    "create_perception_prompt_with_image",
    "get_perception_schema",
    "validate_perception_output",
]

