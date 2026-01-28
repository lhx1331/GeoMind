"""
LangGraph 流程定义

使用 LangGraph 编排 PHRV (Perception-Hypothesis-Retrieval-Verification) 工作流。

主要功能：
1. 定义状态图
2. 连接 PHRV 四个节点
3. 实现条件路由
4. 支持循环优化（可选）
"""

from typing import Any, Dict, Literal, Optional

from langgraph.graph import END, StateGraph

from geomind.agent.nodes.hypothesis import hypothesis
from geomind.agent.nodes.perception import perception
from geomind.agent.nodes.retrieval import retrieval
from geomind.agent.nodes.verification import verification
from geomind.agent.state import AgentState
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """
    条件路由函数 - 决定是否继续迭代
    
    可以根据状态判断是否需要重新生成假设或重新召回候选。
    
    Args:
        state: Agent 状态
    
    Returns:
        "continue" 或 "end"
    """
    # 简单策略：如果预测置信度足够高，则结束
    if state.prediction is not None:
        if state.prediction.confidence >= 0.8:
            logger.info("置信度足够高，结束流程", confidence=state.prediction.confidence)
            return "end"
    
    # 否则可以选择继续优化（这里简化为直接结束）
    return "end"


def create_phrv_graph(
    enable_iterations: bool = False,
    max_iterations: int = 2,
) -> StateGraph:
    """
    创建 PHRV 工作流图
    
    Args:
        enable_iterations: 是否启用迭代优化
        max_iterations: 最大迭代次数
    
    Returns:
        编译后的 LangGraph 图
    """
    logger.info("创建 PHRV 工作流图", enable_iterations=enable_iterations)
    
    # 1. 创建状态图
    workflow = StateGraph(AgentState)
    
    # 2. 添加节点
    workflow.add_node("perception", perception)
    workflow.add_node("hypothesis", hypothesis)
    workflow.add_node("retrieval", retrieval)
    workflow.add_node("verification", verification)
    
    # 3. 定义边（节点连接）
    
    # 线性流程: Perception → Hypothesis → Retrieval → Verification
    workflow.set_entry_point("perception")
    workflow.add_edge("perception", "hypothesis")
    workflow.add_edge("hypothesis", "retrieval")
    workflow.add_edge("retrieval", "verification")
    
    if enable_iterations:
        # 添加条件分支：可以从 Verification 回到 Hypothesis 重新优化
        workflow.add_conditional_edges(
            "verification",
            should_continue,
            {
                "continue": "hypothesis",  # 重新生成假设
                "end": END,  # 结束流程
            }
        )
    else:
        # 简单流程：直接结束
        workflow.add_edge("verification", END)
    
    # 4. 编译图
    graph = workflow.compile()
    
    logger.info("PHRV 工作流图创建完成")
    
    return graph


def create_simple_phrv_graph() -> StateGraph:
    """
    创建简单的 PHRV 工作流图（无迭代）
    
    Returns:
        编译后的 LangGraph 图
    """
    return create_phrv_graph(enable_iterations=False)


def create_iterative_phrv_graph(max_iterations: int = 2) -> StateGraph:
    """
    创建迭代式 PHRV 工作流图
    
    Args:
        max_iterations: 最大迭代次数
    
    Returns:
        编译后的 LangGraph 图
    """
    return create_phrv_graph(enable_iterations=True, max_iterations=max_iterations)


async def run_phrv_workflow(
    image_path: str,
    graph: Optional[StateGraph] = None,
    config: Optional[Dict[str, Any]] = None,
) -> AgentState:
    """
    运行 PHRV 工作流
    
    Args:
        image_path: 输入图像路径
        graph: LangGraph 图（如果为 None，则创建默认图）
        config: 配置选项
    
    Returns:
        最终的 Agent 状态
    """
    logger.info("开始运行 PHRV 工作流", image_path=image_path)
    
    # 创建默认图（如果未提供）
    if graph is None:
        graph = create_simple_phrv_graph()
    
    # 初始化状态
    initial_state = AgentState(image_path=image_path)
    
    # 运行图
    try:
        final_state = await graph.ainvoke(
            initial_state,
            config=config or {},
        )
        
        logger.info(
            "PHRV 工作流完成",
            has_prediction=final_state.prediction is not None,
            confidence=final_state.prediction.confidence if final_state.prediction else 0,
        )
        
        return final_state
        
    except Exception as e:
        logger.error("PHRV 工作流执行失败", error=str(e), exc_info=True)
        raise


# 便捷函数
async def predict_location(
    image_path: str,
    use_iterations: bool = False,
) -> AgentState:
    """
    便捷函数：预测图像位置
    
    Args:
        image_path: 图像路径
        use_iterations: 是否使用迭代优化
    
    Returns:
        包含预测的 Agent 状态
    """
    if use_iterations:
        graph = create_iterative_phrv_graph()
    else:
        graph = create_simple_phrv_graph()
    
    return await run_phrv_workflow(image_path, graph)


__all__ = [
    "create_phrv_graph",
    "create_simple_phrv_graph",
    "create_iterative_phrv_graph",
    "run_phrv_workflow",
    "predict_location",
    "should_continue",
]

