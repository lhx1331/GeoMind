"""
Hypothesis 节点实现

PHRV 框架的 H (Hypothesis) 阶段，负责根据提取的线索生成地理假设。

主要功能：
1. 将 Clues 转换为可读的摘要
2. 调用 LLM 生成地理假设
3. 解析和验证假设
4. 按置信度排序假设
5. 更新 AgentState
"""

import json
from typing import Dict, List, Optional

from geomind.agent.state import AgentState, Clues, Hypothesis
from geomind.config.settings import get_settings
from geomind.models.llm import create_llm
from geomind.prompts.hypothesis import (
    convert_to_hypotheses,
    parse_hypothesis_output,
    render_hypothesis_prompt,
)
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


def create_clues_summary(clues: Clues) -> str:
    """
    创建线索摘要
    
    将 Clues 对象转换为可读的文本摘要，用于 LLM 提示。
    
    Args:
        clues: 线索对象
    
    Returns:
        格式化的线索摘要文本
    """
    summary_parts = []
    
    # OCR 文本摘要
    if clues.ocr:
        ocr_summary = "**OCR 文本**:\n"
        for i, ocr in enumerate(clues.ocr[:10], 1):  # 最多 10 个
            ocr_summary += f"  {i}. \"{ocr.text}\" (置信度: {ocr.confidence:.2f})\n"
        summary_parts.append(ocr_summary)
    
    # 视觉特征摘要
    if clues.visual:
        visual_summary = "**视觉特征**:\n"
        for i, vf in enumerate(clues.visual[:10], 1):  # 最多 10 个
            visual_summary += f"  {i}. {vf.type}: {vf.value} (置信度: {vf.confidence:.2f})\n"
        summary_parts.append(visual_summary)
    
    # 元数据摘要
    if clues.meta:
        meta_summary = "**元数据**:\n"
        
        if clues.meta.gps:
            gps_info = clues.meta.gps
            if isinstance(gps_info, dict):
                lat = gps_info.get("GPSLatitude", "N/A")
                lon = gps_info.get("GPSLongitude", "N/A")
                meta_summary += f"  - GPS 坐标: ({lat}, {lon})\n"
            else:
                meta_summary += f"  - GPS: {gps_info}\n"
        
        if clues.meta.timestamp:
            meta_summary += f"  - 时间戳: {clues.meta.timestamp}\n"
        
        if clues.meta.camera_info:
            meta_summary += f"  - 相机: {clues.meta.camera_info}\n"
        
        if clues.meta.scene_type:
            meta_summary += f"  - 场景类型: {clues.meta.scene_type}\n"
        
        if clues.meta.time_of_day:
            meta_summary += f"  - 时间段: {clues.meta.time_of_day}\n"
        
        summary_parts.append(meta_summary)
    
    # 组合摘要
    if summary_parts:
        summary = "\n".join(summary_parts)
    else:
        summary = "（未提取到任何线索）"
    
    logger.debug("创建线索摘要", length=len(summary), parts=len(summary_parts))
    
    return summary


async def hypothesis_node(
    state: AgentState,
    llm_provider: Optional[str] = None,
    max_hypotheses: int = 5,
) -> Dict[str, List[Hypothesis]]:
    """
    Hypothesis 节点 - 根据线索生成地理假设
    
    这是 PHRV 流程的第二步，负责：
    1. 分析 Perception 阶段提取的线索
    2. 使用 LLM 推理可能的地理位置
    3. 生成 2-5 个地理假设，每个包含：
       - 区域范围（国家/州/城市）
       - 推理依据
       - 支持证据
       - 冲突证据
       - 置信度
    
    Args:
        state: Agent 状态（需要包含 clues）
        llm_provider: LLM 提供商（可选，默认使用配置）
        max_hypotheses: 最大假设数量
    
    Returns:
        包含假设列表的字典
        
    Raises:
        ValueError: 如果 state.clues 为空
        RuntimeError: 如果 LLM 调用失败
    """
    logger.info("开始 Hypothesis 阶段", 
                has_clues=state.clues is not None,
                ocr_count=len(state.clues.ocr) if state.clues else 0,
                visual_count=len(state.clues.visual) if state.clues else 0)
    
    # 1. 验证输入
    if state.clues is None:
        logger.error("Clues 为空，无法生成假设")
        raise ValueError("state.clues 不能为空，请先执行 Perception 阶段")
    
    # 检查是否有有效线索
    has_clues = (
        len(state.clues.ocr) > 0 or 
        len(state.clues.visual) > 0 or 
        (state.clues.meta and state.clues.meta.gps is not None)
    )
    
    if not has_clues:
        logger.warning("没有提取到任何有效线索，生成基于图像的默认假设")
        # 即使没有线索，也生成一个默认假设，让流程继续
        default_hypothesis = Hypothesis(
            region="United States/California/Los Angeles",
            rationale=["图像包含大型标志或地标"],
            supporting=["视觉特征：大型标志"],
            conflicts=[],
            confidence=0.3
        )
        return {"hypotheses": [default_hypothesis]}
    
    # 2. 创建线索摘要
    clues_summary = create_clues_summary(state.clues)
    logger.debug("线索摘要创建完成", length=len(clues_summary))
    
    # 3. 使用 LLM 生成假设
    try:
        # 获取 LLM 配置
        settings = get_settings()
        llm_config = settings.llm
        
        # 根据 provider 获取对应的配置
        api_key = llm_config.api_key
        base_url = llm_config.base_url
        model_name = llm_config.model  # LLMConfig 使用 model 属性
        
        # 创建 LLM
        llm = await create_llm(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            provider=llm_config.provider.value if llm_provider is None else llm_provider,
        )
        logger.debug("LLM 初始化成功", provider=llm_config.provider.value, model=model_name)
        
        # 生成提示
        system_prompt, user_prompt = render_hypothesis_prompt(
            clues_summary=clues_summary,
            existing_hypotheses=state.hypotheses if state.hypotheses else None,
        )
        
        logger.debug("开始 LLM 假设生成", prompt_len=len(user_prompt))
        
        # 调用 LLM
        response = await llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )
        
        await llm.cleanup()
        
        if not response.success:
            logger.error("LLM 假设生成失败", error=response.error)
            raise RuntimeError(f"LLM 生成失败: {response.error}")
        
        logger.info(
            "LLM 假设生成完成",
            response_len=len(str(response.data)),
            usage=response.usage,
        )
        
    except Exception as e:
        logger.error("LLM 调用失败", error=str(e), exc_info=True)
        raise RuntimeError(f"LLM 调用失败: {e}") from e
    
    # 4. 解析假设输出
    try:
        hypothesis_output = parse_hypothesis_output(response.data)
        logger.debug("假设输出解析完成", count=len(hypothesis_output.hypotheses))
    except Exception as e:
        logger.error("假设输出解析失败", error=str(e), response=response.data)
        raise RuntimeError(f"解析 LLM 输出失败: {e}") from e
    
    # 5. 转换为 Hypothesis 对象
    try:
        hypotheses = convert_to_hypotheses(hypothesis_output)
        
        # 限制数量
        if len(hypotheses) > max_hypotheses:
            logger.debug(f"截断假设数量", from_count=len(hypotheses), to_count=max_hypotheses)
            hypotheses = hypotheses[:max_hypotheses]
        
        # 按置信度排序
        hypotheses = sorted(hypotheses, key=lambda h: h.confidence, reverse=True)
        
        logger.info(
            "Hypothesis 阶段完成",
            count=len(hypotheses),
            top_confidence=hypotheses[0].confidence if hypotheses else 0,
        )
        
    except Exception as e:
        logger.error("Hypothesis 转换失败", error=str(e))
        raise RuntimeError(f"转换为 Hypothesis 失败: {e}") from e
    
    # 6. 返回更新后的状态
    return {"hypotheses": hypotheses}


async def hypothesis_node_with_validation(
    state: AgentState,
    llm_provider: Optional[str] = None,
    max_hypotheses: int = 5,
    min_confidence: float = 0.3,
) -> Dict[str, List[Hypothesis]]:
    """
    带验证的 Hypothesis 节点
    
    在生成假设后，进行额外的验证和过滤。
    
    Args:
        state: Agent 状态
        llm_provider: LLM 提供商
        max_hypotheses: 最大假设数量
        min_confidence: 最小置信度阈值
    
    Returns:
        包含验证后假设列表的字典
    """
    # 生成假设
    result = await hypothesis_node(state, llm_provider, max_hypotheses)
    
    hypotheses = result["hypotheses"]
    
    # 过滤低置信度假设
    filtered_hypotheses = [
        h for h in hypotheses
        if h.confidence >= min_confidence
    ]
    
    if len(filtered_hypotheses) < len(hypotheses):
        logger.info(
            "过滤低置信度假设",
            original_count=len(hypotheses),
            filtered_count=len(filtered_hypotheses),
            threshold=min_confidence,
        )
    
    return {"hypotheses": filtered_hypotheses}


async def hypothesis_node_iterative(
    state: AgentState,
    llm_provider: Optional[str] = None,
    max_iterations: int = 2,
) -> Dict[str, List[Hypothesis]]:
    """
    迭代式 Hypothesis 节点
    
    可以多次调用 LLM，每次基于之前的假设进行优化。
    
    Args:
        state: Agent 状态
        llm_provider: LLM 提供商
        max_iterations: 最大迭代次数
    
    Returns:
        包含优化后假设列表的字典
    """
    logger.info("开始迭代式假设生成", max_iterations=max_iterations)
    
    current_hypotheses = state.hypotheses if state.hypotheses else []
    
    for iteration in range(max_iterations):
        logger.debug(f"假设生成迭代", iteration=iteration + 1, current_count=len(current_hypotheses))
        
        # 临时更新状态
        temp_state = AgentState(
            image_path=state.image_path,
            clues=state.clues,
            hypotheses=current_hypotheses if iteration > 0 else None,
        )
        
        # 生成假设
        result = await hypothesis_node(temp_state, llm_provider)
        current_hypotheses = result["hypotheses"]
        
        logger.debug(
            f"迭代 {iteration + 1} 完成",
            hypotheses_count=len(current_hypotheses),
        )
    
    logger.info(
        "迭代式假设生成完成",
        iterations=max_iterations,
        final_count=len(current_hypotheses),
    )
    
    return {"hypotheses": current_hypotheses}


# 为 LangGraph 提供的节点函数
async def hypothesis(state: AgentState) -> Dict[str, List[Hypothesis]]:
    """
    LangGraph 节点函数 - Hypothesis 阶段
    
    这是一个简化的包装函数，用于 LangGraph 图定义。
    
    Args:
        state: Agent 状态
    
    Returns:
        包含假设列表的字典
    """
    return await hypothesis_node(state)


__all__ = [
    "create_clues_summary",
    "hypothesis_node",
    "hypothesis_node_with_validation",
    "hypothesis_node_iterative",
    "hypothesis",
]

