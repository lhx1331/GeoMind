"""
Verification 节点实现

PHRV 框架的 V (Verification) 阶段，负责验证候选地点并生成最终预测。

主要功能：
1. 使用验证工具验证每个候选
2. OCR-POI 匹配验证
3. 语言/区域先验验证
4. 道路拓扑检查（可选）
5. 综合证据生成最终预测
6. 更新 AgentState
"""

import asyncio
from typing import Dict, List, Optional, Tuple

from geomind.agent.state import AgentState, Candidate, Evidence, FinalResult
from geomind.models.llm import create_llm
from geomind.prompts.verification import (
    render_verification_prompt,
)
from geomind.tools.mcp.verification import (
    check_language_prior,
    match_ocr_poi,
    verify_road_topology,
)
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


async def verify_candidate(
    candidate: Candidate,
    clues: "AgentState.clues",
    use_ocr_poi: bool = True,
    use_language_prior: bool = True,
    use_road_topology: bool = False,
) -> Tuple[Candidate, List[Evidence]]:
    """
    验证单个候选地点
    
    使用多种验证工具来检查候选地点的合理性。
    
    Args:
        candidate: 候选地点
        clues: 从 Perception 阶段提取的线索
        use_ocr_poi: 是否使用 OCR-POI 匹配
        use_language_prior: 是否使用语言先验
        use_road_topology: 是否使用道路拓扑检查
    
    Returns:
        (更新后的候选, 证据列表)
    """
    evidence_list = []
    
    logger.debug(
        "开始验证候选",
        name=candidate.name,
        lat=candidate.lat,
        lon=candidate.lon,
    )
    
    # 1. OCR-POI 匹配验证
    if use_ocr_poi and clues.ocr:
        try:
            ocr_texts = [ocr.text for ocr in clues.ocr]
            
            logger.debug("执行 OCR-POI 匹配", ocr_count=len(ocr_texts))
            
            match_result = await match_ocr_poi(
                ocr_texts=ocr_texts,
                lat=candidate.lat,
                lon=candidate.lon,
                radius=1000,  # 1km 半径
            )
            
            if match_result.is_success():
                match_data = match_result.data
                evidence = Evidence(
                    type="ocr_poi_match",
                    value=f"匹配 {match_data.get('match_count', 0)}/{len(ocr_texts)} 个文本",
                    check="ocr_poi",
                    confidence=match_data.get("confidence", 0.5),
                    details=match_data,
                )
                evidence_list.append(evidence)
                
                logger.debug(
                    "OCR-POI 匹配完成",
                    matches=match_data.get('match_count', 0),
                    confidence=evidence.confidence,
                )
            else:
                logger.warning("OCR-POI 匹配失败", error=match_result.error)
                
        except Exception as e:
            logger.warning("OCR-POI 验证失败", error=str(e))
    
    # 2. 语言先验验证
    if use_language_prior and clues.ocr:
        try:
            ocr_texts = [ocr.text for ocr in clues.ocr]
            
            logger.debug("执行语言先验检查")
            
            prior_result = await check_language_prior(
                ocr_texts=ocr_texts,
                lat=candidate.lat,
                lon=candidate.lon,
            )
            
            if prior_result.is_success():
                prior_data = prior_result.data
                evidence = Evidence(
                    type="language_prior",
                    value=f"语言一致性: {prior_data.get('consistency', 'unknown')}",
                    check="language",
                    confidence=prior_data.get("confidence", 0.5),
                    details=prior_data,
                )
                evidence_list.append(evidence)
                
                logger.debug(
                    "语言先验检查完成",
                    consistency=prior_data.get('consistency'),
                    confidence=evidence.confidence,
                )
            else:
                logger.warning("语言先验检查失败", error=prior_result.error)
                
        except Exception as e:
            logger.warning("语言先验验证失败", error=str(e))
    
    # 3. 道路拓扑验证（可选，较耗时）
    if use_road_topology:
        try:
            logger.debug("执行道路拓扑检查")
            
            topology_result = await verify_road_topology(
                lat=candidate.lat,
                lon=candidate.lon,
                expected_road_type=clues.meta.scene_type if clues.meta else None,
            )
            
            if topology_result.is_success():
                topology_data = topology_result.data
                evidence = Evidence(
                    type="road_topology",
                    value=f"道路类型: {topology_data.get('road_type', 'unknown')}",
                    check="topology",
                    confidence=topology_data.get("confidence", 0.5),
                    details=topology_data,
                )
                evidence_list.append(evidence)
                
                logger.debug(
                    "道路拓扑检查完成",
                    road_type=topology_data.get('road_type'),
                    confidence=evidence.confidence,
                )
            else:
                logger.warning("道路拓扑检查失败", error=topology_result.error)
                
        except Exception as e:
            logger.warning("道路拓扑验证失败", error=str(e))
    
    # 4. 更新候选分数
    if evidence_list:
        # 综合证据调整分数
        evidence_scores = [e.confidence for e in evidence_list]
        avg_evidence_score = sum(evidence_scores) / len(evidence_scores)
        
        # 结合原始分数和证据分数
        candidate.score = (candidate.score * 0.6) + (avg_evidence_score * 0.4)
        
        logger.debug(
            "候选分数更新",
            original_score=candidate.score,
            evidence_score=avg_evidence_score,
            final_score=candidate.score,
        )
    
    return candidate, evidence_list


async def verification_node(
    state: AgentState,
    use_llm_verification: bool = True,
    use_ocr_poi: bool = True,
    use_language_prior: bool = True,
    use_road_topology: bool = False,
    top_k: int = 1,
) -> Dict:
    """
    Verification 节点 - 验证候选地点并生成最终预测
    
    这是 PHRV 流程的第四步，负责：
    1. 使用验证工具验证每个候选
    2. 收集验证证据
    3. 使用 LLM 进行最终推理（可选）
    4. 生成最终预测和置信度
    
    Args:
        state: Agent 状态（需要包含 candidates）
        use_llm_verification: 是否使用 LLM 进行最终验证
        use_ocr_poi: 是否使用 OCR-POI 匹配
        use_language_prior: 是否使用语言先验
        use_road_topology: 是否使用道路拓扑检查
        top_k: 返回的预测数量
    
    Returns:
        包含预测的字典
        
    Raises:
        ValueError: 如果 state.candidates 为空
        RuntimeError: 如果验证失败
    """
    logger.info(
        "开始 Verification 阶段",
        has_candidates=state.candidates is not None,
        use_llm=use_llm_verification,
    )
    
    # 1. 验证输入
    if state.candidates is None or len(state.candidates) == 0:
        logger.error("Candidates 为空，无法进行验证")
        raise ValueError("state.candidates 不能为空，请先执行 Retrieval 阶段")
    
    if state.clues is None:
        logger.warning("Clues 为空，验证能力受限")
    
    # 2. 验证每个候选
    verified_candidates = []
    all_evidence = {}
    
    for idx, candidate in enumerate(state.candidates, 1):
        logger.debug(
            f"验证候选 {idx}/{len(state.candidates)}",
            name=candidate.name,
            score=candidate.score,
        )
        
        try:
            verified_candidate, evidence = await verify_candidate(
                candidate=candidate,
                clues=state.clues,
                use_ocr_poi=use_ocr_poi,
                use_language_prior=use_language_prior,
                use_road_topology=use_road_topology,
            )
            
            verified_candidates.append(verified_candidate)
            all_evidence[candidate.name] = evidence
            
        except Exception as e:
            logger.warning(
                "候选验证失败",
                candidate=candidate.name,
                error=str(e),
            )
            # 即使验证失败，也保留候选
            verified_candidates.append(candidate)
            all_evidence[candidate.name] = []
    
    # 3. 按分数排序
    verified_candidates = sorted(
        verified_candidates,
        key=lambda c: c.score,
        reverse=True,
    )
    
    # 4. 使用 LLM 进行最终验证（可选）
    if use_llm_verification and verified_candidates:
        try:
            logger.debug("开始 LLM 最终验证")
            
            # 创建 LLM
            llm = create_llm()
            await llm.initialize()
            
            # 准备候选摘要
            candidates_summary = []
            for i, c in enumerate(verified_candidates[:5], 1):  # 最多 5 个
                evidence_list = all_evidence.get(c.name, [])
                evidence_str = "; ".join([f"{e.type}: {e.value}" for e in evidence_list])
                
                candidates_summary.append({
                    "rank": i,
                    "name": c.name,
                    "lat": c.lat,
                    "lon": c.lon,
                    "score": c.score,
                    "evidence": evidence_str,
                })
            
            # 生成验证提示
            system_prompt, user_prompt = render_verification_prompt(
                candidates=verified_candidates[:5],
                clues_summary=state.clues,
                evidence_list=[all_evidence.get(c.name, []) for c in verified_candidates[:5]],
            )
            
            logger.debug("开始 LLM 验证", prompt_len=len(user_prompt))
            
            # 调用 LLM
            response = await llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )
            
            await llm.cleanup()
            
            if response.success:
                logger.info("LLM 验证完成", response_len=len(str(response.data)))
                
                # LLM 验证输出（暂时跳过，使用基于分数的预测）
                logger.info("LLM 验证完成，使用基于分数的预测")
            else:
                logger.warning("LLM 验证失败", error=response.error)
                
        except Exception as e:
            logger.warning("LLM 验证失败", error=str(e), exc_info=True)
    
    # 5. 生成基于分数的预测（无 LLM 或 LLM 失败时）
    if verified_candidates:
        top_candidate = verified_candidates[0]
        
        # 收集支持证据
        supporting_evidence = []
        for evidence_list in all_evidence.values():
            for e in evidence_list:
                if e.result == "pass":
                    supporting_evidence.append(e.details.get("value", str(e.details)))
        
        # 收集排除原因
        why_not = []
        for c in verified_candidates[1:top_k]:
            why_not.append(f"{c.name} 分数较低 ({c.score:.2f})")
        
        final_result = FinalResult(
            answer=top_candidate.name or f"{top_candidate.lat:.4f}, {top_candidate.lon:.4f}",
            coordinates={"lat": top_candidate.lat, "lon": top_candidate.lon},
            confidence=top_candidate.score,
            why=f"基于最高分数候选: {top_candidate.name}。支持证据: {', '.join(supporting_evidence[:3]) if supporting_evidence else '无'}",
            why_not=why_not[:3],
            reasoning_path=[
                f"Perception: 提取了 {len(state.clues.ocr) if state.clues else 0} 个 OCR 线索",
                f"Hypothesis: 生成了 {len(state.hypotheses)} 个假设",
                f"Retrieval: 召回了 {len(state.candidates)} 个候选",
                f"Verification: 验证了 {len(verified_candidates)} 个候选，最高分: {top_candidate.score:.2f}",
            ],
        )
        
        logger.info(
            "Verification 阶段完成",
            lat=top_candidate.lat,
            lon=top_candidate.lon,
            confidence=top_candidate.score,
        )
        
        return {
            "final": final_result,
            "verified_candidates": verified_candidates[:top_k],
            "evidence": all_evidence,
        }
    else:
        logger.error("没有有效的候选，无法生成预测")
        raise RuntimeError("验证后没有有效候选")


async def verification_node_simple(
    state: AgentState,
) -> Dict:
    """
    简化的 Verification 节点
    
    仅使用基本验证，不调用 LLM。
    
    Args:
        state: Agent 状态
    
    Returns:
        包含预测的字典
    """
    return await verification_node(
        state,
        use_llm_verification=False,
        use_ocr_poi=True,
        use_language_prior=True,
        use_road_topology=False,
    )


async def verification_node_comprehensive(
    state: AgentState,
) -> Dict:
    """
    全面的 Verification 节点
    
    使用所有可用的验证工具。
    
    Args:
        state: Agent 状态
    
    Returns:
        包含预测的字典
    """
    return await verification_node(
        state,
        use_llm_verification=True,
        use_ocr_poi=True,
        use_language_prior=True,
        use_road_topology=True,
    )


# 为 LangGraph 提供的节点函数
async def verification(state: AgentState) -> Dict:
    """
    LangGraph 节点函数 - Verification 阶段
    
    这是一个简化的包装函数，用于 LangGraph 图定义。
    
    Args:
        state: Agent 状态
    
    Returns:
        包含预测的字典
    """
    result = await verification_node(state)
    
    # 更新状态
    return {
        "prediction": result["prediction"],
    }


__all__ = [
    "verify_candidate",
    "verification_node",
    "verification_node_simple",
    "verification_node_comprehensive",
    "verification",
]

