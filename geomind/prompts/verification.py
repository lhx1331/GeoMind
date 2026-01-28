"""
Verification 阶段提示模板

提供用于验证候选地点的提示模板和辅助函数。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from geomind.agent.state import Candidate, Clues, Evidence
from geomind.prompts.base import PromptTemplate, load_template
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


# Verification 输出数据模型
class VerificationCheck(BaseModel):
    """单个验证检查模型"""
    check_type: str = Field(description="检查类型")
    tool_name: str = Field(description="工具名称")
    tool_params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    expected_outcome: str = Field(description="预期结果")
    scoring_criteria: str = Field(description="评分标准")


class VerificationStrategy(BaseModel):
    """验证策略输出模型"""
    verification_checks: List[VerificationCheck] = Field(description="验证检查列表")
    priority: str = Field(default="medium", description="优先级")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="置信度阈值")


def get_verification_template() -> PromptTemplate:
    """
    获取 Verification 提示模板
    
    Returns:
        PromptTemplate: Verification 阶段的提示模板
    """
    return load_template("verification")


def render_verification_prompt(
    candidate: Candidate,
    clues: Clues,
    available_tools: Optional[List[str]] = None
) -> str:
    """
    渲染 Verification 阶段的提示
    
    Args:
        candidate: 待验证的候选地点
        clues: 原始线索
        available_tools: 可用的验证工具列表
    
    Returns:
        str: 渲染后的提示
    """
    template = get_verification_template()
    
    # 准备候选信息
    candidate_dict = {
        "name": candidate.name,
        "latitude": candidate.lat,
        "longitude": candidate.lon,
        "address": candidate.address,
        "source": candidate.source
    }
    
    # 准备线索信息
    clues_dict = {
        "ocr": [{"text": ocr.text} for ocr in clues.ocr],
        "visual": [{"type": vf.type, "value": vf.value} for vf in clues.visual]
    }
    
    # 默认可用工具
    if available_tools is None:
        available_tools = [
            "ocr_poi_match - OCR文本与POI匹配",
            "road_topology_check - 道路拓扑检查",
            "language_region_prior - 语言区域先验"
        ]
    
    # 渲染模板
    prompt = template.render(
        candidate=candidate_dict,
        clues=clues_dict,
        available_tools=available_tools
    )
    
    logger.debug(f"Rendered verification prompt for candidate: {candidate.name}")
    return prompt


def parse_verification_strategy(output: Dict[str, Any]) -> VerificationStrategy:
    """
    解析并验证 Verification 策略输出
    
    Args:
        output: LLM 返回的原始输出字典
    
    Returns:
        VerificationStrategy: 验证后的策略
    
    Raises:
        ValidationError: 如果输出格式不符合 schema
    """
    try:
        strategy = VerificationStrategy(**output)
        logger.info(f"Parsed verification strategy with {len(strategy.verification_checks)} checks")
        return strategy
    except ValidationError as e:
        logger.error(f"Failed to parse verification strategy: {e}")
        raise


def create_evidence_from_result(
    candidate_id: str,
    check_type: str,
    result: Dict[str, Any],
    score: float
) -> Evidence:
    """
    从验证结果创建 Evidence 对象
    
    Args:
        candidate_id: 候选地点ID
        check_type: 检查类型
        result: 验证结果
        score: 评分
    
    Returns:
        Evidence: 证据对象
    """
    evidence = Evidence(
        candidate_id=candidate_id,
        check=check_type,  # 修正字段名
        result=result.get("outcome", "unknown"),
        score=score,
        details=result
    )
    
    logger.debug(f"Created evidence for candidate {candidate_id}: {check_type} (score={score})")
    return evidence


def validate_verification_strategy(output: Dict[str, Any]) -> bool:
    """
    验证输出是否符合 Verification Strategy Schema
    
    Args:
        output: 要验证的输出字典
    
    Returns:
        bool: 是否有效
    """
    try:
        parse_verification_strategy(output)
        return True
    except ValidationError as e:
        logger.warning(f"Verification strategy validation failed: {e}")
        return False


# 导出
__all__ = [
    "VerificationCheck",
    "VerificationStrategy",
    "get_verification_template",
    "render_verification_prompt",
    "parse_verification_strategy",
    "create_evidence_from_result",
    "validate_verification_strategy",
]

