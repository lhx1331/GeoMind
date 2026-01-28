"""
Agent 状态数据模型

定义 PHRV 流程中的所有状态数据结构。
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OCRText(BaseModel):
    """OCR 文本"""

    text: str = Field(description="识别的文本")
    bbox: List[int] = Field(description="文本边界框 [x1, y1, x2, y2]")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")
    lang: Optional[str] = Field(default=None, description="语言")


class VisualFeature(BaseModel):
    """视觉特征"""

    type: str = Field(
        description="特征类型：road_marking, vegetation, architecture, landmark, vehicle 等"
    )
    value: str = Field(description="特征值描述")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")
    bbox: Optional[List[int]] = Field(default=None, description="特征位置边界框")


class Metadata(BaseModel):
    """元数据"""

    exif: Dict[str, Any] = Field(default_factory=dict, description="EXIF 数据")
    gps: Optional[Dict[str, float]] = Field(default=None, description="GPS 坐标")
    timestamp: Optional[str] = Field(default=None, description="时间戳")
    camera_info: Optional[Dict[str, str]] = Field(
        default=None, description="相机信息"
    )


class Clues(BaseModel):
    """感知线索

    包含 OCR 文本、视觉特征和元数据。
    """

    ocr: List[OCRText] = Field(default_factory=list, description="OCR 文本列表")
    visual: List[VisualFeature] = Field(
        default_factory=list, description="视觉特征列表"
    )
    meta: Metadata = Field(default_factory=Metadata, description="元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ocr": [
                    {
                        "text": "Tokyo Station",
                        "bbox": [100, 200, 300, 250],
                        "confidence": 0.95,
                        "lang": "en",
                    }
                ],
                "visual": [
                    {
                        "type": "architecture",
                        "value": "modern glass building",
                        "confidence": 0.85,
                    }
                ],
                "meta": {"exif": {}, "gps": {"lat": 35.6812, "lon": 139.7671}},
            }
        }
    )


class Hypothesis(BaseModel):
    """地理假设

    基于感知线索生成的地理位置假设。
    """

    region: str = Field(description="假设的地理区域，如 'Japan/Tokyo'")
    rationale: List[str] = Field(description="假设的理由列表")
    supporting: List[str] = Field(description="支持该假设的线索")
    conflicts: List[str] = Field(
        default_factory=list, description="与该假设冲突的线索"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, default=0.5, description="假设的置信度"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "region": "Japan/Tokyo",
                "rationale": [
                    "OCR text contains Japanese characters",
                    "Modern architecture style",
                ],
                "supporting": ["Tokyo Station sign", "Japanese text"],
                "conflicts": [],
                "confidence": 0.8,
            }
        }
    )


class Candidate(BaseModel):
    """候选地点

    通过检索得到的候选地理位置。
    """

    name: str = Field(description="地点名称")
    lat: float = Field(ge=-90.0, le=90.0, description="纬度")
    lon: float = Field(ge=-180.0, le=180.0, description="经度")
    source: str = Field(description="来源：geoclip, poi_search, geocode 等")
    score: float = Field(ge=0.0, le=1.0, description="得分/置信度")
    address: Optional[str] = Field(default=None, description="地址")
    region: Optional[str] = Field(default=None, description="所属区域")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="其他元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Tokyo Station",
                "lat": 35.6812,
                "lon": 139.7671,
                "source": "poi_search",
                "score": 0.92,
                "address": "1 Chome Marunouchi, Chiyoda City, Tokyo",
                "region": "Japan/Tokyo",
            }
        }
    )


class Evidence(BaseModel):
    """验证证据

    针对候选地点的验证结果。
    """

    candidate_id: str = Field(description="候选地点标识（通常是名称或索引）")
    check: str = Field(
        description="检查类型：ocr_poi_match, road_topology_check, language_region_prior 等"
    )
    result: str = Field(description="验证结果：pass, fail, uncertain")
    score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="验证得分"
    )
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    reason: Optional[str] = Field(default=None, description="结果原因说明")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "candidate_id": "Tokyo Station",
                "check": "ocr_poi_match",
                "result": "pass",
                "score": 0.95,
                "details": {"matched_texts": ["Tokyo Station"]},
                "reason": "OCR text matches POI name",
            }
        }
    )


class FinalResult(BaseModel):
    """最终结果

    Agent 推理的最终输出。
    """

    answer: str = Field(description="最终答案（地点名称或描述）")
    coordinates: Optional[Dict[str, float]] = Field(
        default=None, description="坐标 {lat, lon}"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")
    why: str = Field(description="支持证据说明")
    why_not: List[str] = Field(
        default_factory=list, description="排除其他候选的原因"
    )
    reasoning_path: List[str] = Field(
        default_factory=list, description="推理路径记录"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Tokyo Station, Tokyo, Japan",
                "coordinates": {"lat": 35.6812, "lon": 139.7671},
                "confidence": 0.92,
                "why": "OCR text matches POI name, architecture style consistent",
                "why_not": ["Osaka excluded: no matching landmarks"],
                "reasoning_path": [
                    "Perception: Detected Japanese text",
                    "Hypothesis: Tokyo region",
                    "Retrieval: Found Tokyo Station",
                    "Verification: OCR matches POI",
                ],
            }
        }
    )


class AgentState(BaseModel):
    """Agent 完整状态

    包含 PHRV 流程的所有中间和最终状态。
    """

    # 输入
    image_path: Optional[str] = Field(default=None, description="输入图像路径")
    image_data: Optional[bytes] = Field(default=None, description="输入图像数据")

    # PHRV 状态
    clues: Optional[Clues] = Field(default=None, description="感知线索")
    hypotheses: List[Hypothesis] = Field(
        default_factory=list, description="地理假设列表"
    )
    candidates: List[Candidate] = Field(
        default_factory=list, description="候选地点列表"
    )
    evidence: List[Evidence] = Field(default_factory=list, description="验证证据列表")
    final: Optional[FinalResult] = Field(default=None, description="最终结果")

    # 元信息
    iteration: int = Field(default=0, description="当前迭代次数")
    max_iterations: int = Field(default=5, description="最大迭代次数")
    current_phase: str = Field(
        default="init", description="当前阶段：init, perception, hypothesis, retrieval, verification, finalize"
    )
    error: Optional[str] = Field(default=None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="其他元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_path": "/path/to/image.jpg",
                "clues": {
                    "ocr": [{"text": "Tokyo", "bbox": [0, 0, 100, 50], "confidence": 0.9}],
                    "visual": [{"type": "landmark", "value": "station", "confidence": 0.8}],
                    "meta": {},
                },
                "hypotheses": [
                    {
                        "region": "Japan/Tokyo",
                        "rationale": ["Japanese text detected"],
                        "supporting": ["Tokyo OCR"],
                        "confidence": 0.8,
                    }
                ],
                "candidates": [
                    {
                        "name": "Tokyo Station",
                        "lat": 35.6812,
                        "lon": 139.7671,
                        "source": "poi_search",
                        "score": 0.9,
                    }
                ],
                "evidence": [
                    {
                        "candidate_id": "Tokyo Station",
                        "check": "ocr_match",
                        "result": "pass",
                        "score": 0.95,
                    }
                ],
                "final": {
                    "answer": "Tokyo Station",
                    "confidence": 0.92,
                    "why": "Strong evidence",
                },
                "iteration": 1,
                "current_phase": "finalize",
            }
        }
    )

    def is_complete(self) -> bool:
        """检查推理是否完成"""
        return self.final is not None or self.iteration >= self.max_iterations

    def has_error(self) -> bool:
        """检查是否有错误"""
        return self.error is not None

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        """添加假设"""
        self.hypotheses.append(hypothesis)

    def add_candidate(self, candidate: Candidate) -> None:
        """添加候选"""
        self.candidates.append(candidate)

    def add_evidence(self, evidence: Evidence) -> None:
        """添加证据"""
        self.evidence.append(evidence)

    def get_best_candidate(self) -> Optional[Candidate]:
        """获取得分最高的候选"""
        if not self.candidates:
            return None
        return max(self.candidates, key=lambda c: c.score)

    def get_passed_evidence_count(self) -> int:
        """获取通过验证的证据数量"""
        return sum(1 for e in self.evidence if e.result == "pass")


# 导出所有模型
__all__ = [
    "OCRText",
    "VisualFeature",
    "Metadata",
    "Clues",
    "Hypothesis",
    "Candidate",
    "Evidence",
    "FinalResult",
    "AgentState",
]

