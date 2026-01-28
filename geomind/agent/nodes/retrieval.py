"""
Retrieval 节点实现

PHRV 框架的 R (Retrieval) 阶段，负责使用 GeoCLIP 召回候选地点。

主要功能：
1. 使用 GeoCLIP 编码图像
2. 为每个假设创建文本查询
3. 使用 GeoCLIP 预测地理位置
4. 召回 top-k 候选地点
5. 更新 AgentState
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from geomind.agent.state import AgentState, Candidate, Hypothesis
from geomind.models.geoclip import create_geoclip
from geomind.utils.image import load_image
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


def create_hypothesis_query(hypothesis: Hypothesis) -> str:
    """
    为假设创建查询文本
    
    将 Hypothesis 对象转换为适合 GeoCLIP 的查询文本。
    
    Args:
        hypothesis: 假设对象
    
    Returns:
        查询文本
    """
    # 基础查询：区域名称
    query_parts = [hypothesis.region]
    
    # 添加关键支持证据
    if hypothesis.supporting:
        # 取前 3 个最重要的证据
        top_evidence = hypothesis.supporting[:3]
        query_parts.extend(top_evidence)
    
    # 组合查询
    query = ", ".join(query_parts)
    
    logger.debug(
        "创建假设查询",
        region=hypothesis.region,
        query=query,
        evidence_count=len(hypothesis.supporting) if hypothesis.supporting else 0,
    )
    
    return query


async def retrieval_node(
    state: AgentState,
    top_k: int = 5,
    use_image: bool = True,
    use_text: bool = True,
) -> Dict[str, List[Candidate]]:
    """
    Retrieval 节点 - 使用 GeoCLIP 召回候选地点
    
    这是 PHRV 流程的第三步，负责：
    1. 使用 GeoCLIP 编码图像（如果 use_image=True）
    2. 为每个假设创建文本查询
    3. 使用 GeoCLIP 预测地理位置
    4. 为每个假设召回 top-k 候选地点
    
    Args:
        state: Agent 状态（需要包含 hypotheses）
        top_k: 每个假设返回的候选数量
        use_image: 是否使用图像编码
        use_text: 是否使用文本编码（假设）
    
    Returns:
        包含候选列表的字典
        
    Raises:
        ValueError: 如果 state.hypotheses 为空
        RuntimeError: 如果 GeoCLIP 调用失败
    """
    logger.info(
        "开始 Retrieval 阶段",
        has_hypotheses=state.hypotheses is not None,
        use_image=use_image,
        use_text=use_text,
    )
    
    # 1. 验证输入
    if state.hypotheses is None or len(state.hypotheses) == 0:
        logger.error("Hypotheses 为空，无法召回候选")
        raise ValueError("state.hypotheses 不能为空，请先执行 Hypothesis 阶段")
    
    # 2. 加载图像
    if use_image:
        try:
            image = load_image(state.image_path)
            logger.debug("图像加载成功", size=image.size)
        except Exception as e:
            logger.error("图像加载失败", error=str(e), path=str(state.image_path))
            raise ValueError(f"无法加载图像: {state.image_path}") from e
    else:
        image = None
    
    # 3. 初始化 GeoCLIP
    try:
        geoclip = create_geoclip()
        await geoclip.initialize()
        logger.debug("GeoCLIP 初始化成功")
    except Exception as e:
        logger.error("GeoCLIP 初始化失败", error=str(e), exc_info=True)
        raise RuntimeError(f"GeoCLIP 初始化失败: {e}") from e
    
    # 4. 编码图像（如果需要）
    image_embedding = None
    if use_image and image is not None:
        try:
            logger.debug("开始图像编码")
            image_response = await geoclip.encode_image(image)
            
            if not image_response.success:
                logger.error("图像编码失败", error=image_response.error)
                raise RuntimeError(f"图像编码失败: {image_response.error}")
            
            image_embedding = image_response.data
            logger.info("图像编码完成", embedding_dim=len(image_embedding))
            
        except Exception as e:
            logger.error("图像编码失败", error=str(e), exc_info=True)
            raise RuntimeError(f"图像编码失败: {e}") from e
    
    # 5. 为每个假设召回候选
    all_candidates = []
    
    for idx, hypothesis in enumerate(state.hypotheses, 1):
        logger.debug(
            f"处理假设 {idx}/{len(state.hypotheses)}",
            region=hypothesis.region,
            confidence=hypothesis.confidence,
        )
        
        try:
            # 5.1 创建查询文本
            query_text = create_hypothesis_query(hypothesis)
            
            # 5.2 使用 GeoCLIP 预测位置
            if use_image and image_embedding is not None:
                # 使用图像编码
                logger.debug("使用图像编码进行预测", query=query_text)
                location_response = await geoclip.predict_location(
                    image=image,
                    text=query_text if use_text else None,
                )
            elif use_text:
                # 仅使用文本编码
                logger.debug("仅使用文本编码进行预测", query=query_text)
                
                # 编码文本
                text_response = await geoclip.encode_text(query_text)
                if not text_response.success:
                    logger.warning("文本编码失败", error=text_response.error)
                    continue
                
                # 使用文本编码预测
                location_response = await geoclip.predict_location(text=query_text)
            else:
                logger.warning("既不使用图像也不使用文本，跳过")
                continue
            
            # 5.3 检查响应
            if not location_response.success:
                logger.warning(
                    "位置预测失败",
                    hypothesis=hypothesis.region,
                    error=location_response.error,
                )
                continue
            
            location_data = location_response.data
            
            # 5.4 创建候选
            # GeoCLIP 返回单个位置预测
            if isinstance(location_data, dict):
                candidate = Candidate(
                    lat=location_data.get("lat", 0.0),
                    lon=location_data.get("lon", 0.0),
                    name=hypothesis.region,
                    hypothesis_source=hypothesis.region,
                    score=hypothesis.confidence,  # 使用假设的置信度
                    retrieval_method="geoclip",
                )
                all_candidates.append(candidate)
                
                logger.debug(
                    "召回候选",
                    hypothesis=hypothesis.region,
                    lat=candidate.lat,
                    lon=candidate.lon,
                )
            
        except Exception as e:
            logger.warning(
                "处理假设失败",
                hypothesis=hypothesis.region,
                error=str(e),
            )
            continue
    
    # 6. 清理 GeoCLIP
    await geoclip.cleanup()
    
    # 7. 按分数排序并限制数量
    all_candidates = sorted(all_candidates, key=lambda c: c.score, reverse=True)
    
    if len(all_candidates) > top_k:
        logger.debug(f"截断候选数量", from_count=len(all_candidates), to_count=top_k)
        all_candidates = all_candidates[:top_k]
    
    logger.info(
        "Retrieval 阶段完成",
        candidates_count=len(all_candidates),
        top_score=all_candidates[0].score if all_candidates else 0,
    )
    
    # 8. 返回更新后的状态
    return {"candidates": all_candidates}


async def retrieval_node_with_fallback(
    state: AgentState,
    top_k: int = 5,
    fallback_to_text_only: bool = True,
) -> Dict[str, List[Candidate]]:
    """
    带回退的 Retrieval 节点
    
    如果图像编码失败，可以回退到仅使用文本。
    
    Args:
        state: Agent 状态
        top_k: 候选数量
        fallback_to_text_only: 是否在图像失败时回退到文本
    
    Returns:
        包含候选列表的字典
    """
    try:
        # 尝试使用图像和文本
        return await retrieval_node(state, top_k, use_image=True, use_text=True)
    except Exception as e:
        logger.warning("图像+文本召回失败", error=str(e))
        
        if not fallback_to_text_only:
            raise
        
        logger.info("回退到仅使用文本召回")
        
        try:
            # 回退到仅文本
            return await retrieval_node(state, top_k, use_image=False, use_text=True)
        except Exception as fallback_error:
            logger.error("文本回退也失败", error=str(fallback_error))
            raise RuntimeError(f"Retrieval 完全失败: {fallback_error}") from e


async def retrieval_node_multi_scale(
    state: AgentState,
    scales: List[str] = ["city", "region", "country"],
    top_k_per_scale: int = 3,
) -> Dict[str, List[Candidate]]:
    """
    多尺度 Retrieval 节点
    
    在不同地理尺度上召回候选（城市、地区、国家）。
    
    Args:
        state: Agent 状态
        scales: 地理尺度列表
        top_k_per_scale: 每个尺度的候选数量
    
    Returns:
        包含候选列表的字典
    """
    logger.info("开始多尺度 Retrieval", scales=scales)
    
    all_candidates = []
    
    for scale in scales:
        logger.debug(f"处理尺度: {scale}")
        
        # 为每个尺度调整假设查询
        # 这里可以根据尺度调整查询策略
        
        # 执行标准召回
        result = await retrieval_node(state, top_k=top_k_per_scale)
        
        # 标记尺度
        scale_candidates = result["candidates"]
        for candidate in scale_candidates:
            candidate.metadata = candidate.metadata or {}
            candidate.metadata["scale"] = scale
        
        all_candidates.extend(scale_candidates)
    
    # 去重并排序
    # 简单的去重：基于坐标相似性
    unique_candidates = []
    seen_coords = set()
    
    for candidate in sorted(all_candidates, key=lambda c: c.score, reverse=True):
        coord_key = (round(candidate.lat, 2), round(candidate.lon, 2))
        if coord_key not in seen_coords:
            unique_candidates.append(candidate)
            seen_coords.add(coord_key)
    
    logger.info(
        "多尺度 Retrieval 完成",
        total_candidates=len(all_candidates),
        unique_candidates=len(unique_candidates),
    )
    
    return {"candidates": unique_candidates}


async def retrieval_node_ensemble(
    state: AgentState,
    top_k: int = 5,
    use_multiple_queries: bool = True,
) -> Dict[str, List[Candidate]]:
    """
    集成 Retrieval 节点
    
    使用多种查询策略并集成结果。
    
    Args:
        state: Agent 状态
        top_k: 候选数量
        use_multiple_queries: 是否为每个假设生成多个查询
    
    Returns:
        包含候选列表的字典
    """
    logger.info("开始集成 Retrieval")
    
    # 1. 图像+文本
    result_1 = await retrieval_node(state, top_k, use_image=True, use_text=True)
    
    # 2. 仅图像（如果支持）
    try:
        result_2 = await retrieval_node(state, top_k, use_image=True, use_text=False)
    except Exception as e:
        logger.warning("仅图像召回失败", error=str(e))
        result_2 = {"candidates": []}
    
    # 3. 合并结果
    all_candidates = result_1["candidates"] + result_2["candidates"]
    
    # 去重和重新评分
    candidate_map = {}
    for candidate in all_candidates:
        coord_key = (round(candidate.lat, 2), round(candidate.lon, 2))
        
        if coord_key in candidate_map:
            # 累加分数
            candidate_map[coord_key].score += candidate.score
        else:
            candidate_map[coord_key] = candidate
    
    # 排序
    final_candidates = sorted(
        candidate_map.values(),
        key=lambda c: c.score,
        reverse=True,
    )[:top_k]
    
    logger.info("集成 Retrieval 完成", candidates_count=len(final_candidates))
    
    return {"candidates": final_candidates}


# 为 LangGraph 提供的节点函数
async def retrieval(state: AgentState) -> Dict[str, List[Candidate]]:
    """
    LangGraph 节点函数 - Retrieval 阶段
    
    这是一个简化的包装函数，用于 LangGraph 图定义。
    
    Args:
        state: Agent 状态
    
    Returns:
        包含候选列表的字典
    """
    return await retrieval_node(state)


__all__ = [
    "create_hypothesis_query",
    "retrieval_node",
    "retrieval_node_with_fallback",
    "retrieval_node_multi_scale",
    "retrieval_node_ensemble",
    "retrieval",
]

