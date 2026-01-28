"""
验证工具

实现地理推理验证功能，包括 OCR-POI 匹配、道路拓扑检查、语言区域先验等。
"""

import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from geomind.tools.base import BaseTool, ToolResult
from geomind.tools.mcp.geocode import GeoLocation
from geomind.tools.mcp.poi_search import POI
from geomind.tools.registry import register_tool
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


class MatchResult(BaseModel):
    """匹配结果"""

    score: float = Field(ge=0.0, le=1.0, description="匹配分数")
    matched: bool = Field(description="是否匹配")
    details: Dict[str, Any] = Field(default_factory=dict, description="匹配详情")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "score": 0.85,
                "matched": True,
                "details": {"method": "fuzzy", "confidence": 0.85},
            }
        }
    )


class LanguageRegion(BaseModel):
    """语言区域"""

    language: str = Field(description="语言代码")
    script: Optional[str] = Field(default=None, description="文字系统")
    regions: List[str] = Field(description="可能的区域列表")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "language": "ja",
                "script": "kanji",
                "regions": ["JP", "CN"],
                "confidence": 0.9,
            }
        }
    )


# 语言到区域的映射
LANGUAGE_REGION_MAP = {
    "zh": ["CN", "TW", "HK", "SG"],  # 中文
    "ja": ["JP"],  # 日语
    "ko": ["KR", "KP"],  # 韩语
    "en": ["US", "GB", "CA", "AU", "NZ", "IE"],  # 英语
    "es": ["ES", "MX", "AR", "CO", "PE"],  # 西班牙语
    "fr": ["FR", "CA", "BE", "CH"],  # 法语
    "de": ["DE", "AT", "CH"],  # 德语
    "it": ["IT", "CH"],  # 意大利语
    "pt": ["PT", "BR"],  # 葡萄牙语
    "ru": ["RU", "BY", "KZ"],  # 俄语
    "ar": ["SA", "EG", "AE", "MA"],  # 阿拉伯语
    "hi": ["IN"],  # 印地语
    "th": ["TH"],  # 泰语
    "vi": ["VN"],  # 越南语
    "id": ["ID"],  # 印尼语
    "tr": ["TR"],  # 土耳其语
    "pl": ["PL"],  # 波兰语
    "nl": ["NL", "BE"],  # 荷兰语
    "sv": ["SE"],  # 瑞典语
    "no": ["NO"],  # 挪威语
    "da": ["DK"],  # 丹麦语
    "fi": ["FI"],  # 芬兰语
}

# 文字系统到区域的映射
SCRIPT_REGION_MAP = {
    "latin": ["US", "GB", "FR", "DE", "IT", "ES", "PT", "PL", "NL"],
    "cyrillic": ["RU", "BY", "KZ", "UA"],
    "arabic": ["SA", "EG", "AE", "MA", "IQ"],
    "devanagari": ["IN", "NP"],
    "han": ["CN", "TW", "HK", "JP", "KR"],  # 汉字
    "hiragana": ["JP"],
    "katakana": ["JP"],
    "hangul": ["KR"],
    "thai": ["TH"],
    "hebrew": ["IL"],
    "greek": ["GR"],
}


def normalize_text(text: str) -> str:
    """标准化文本

    Args:
        text: 输入文本

    Returns:
        标准化后的文本
    """
    # 转小写
    text = text.lower()
    # 移除标点符号
    text = re.sub(r'[^\w\s]', '', text)
    # 移除多余空格
    text = ' '.join(text.split())
    return text


def fuzzy_match(text1: str, text2: str, threshold: float = 0.6) -> Tuple[bool, float]:
    """模糊匹配

    Args:
        text1: 文本1
        text2: 文本2
        threshold: 匹配阈值

    Returns:
        (是否匹配, 匹配分数)
    """
    # 标准化文本
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    # 计算相似度
    score = SequenceMatcher(None, text1, text2).ratio()

    return score >= threshold, score


def contains_match(text: str, keywords: List[str]) -> Tuple[bool, float]:
    """包含匹配

    检查文本是否包含任何关键词。

    Args:
        text: 文本
        keywords: 关键词列表

    Returns:
        (是否匹配, 匹配分数)
    """
    text = normalize_text(text)
    matched_count = 0

    for keyword in keywords:
        keyword = normalize_text(keyword)
        if keyword in text:
            matched_count += 1

    if not keywords:
        return False, 0.0

    score = matched_count / len(keywords)
    return score > 0, score


def detect_language(text: str) -> Optional[str]:
    """检测文本语言

    Args:
        text: 文本

    Returns:
        语言代码
    """
    # 简单的语言检测（基于字符范围）
    # 日文（平假名、片假名）- 优先检测，因为日文也包含汉字
    if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
        return "ja"
    # 韩文
    if re.search(r'[\uac00-\ud7af]', text):
        return "ko"
    # 中文（汉字）- 放在日文和韩文之后
    if re.search(r'[\u4e00-\u9fff]', text):
        return "zh"
    # 阿拉伯文
    if re.search(r'[\u0600-\u06ff]', text):
        return "ar"
    # 西里尔字母（俄语等）
    if re.search(r'[\u0400-\u04ff]', text):
        return "ru"
    # 泰文
    if re.search(r'[\u0e00-\u0e7f]', text):
        return "th"
    # 希伯来文
    if re.search(r'[\u0590-\u05ff]', text):
        return "he"
    # 希腊文
    if re.search(r'[\u0370-\u03ff]', text):
        return "el"
    # 默认英语
    return "en"


def detect_script(text: str) -> Optional[str]:
    """检测文字系统

    Args:
        text: 文本

    Returns:
        文字系统
    """
    # 汉字
    if re.search(r'[\u4e00-\u9fff]', text):
        return "han"
    # 平假名
    if re.search(r'[\u3040-\u309f]', text):
        return "hiragana"
    # 片假名
    if re.search(r'[\u30a0-\u30ff]', text):
        return "katakana"
    # 韩文
    if re.search(r'[\uac00-\ud7af]', text):
        return "hangul"
    # 阿拉伯文
    if re.search(r'[\u0600-\u06ff]', text):
        return "arabic"
    # 西里尔字母
    if re.search(r'[\u0400-\u04ff]', text):
        return "cyrillic"
    # 天城文（印地语等）
    if re.search(r'[\u0900-\u097f]', text):
        return "devanagari"
    # 泰文
    if re.search(r'[\u0e00-\u0e7f]', text):
        return "thai"
    # 希伯来文
    if re.search(r'[\u0590-\u05ff]', text):
        return "hebrew"
    # 希腊文
    if re.search(r'[\u0370-\u03ff]', text):
        return "greek"
    # 拉丁字母
    if re.search(r'[a-zA-Z]', text):
        return "latin"
    return None


@register_tool(name="match_ocr_to_poi", category="verification", tags=["ocr", "poi", "matching"])
class OCRPOIMatchTool(BaseTool):
    """OCR-POI 匹配工具

    将 OCR 识别的文本与 POI 名称进行匹配。
    """

    @property
    def name(self) -> str:
        return "match_ocr_to_poi"

    @property
    def description(self) -> str:
        return "Match OCR text with POI names to verify location"

    async def execute(
        self,
        ocr_texts: List[str],
        poi_names: List[str],
        threshold: float = 0.6,
        **kwargs,
    ) -> ToolResult:
        """执行 OCR-POI 匹配

        Args:
            ocr_texts: OCR 识别的文本列表
            poi_names: POI 名称列表
            threshold: 匹配阈值

        Returns:
            工具执行结果
        """
        try:
            matches = []
            total_score = 0.0

            for ocr_text in ocr_texts:
                best_match = None
                best_score = 0.0

                for poi_name in poi_names:
                    # 模糊匹配
                    matched, score = fuzzy_match(ocr_text, poi_name, threshold)

                    if score > best_score:
                        best_score = score
                        best_match = poi_name

                if best_match:
                    matches.append({
                        "ocr_text": ocr_text,
                        "poi_name": best_match,
                        "score": best_score,
                        "matched": best_score >= threshold,
                    })
                    total_score += best_score

            # 计算平均分数
            avg_score = total_score / len(ocr_texts) if ocr_texts else 0.0

            result = MatchResult(
                score=avg_score,
                matched=avg_score >= threshold,
                details={
                    "matches": matches,
                    "threshold": threshold,
                    "ocr_count": len(ocr_texts),
                    "poi_count": len(poi_names),
                },
            )

            logger.info(
                f"OCR-POI matching completed",
                score=avg_score,
                matched=result.matched,
                matches=len(matches),
            )

            return ToolResult.success(
                output=result.model_dump(),
                metadata={
                    "ocr_count": len(ocr_texts),
                    "poi_count": len(poi_names),
                    "avg_score": avg_score,
                },
            )

        except Exception as e:
            logger.error(f"OCR-POI matching failed", error=str(e), exc_info=True)
            return ToolResult.error(
                error=str(e),
                metadata={"ocr_count": len(ocr_texts), "poi_count": len(poi_names)},
            )


@register_tool(name="language_region_prior", category="verification", tags=["language", "region"])
class LanguageRegionPriorTool(BaseTool):
    """语言区域先验工具

    根据文本的语言和文字系统推断可能的地理区域。
    """

    @property
    def name(self) -> str:
        return "language_region_prior"

    @property
    def description(self) -> str:
        return "Infer geographic regions from text language and script"

    async def execute(
        self,
        text: str,
        **kwargs,
    ) -> ToolResult:
        """执行语言区域先验判断

        Args:
            text: 输入文本

        Returns:
            工具执行结果
        """
        try:
            # 检测语言
            language = detect_language(text)
            # 检测文字系统
            script = detect_script(text)

            # 获取可能的区域
            regions = []
            confidence = 0.0

            if language and language in LANGUAGE_REGION_MAP:
                regions.extend(LANGUAGE_REGION_MAP[language])
                confidence += 0.6

            if script and script in SCRIPT_REGION_MAP:
                script_regions = SCRIPT_REGION_MAP[script]
                # 如果语言和文字系统都匹配，提高置信度
                if regions:
                    regions = list(set(regions) & set(script_regions))
                    confidence = 0.9
                else:
                    regions = script_regions
                    confidence = 0.4

            # 去重
            regions = list(set(regions))

            result = LanguageRegion(
                language=language or "unknown",
                script=script,
                regions=regions,
                confidence=min(confidence, 1.0),
            )

            logger.info(
                f"Language region prior completed",
                language=language,
                script=script,
                regions=regions,
                confidence=result.confidence,
            )

            return ToolResult.success(
                output=result.model_dump(),
                metadata={
                    "text_length": len(text),
                    "language": language,
                    "script": script,
                },
            )

        except Exception as e:
            logger.error(f"Language region prior failed", error=str(e), exc_info=True)
            return ToolResult.error(
                error=str(e),
                metadata={"text": text[:100]},
            )


@register_tool(name="road_topology_check", category="verification", tags=["road", "topology"])
class RoadTopologyCheckTool(BaseTool):
    """道路拓扑检查工具

    检查候选位置的道路拓扑是否与图像中的道路结构匹配。
    """

    @property
    def name(self) -> str:
        return "road_topology_check"

    @property
    def description(self) -> str:
        return "Check if road topology matches the candidate location"

    async def execute(
        self,
        observed_roads: List[str],
        candidate_roads: List[str],
        threshold: float = 0.5,
        **kwargs,
    ) -> ToolResult:
        """执行道路拓扑检查

        Args:
            observed_roads: 观察到的道路特征列表
            candidate_roads: 候选位置的道路列表
            threshold: 匹配阈值

        Returns:
            工具执行结果
        """
        try:
            # 使用包含匹配
            matched, score = contains_match(
                " ".join(candidate_roads),
                observed_roads,
            )

            result = MatchResult(
                score=score,
                matched=score >= threshold,
                details={
                    "observed_count": len(observed_roads),
                    "candidate_count": len(candidate_roads),
                    "threshold": threshold,
                },
            )

            logger.info(
                f"Road topology check completed",
                score=score,
                matched=result.matched,
            )

            return ToolResult.success(
                output=result.model_dump(),
                metadata={
                    "observed_count": len(observed_roads),
                    "candidate_count": len(candidate_roads),
                    "score": score,
                },
            )

        except Exception as e:
            logger.error(f"Road topology check failed", error=str(e), exc_info=True)
            return ToolResult.error(
                error=str(e),
                metadata={
                    "observed_count": len(observed_roads),
                    "candidate_count": len(candidate_roads),
                },
            )


async def match_ocr_to_poi(
    ocr_texts: List[str],
    poi_names: List[str],
    threshold: float = 0.6,
) -> MatchResult:
    """便捷函数：OCR-POI 匹配

    Args:
        ocr_texts: OCR 文本列表
        poi_names: POI 名称列表
        threshold: 匹配阈值

    Returns:
        匹配结果
    """
    matches = []
    total_score = 0.0

    for ocr_text in ocr_texts:
        best_score = 0.0
        best_match = None

        for poi_name in poi_names:
            matched, score = fuzzy_match(ocr_text, poi_name, threshold)
            if score > best_score:
                best_score = score
                best_match = poi_name

        if best_match:
            total_score += best_score

    avg_score = total_score / len(ocr_texts) if ocr_texts else 0.0

    return MatchResult(
        score=avg_score,
        matched=avg_score >= threshold,
        details={"threshold": threshold},
    )


async def language_region_prior(text: str) -> LanguageRegion:
    """便捷函数：语言区域先验

    Args:
        text: 文本

    Returns:
        语言区域
    """
    language = detect_language(text)
    script = detect_script(text)

    regions = []
    confidence = 0.0

    if language and language in LANGUAGE_REGION_MAP:
        regions.extend(LANGUAGE_REGION_MAP[language])
        confidence += 0.6

    if script and script in SCRIPT_REGION_MAP:
        script_regions = SCRIPT_REGION_MAP[script]
        if regions:
            regions = list(set(regions) & set(script_regions))
            confidence = 0.9
        else:
            regions = script_regions
            confidence = 0.4

    regions = list(set(regions))

    return LanguageRegion(
        language=language or "unknown",
        script=script,
        regions=regions,
        confidence=min(confidence, 1.0),
    )


# 便捷函数包装器
async def match_ocr_poi(
    ocr_texts: List[str],
    poi_name: str,
    threshold: float = 0.6,
) -> MatchResult:
    """
    便捷函数：匹配 OCR 文本和 POI 名称
    
    Args:
        ocr_texts: OCR 文本列表
        poi_name: POI 名称
        threshold: 匹配阈值
    
    Returns:
        MatchResult: 匹配结果
    """
    tool = OCRPOIMatchTool()
    result = await tool.execute(ocr_texts=ocr_texts, poi_name=poi_name, threshold=threshold)
    if result.success:
        return MatchResult(**result.output)
    return MatchResult(score=0.0, matched=False, details={"error": result.error})


async def check_language_prior(
    text: str,
    candidate_region: str,
) -> LanguageRegion:
    """
    便捷函数：检查语言区域先验
    
    Args:
        text: 文本内容
        candidate_region: 候选区域
    
    Returns:
        LanguageRegion: 语言区域信息
    """
    tool = LanguageRegionPriorTool()
    result = await tool.execute(text=text, candidate_region=candidate_region)
    if result.success:
        return LanguageRegion(**result.output)
    return LanguageRegion(language="unknown", regions=[], confidence=0.0)


async def verify_road_topology(
    candidate_location: Dict[str, float],
    image_features: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    便捷函数：验证道路拓扑
    
    Args:
        candidate_location: 候选位置 {"lat": float, "lon": float}
        image_features: 图像特征列表
    
    Returns:
        验证结果字典
    """
    tool = RoadTopologyCheckTool()
    result = await tool.execute(
        candidate_location=candidate_location,
        image_features=image_features,
    )
    if result.success:
        return result.output
    return {"verified": False, "error": result.error}


__all__ = [
    "MatchResult",
    "LanguageRegion",
    "OCRPOIMatchTool",
    "LanguageRegionPriorTool",
    "RoadTopologyCheckTool",
    "match_ocr_to_poi",
    "language_region_prior",
    "fuzzy_match",
    "contains_match",
    "detect_language",
    "detect_script",
]

