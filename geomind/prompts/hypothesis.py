"""
Hypothesis 阶段提示模板

提供用于生成地理假设的提示模板和辅助函数。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from geomind.agent.state import Clues, Hypothesis
from geomind.prompts.base import PromptTemplate, load_template
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


# Hypothesis 输出数据模型
class HypothesisRegion(BaseModel):
    """地理区域模型"""
    country: Optional[str] = Field(default=None, description="国家")
    state: Optional[str] = Field(default=None, description="州/省")
    city: Optional[str] = Field(default=None, description="城市")


class HypothesisOutput(BaseModel):
    """单个假设输出模型"""
    region: HypothesisRegion = Field(description="地理区域")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")
    reasoning: str = Field(description="推理依据")
    supporting_clues: List[str] = Field(default_factory=list, description="支持证据")
    conflicting_clues: Optional[List[str]] = Field(default=None, description="冲突证据")


def get_hypothesis_template() -> PromptTemplate:
    """
    获取 Hypothesis 提示模板
    
    Returns:
        PromptTemplate: Hypothesis 阶段的提示模板
    """
    return load_template("hypothesis")


def render_hypothesis_prompt(clues: Clues) -> str:
    """
    渲染 Hypothesis 阶段的提示
    
    Args:
        clues: 从 Perception 阶段获得的线索
    
    Returns:
        str: 渲染后的提示
    """
    template = get_hypothesis_template()
    
    # 准备模板变量
    ocr_texts = [{"text": ocr.text, "confidence": ocr.confidence, "lang": ocr.lang} for ocr in clues.ocr]
    visual_features = [{"type": vf.type, "value": vf.value, "confidence": vf.confidence} for vf in clues.visual]
    metadata = clues.meta.model_dump(exclude_none=True) if clues.meta else {}
    
    # 渲染模板
    prompt = template.render(
        ocr_texts=ocr_texts,
        visual_features=visual_features,
        metadata=metadata
    )
    
    logger.debug(f"Rendered hypothesis prompt with {len(ocr_texts)} OCR texts and {len(visual_features)} visual features")
    return prompt


def parse_hypothesis_output(output: List[Dict[str, Any]]) -> List[HypothesisOutput]:
    """
    解析并验证 Hypothesis 阶段的输出
    
    Args:
        output: LLM 返回的原始输出列表
    
    Returns:
        List[HypothesisOutput]: 验证后的假设列表
    
    Raises:
        ValidationError: 如果输出格式不符合 schema
    """
    try:
        results = [HypothesisOutput(**item) for item in output]
        logger.info(f"Parsed {len(results)} hypotheses")
        return results
    except ValidationError as e:
        logger.error(f"Failed to parse hypothesis output: {e}")
        raise


def convert_to_hypotheses(hypothesis_outputs: List[HypothesisOutput]) -> List[Hypothesis]:
    """
    将 Hypothesis 输出转换为 Hypothesis 对象列表
    
    Args:
        hypothesis_outputs: Hypothesis 阶段的输出列表
    
    Returns:
        List[Hypothesis]: 转换后的假设对象列表
    """
    hypotheses = []
    
    for output in hypothesis_outputs:
        # 构建区域字符串
        region_parts = []
        if output.region.city:
            region_parts.append(output.region.city)
        if output.region.state:
            region_parts.append(output.region.state)
        if output.region.country:
            region_parts.append(output.region.country)
        
        region_str = "/".join(region_parts) if region_parts else "Unknown"
        
        hypothesis = Hypothesis(
            region=region_str,
            rationale=[output.reasoning],  # 转换为列表
            supporting=output.supporting_clues,
            conflicts=output.conflicting_clues or [],
            confidence=output.confidence
        )
        hypotheses.append(hypothesis)
    
    logger.info(f"Converted {len(hypotheses)} hypothesis outputs to Hypothesis objects")
    return hypotheses


def validate_hypothesis_output(output: List[Dict[str, Any]]) -> bool:
    """
    验证输出是否符合 Hypothesis Schema
    
    Args:
        output: 要验证的输出列表
    
    Returns:
        bool: 是否有效
    """
    try:
        parse_hypothesis_output(output)
        return True
    except ValidationError as e:
        logger.warning(f"Hypothesis output validation failed: {e}")
        return False


# 导出
__all__ = [
    "HypothesisRegion",
    "HypothesisOutput",
    "get_hypothesis_template",
    "render_hypothesis_prompt",
    "parse_hypothesis_output",
    "convert_to_hypotheses",
    "validate_hypothesis_output",
]

