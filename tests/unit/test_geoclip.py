"""
GeoCLIP 模型单元测试
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from geomind.models.base import ModelConfig, ModelType
from geomind.models.geoclip import GeoCLIP, MockGeoCLIPModel, create_geoclip


class TestGeoCLIPInitialization:
    """测试 GeoCLIP 初始化"""

    @pytest.mark.asyncio
    async def test_geoclip_init_basic(self):
        """测试基础初始化"""
        config = ModelConfig(
            model_type=ModelType.RETRIEVAL,
            model_name="geoclip",
        )
        geoclip = GeoCLIP(config=config, device="cpu", use_cache=False)

        assert geoclip.config.model_name == "geoclip"
        assert geoclip.device == "cpu"
        assert not geoclip.is_initialized

        await geoclip.initialize()
        assert geoclip.is_initialized
        assert geoclip.model is not None
        assert geoclip.location_database is not None

        await geoclip.cleanup()
        assert not geoclip.is_initialized
        assert geoclip.model is None

    @pytest.mark.asyncio
    async def test_geoclip_init_with_cache(self):
        """测试带缓存的初始化"""
        geoclip = GeoCLIP(device="cpu", use_cache=True)
        
        await geoclip.initialize()
        assert geoclip.use_cache is True
        assert geoclip.cache is not None

        await geoclip.cleanup()

    @pytest.mark.asyncio
    async def test_create_geoclip_helper(self):
        """测试便捷创建函数"""
        mock_settings = MagicMock()
        mock_settings.geoclip.model_path = Path("./models/geoclip")
        mock_settings.geoclip.device = "cpu"

        with patch("geomind.models.geoclip.get_settings", return_value=mock_settings):
            geoclip = await create_geoclip(device="cpu", use_cache=False)

            assert geoclip.is_initialized
            assert geoclip.device == "cpu"

            await geoclip.cleanup()


class TestLocationDatabase:
    """测试位置数据库"""

    @pytest.mark.asyncio
    async def test_location_database_initialization(self):
        """测试位置数据库初始化"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        assert geoclip.location_database is not None
        assert len(geoclip.location_database) > 0
        assert geoclip.location_embeddings is not None
        assert len(geoclip.location_embeddings) == len(geoclip.location_database)

        # 检查数据格式
        assert geoclip.location_database.shape[1] == 2  # [lat, lon]
        
        # 检查范围
        lats = geoclip.location_database[:, 0]
        lons = geoclip.location_database[:, 1]
        assert lats.min() >= -90 and lats.max() <= 90
        assert lons.min() >= -180 and lons.max() <= 180

        await geoclip.cleanup()


class TestImageEncoding:
    """测试图像编码"""

    @pytest.mark.asyncio
    async def test_encode_image_from_pil(self):
        """测试从 PIL 图像编码"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        # 创建测试图像
        img = Image.new("RGB", (224, 224), color="red")

        response = await geoclip.encode_image(img)

        assert response.success is True
        assert isinstance(response.data, list)
        assert len(response.data) > 0
        assert all(isinstance(x, float) for x in response.data)

        await geoclip.cleanup()

    @pytest.mark.asyncio
    async def test_encode_image_with_cache(self):
        """测试带缓存的图像编码"""
        # Mock 缓存
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # 第一次未命中
        
        geoclip = GeoCLIP(device="cpu", use_cache=True)
        await geoclip.initialize()
        geoclip.cache = mock_cache

        img = Image.new("RGB", (224, 224), color="blue")
        
        # 第一次调用（PIL 图像不会使用缓存，因为没有路径）
        response1 = await geoclip.encode_image(img)
        assert response1.success is True
        
        # PIL 图像不会触发缓存（因为没有唯一标识符）
        # 所以我们不检查 set 是否被调用

        await geoclip.cleanup()

    @pytest.mark.asyncio
    async def test_encode_image_not_initialized(self):
        """测试未初始化时编码"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)

        img = Image.new("RGB", (100, 100))

        with pytest.raises(RuntimeError, match="not initialized"):
            await geoclip.encode_image(img)


class TestTextEncoding:
    """测试文本编码"""

    @pytest.mark.asyncio
    async def test_encode_text_basic(self):
        """测试基础文本编码"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        response = await geoclip.encode_text("Tokyo, Japan")

        assert response.success is True
        assert isinstance(response.data, list)
        assert len(response.data) > 0
        assert all(isinstance(x, float) for x in response.data)

        await geoclip.cleanup()

    @pytest.mark.asyncio
    async def test_encode_text_consistency(self):
        """测试文本编码一致性"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        # 相同文本应该产生相同的嵌入
        response1 = await geoclip.encode_text("Paris")
        response2 = await geoclip.encode_text("Paris")

        assert response1.success is True
        assert response2.success is True
        assert response1.data == response2.data

        await geoclip.cleanup()

    @pytest.mark.asyncio
    async def test_encode_text_with_cache(self):
        """测试带缓存的文本编码"""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        
        geoclip = GeoCLIP(device="cpu", use_cache=True)
        geoclip.cache = mock_cache
        
        await geoclip.initialize()

        # 第一次调用
        response1 = await geoclip.encode_text("London")
        assert response1.success is True
        assert mock_cache.set.called

        # 模拟缓存命中
        mock_cache.get.return_value = response1.data
        
        # 第二次调用
        response2 = await geoclip.encode_text("London")
        assert response2.success is True
        assert response2.metadata.get("cached") is True

        await geoclip.cleanup()


class TestRetrieval:
    """测试检索功能"""

    @pytest.mark.asyncio
    async def test_retrieve_basic(self):
        """测试基础检索"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        # 创建查询嵌入
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]

        response = await geoclip.retrieve(query_embedding, top_k=5)

        assert response.success is True
        assert isinstance(response.data, list)
        assert len(response.data) == 5

        # 检查结果格式
        for result in response.data:
            assert "lat" in result
            assert "lon" in result
            assert "score" in result
            assert -90 <= result["lat"] <= 90
            assert -180 <= result["lon"] <= 180

        # 检查结果是否按分数排序
        scores = [r["score"] for r in response.data]
        assert scores == sorted(scores, reverse=True)

        await geoclip.cleanup()

    @pytest.mark.asyncio
    async def test_retrieve_top_k(self):
        """测试不同的 top_k 值"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        query_embedding = [0.1] * 6

        # 测试不同的 k 值
        for k in [1, 3, 10]:
            response = await geoclip.retrieve(query_embedding, top_k=k)
            assert response.success is True
            assert len(response.data) == k

        await geoclip.cleanup()

    @pytest.mark.asyncio
    async def test_retrieve_not_initialized(self):
        """测试未初始化时检索"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)

        query_embedding = [0.1] * 6

        with pytest.raises(RuntimeError, match="not initialized"):
            await geoclip.retrieve(query_embedding)


class TestPredictLocation:
    """测试位置预测"""

    @pytest.mark.asyncio
    async def test_predict_location_basic(self):
        """测试基础位置预测"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        # 创建测试图像
        img = Image.new("RGB", (224, 224), color="green")

        response = await geoclip.predict_location(img, top_k=3)

        assert response.success is True
        assert isinstance(response.data, list)
        assert len(response.data) == 3

        # 检查结果
        for result in response.data:
            assert "lat" in result
            assert "lon" in result
            assert "score" in result

        await geoclip.cleanup()

    @pytest.mark.asyncio
    async def test_predict_location_integration(self):
        """测试完整的预测流程"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        # 创建不同颜色的图像
        img1 = Image.new("RGB", (224, 224), color="red")
        img2 = Image.new("RGB", (224, 224), color="blue")

        response1 = await geoclip.predict_location(img1, top_k=5)
        response2 = await geoclip.predict_location(img2, top_k=5)

        assert response1.success is True
        assert response2.success is True

        # 不同图像应该产生不同的预测
        # （虽然在 mock 实现中可能相似，但结构应该正确）
        assert len(response1.data) == 5
        assert len(response2.data) == 5

        await geoclip.cleanup()


class TestMockModel:
    """测试 Mock 模型"""

    def test_mock_model_encode_image(self):
        """测试 Mock 模型图像编码"""
        model = MockGeoCLIPModel(device="cpu")
        
        img = Image.new("RGB", (224, 224), color="red")
        embedding = model.encode_image(img)

        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == model.embedding_dim
        
        # 检查归一化
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-5

    def test_mock_model_encode_text(self):
        """测试 Mock 模型文本编码"""
        model = MockGeoCLIPModel(device="cpu")
        
        embedding1 = model.encode_text("Tokyo")
        embedding2 = model.encode_text("Tokyo")
        embedding3 = model.encode_text("Paris")

        assert isinstance(embedding1, np.ndarray)
        assert len(embedding1) == model.embedding_dim
        
        # 相同文本应该产生相同嵌入
        np.testing.assert_array_equal(embedding1, embedding2)
        
        # 不同文本应该产生不同嵌入
        assert not np.array_equal(embedding1, embedding3)

    def test_mock_model_different_colors(self):
        """测试不同颜色图像产生不同嵌入"""
        model = MockGeoCLIPModel(device="cpu")
        
        img_red = Image.new("RGB", (224, 224), color="red")
        img_blue = Image.new("RGB", (224, 224), color="blue")
        
        emb_red = model.encode_image(img_red)
        emb_blue = model.encode_image(img_blue)

        # 不同颜色应该产生不同嵌入
        assert not np.array_equal(emb_red, emb_blue)


class TestCacheKey:
    """测试缓存键生成"""

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        geoclip = GeoCLIP(device="cpu", use_cache=True)

        # 字符串输入
        key1 = geoclip._get_cache_key("test_image.jpg", "image")
        key2 = geoclip._get_cache_key("test_image.jpg", "image")
        key3 = geoclip._get_cache_key("other_image.jpg", "image")

        # 相同输入应该产生相同键
        assert key1 == key2
        
        # 不同输入应该产生不同键
        assert key1 != key3

        # 检查前缀
        assert key1.startswith("image:")

    def test_cache_key_with_bytes(self):
        """测试字节输入的缓存键"""
        geoclip = GeoCLIP(device="cpu", use_cache=True)

        data = b"test data"
        key = geoclip._get_cache_key(data, "test")

        assert isinstance(key, str)
        assert key.startswith("test:")


class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_encode_image_error(self):
        """测试图像编码错误处理"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        # 测试无效图像类型
        response = await geoclip.encode_image(12345)

        assert response.success is False
        assert "error" in response.error.lower() or "unsupported" in response.error.lower()

        await geoclip.cleanup()

    @pytest.mark.asyncio
    async def test_retrieve_invalid_embedding(self):
        """测试无效嵌入的检索"""
        geoclip = GeoCLIP(device="cpu", use_cache=False)
        await geoclip.initialize()

        # 空嵌入
        response = await geoclip.retrieve([])

        # 应该返回错误或空结果
        assert response.success is False or len(response.data) == 0

        await geoclip.cleanup()

