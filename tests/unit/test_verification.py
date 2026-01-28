"""
验证工具单元测试
"""

import pytest

from geomind.tools.base import ToolStatus
from geomind.tools.mcp.verification import (
    LanguageRegionPriorTool,
    MatchResult,
    OCRPOIMatchTool,
    RoadTopologyCheckTool,
    contains_match,
    detect_language,
    detect_script,
    fuzzy_match,
    language_region_prior,
    match_ocr_to_poi,
    normalize_text,
)
from geomind.tools.registry import get_registry


class TestTextProcessing:
    """测试文本处理函数"""

    def test_normalize_text(self):
        """测试文本标准化"""
        assert normalize_text("Tokyo Station") == "tokyo station"
        assert normalize_text("  Tokyo   Station  ") == "tokyo station"
        assert normalize_text("Tokyo, Station!") == "tokyo station"

    def test_fuzzy_match_exact(self):
        """测试精确匹配"""
        matched, score = fuzzy_match("Tokyo Station", "Tokyo Station")
        assert matched is True
        assert score == 1.0

    def test_fuzzy_match_similar(self):
        """测试相似匹配"""
        matched, score = fuzzy_match("Tokyo Station", "Tokyo Stat", threshold=0.6)
        assert matched is True
        assert score > 0.6

    def test_fuzzy_match_different(self):
        """测试不匹配"""
        matched, score = fuzzy_match("Tokyo Station", "Osaka Castle", threshold=0.6)
        assert matched is False
        assert score < 0.6

    def test_contains_match(self):
        """测试包含匹配"""
        matched, score = contains_match("Tokyo Station Central", ["tokyo", "station"])
        assert matched is True
        assert score == 1.0

    def test_contains_match_partial(self):
        """测试部分包含"""
        matched, score = contains_match("Tokyo Station", ["tokyo", "osaka"])
        assert matched is True
        assert score == 0.5

    def test_contains_match_none(self):
        """测试无匹配"""
        matched, score = contains_match("Tokyo Station", ["osaka", "kyoto"])
        assert matched is False
        assert score == 0.0


class TestLanguageDetection:
    """测试语言检测"""

    def test_detect_chinese(self):
        """测试检测中文"""
        assert detect_language("北京站") == "zh"

    def test_detect_japanese(self):
        """测试检测日文"""
        # 纯汉字会被识别为中文，需要包含假名
        assert detect_language("とうきょうえき") == "ja"
        assert detect_language("トウキョウエキ") == "ja"
        assert detect_language("東京駅です") == "ja"  # 包含假名

    def test_detect_korean(self):
        """测试检测韩文"""
        assert detect_language("서울역") == "ko"

    def test_detect_arabic(self):
        """测试检测阿拉伯文"""
        assert detect_language("محطة طوكيو") == "ar"

    def test_detect_russian(self):
        """测试检测俄文"""
        assert detect_language("Токио") == "ru"

    def test_detect_thai(self):
        """测试检测泰文"""
        assert detect_language("สถานีโตเกียว") == "th"

    def test_detect_english(self):
        """测试检测英文"""
        assert detect_language("Tokyo Station") == "en"


class TestScriptDetection:
    """测试文字系统检测"""

    def test_detect_han(self):
        """测试检测汉字"""
        assert detect_script("北京站") == "han"

    def test_detect_hiragana(self):
        """测试检测平假名"""
        assert detect_script("ひらがな") == "hiragana"

    def test_detect_katakana(self):
        """测试检测片假名"""
        assert detect_script("カタカナ") == "katakana"

    def test_detect_hangul(self):
        """测试检测韩文"""
        assert detect_script("한글") == "hangul"

    def test_detect_arabic(self):
        """测试检测阿拉伯文"""
        assert detect_script("العربية") == "arabic"

    def test_detect_cyrillic(self):
        """测试检测西里尔字母"""
        assert detect_script("Кириллица") == "cyrillic"

    def test_detect_latin(self):
        """测试检测拉丁字母"""
        assert detect_script("Latin") == "latin"


class TestMatchResult:
    """测试 MatchResult 数据模型"""

    def test_create_match_result(self):
        """测试创建匹配结果"""
        result = MatchResult(
            score=0.85,
            matched=True,
            details={"method": "fuzzy"},
        )

        assert result.score == 0.85
        assert result.matched is True
        assert result.details["method"] == "fuzzy"


class TestOCRPOIMatchTool:
    """测试 OCR-POI 匹配工具"""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """测试成功匹配"""
        tool = OCRPOIMatchTool()
        result = await tool.execute(
            ocr_texts=["Tokyo Station", "Central Post"],
            poi_names=["Tokyo Station", "Central Post Office"],
            threshold=0.6,
        )

        assert result.status == ToolStatus.SUCCESS
        assert result.output["matched"] is True
        assert result.output["score"] > 0.6

    @pytest.mark.asyncio
    async def test_execute_no_match(self):
        """测试无匹配"""
        tool = OCRPOIMatchTool()
        result = await tool.execute(
            ocr_texts=["Tokyo Station"],
            poi_names=["Osaka Castle"],
            threshold=0.8,
        )

        assert result.status == ToolStatus.SUCCESS
        assert result.output["matched"] is False

    @pytest.mark.asyncio
    async def test_execute_empty_lists(self):
        """测试空列表"""
        tool = OCRPOIMatchTool()
        result = await tool.execute(
            ocr_texts=[],
            poi_names=[],
        )

        assert result.status == ToolStatus.SUCCESS
        assert result.output["score"] == 0.0


class TestLanguageRegionPriorTool:
    """测试语言区域先验工具"""

    @pytest.mark.asyncio
    async def test_execute_japanese(self):
        """测试日文"""
        tool = LanguageRegionPriorTool()
        result = await tool.execute(text="東京駅です")  # 包含假名

        assert result.status == ToolStatus.SUCCESS
        assert result.output["language"] == "ja"
        assert "JP" in result.output["regions"]
        assert result.output["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_execute_chinese(self):
        """测试中文"""
        tool = LanguageRegionPriorTool()
        result = await tool.execute(text="北京站")

        assert result.status == ToolStatus.SUCCESS
        assert result.output["language"] == "zh"
        assert "CN" in result.output["regions"]

    @pytest.mark.asyncio
    async def test_execute_korean(self):
        """测试韩文"""
        tool = LanguageRegionPriorTool()
        result = await tool.execute(text="서울역")

        assert result.status == ToolStatus.SUCCESS
        assert result.output["language"] == "ko"
        assert "KR" in result.output["regions"]

    @pytest.mark.asyncio
    async def test_execute_english(self):
        """测试英文"""
        tool = LanguageRegionPriorTool()
        result = await tool.execute(text="Tokyo Station")

        assert result.status == ToolStatus.SUCCESS
        assert result.output["language"] == "en"
        assert len(result.output["regions"]) > 0


class TestRoadTopologyCheckTool:
    """测试道路拓扑检查工具"""

    @pytest.mark.asyncio
    async def test_execute_match(self):
        """测试匹配"""
        tool = RoadTopologyCheckTool()
        result = await tool.execute(
            observed_roads=["highway", "intersection"],
            candidate_roads=["Highway 1", "Main Street Intersection", "Bridge"],
            threshold=0.5,
        )

        assert result.status == ToolStatus.SUCCESS
        assert result.output["matched"] is True

    @pytest.mark.asyncio
    async def test_execute_no_match(self):
        """测试不匹配"""
        tool = RoadTopologyCheckTool()
        result = await tool.execute(
            observed_roads=["highway", "bridge"],
            candidate_roads=["Local Street", "Alley"],
            threshold=0.8,
        )

        assert result.status == ToolStatus.SUCCESS
        assert result.output["matched"] is False

    @pytest.mark.asyncio
    async def test_execute_empty_roads(self):
        """测试空道路列表"""
        tool = RoadTopologyCheckTool()
        result = await tool.execute(
            observed_roads=[],
            candidate_roads=["Highway 1"],
        )

        assert result.status == ToolStatus.SUCCESS
        assert result.output["score"] == 0.0


class TestConvenienceFunctions:
    """测试便捷函数"""

    @pytest.mark.asyncio
    async def test_match_ocr_to_poi(self):
        """测试 OCR-POI 匹配函数"""
        result = await match_ocr_to_poi(
            ocr_texts=["Tokyo Station"],
            poi_names=["Tokyo Station", "Tokyo Tower"],
            threshold=0.6,
        )

        assert isinstance(result, MatchResult)
        assert result.matched is True

    @pytest.mark.asyncio
    async def test_language_region_prior(self):
        """测试语言区域先验函数"""
        result = await language_region_prior("東京駅です")  # 包含假名

        assert result.language == "ja"
        assert "JP" in result.regions
        assert result.confidence > 0.5


class TestToolRegistration:
    """测试工具注册"""

    def test_ocr_poi_match_tool_registered(self):
        """测试 OCR-POI 匹配工具已注册"""
        registry = get_registry()
        assert registry.has("match_ocr_to_poi")

        tool = registry.get("match_ocr_to_poi")
        assert tool is not None
        assert tool.name == "match_ocr_to_poi"
        assert tool.category == "verification"

    def test_language_region_prior_tool_registered(self):
        """测试语言区域先验工具已注册"""
        registry = get_registry()
        assert registry.has("language_region_prior")

        tool = registry.get("language_region_prior")
        assert tool is not None
        assert tool.name == "language_region_prior"

    def test_road_topology_check_tool_registered(self):
        """测试道路拓扑检查工具已注册"""
        registry = get_registry()
        assert registry.has("road_topology_check")

        tool = registry.get("road_topology_check")
        assert tool is not None
        assert tool.name == "road_topology_check"


class TestEdgeCases:
    """测试边界情况"""

    def test_fuzzy_match_empty_strings(self):
        """测试空字符串匹配"""
        matched, score = fuzzy_match("", "")
        assert matched is True
        assert score == 1.0

    def test_detect_language_empty(self):
        """测试检测空文本"""
        assert detect_language("") == "en"

    def test_detect_script_empty(self):
        """测试检测空文本的文字系统"""
        assert detect_script("") is None

    def test_detect_language_mixed(self):
        """测试检测混合语言"""
        # 应该检测到第一个出现的语言
        result = detect_language("Hello 你好")
        assert result in ["zh", "en"]

    @pytest.mark.asyncio
    async def test_match_ocr_to_poi_empty(self):
        """测试空列表匹配"""
        result = await match_ocr_to_poi([], [])
        assert result.score == 0.0
        assert result.matched is False

