"""
工具函数单元测试
"""

import tempfile
import time
from pathlib import Path

import pytest
from PIL import Image

from geomind.utils.cache import MemoryCache, cache_key, get_cache
from geomind.utils.image import (
    crop_image,
    extract_exif,
    get_image_info,
    load_image,
    resize_image,
    save_image,
)
from geomind.utils.retry import retry, retry_on_exception


class TestImageUtils:
    """测试图像处理工具"""

    @pytest.fixture
    def sample_image(self):
        """创建测试图像"""
        img = Image.new("RGB", (800, 600), color="red")
        return img

    @pytest.fixture
    def sample_image_file(self, sample_image):
        """创建测试图像文件"""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            sample_image.save(f, format="JPEG")
            return Path(f.name)

    def test_load_image_from_file(self, sample_image_file):
        """测试从文件加载图像"""
        image = load_image(sample_image_file)
        assert image is not None
        assert image.size == (800, 600)
        # 清理
        sample_image_file.unlink()

    def test_load_image_with_max_size(self, sample_image_file):
        """测试加载图像并限制大小"""
        image = load_image(sample_image_file, max_size=(400, 300))
        assert image.width <= 400
        assert image.height <= 300
        # 清理
        sample_image_file.unlink()

    def test_resize_image(self, sample_image):
        """测试调整图像大小"""
        resized = resize_image(sample_image, (400, 300))
        assert resized.width <= 400
        assert resized.height <= 300

    def test_resize_image_keep_aspect_ratio(self, sample_image):
        """测试保持宽高比的缩放"""
        resized = resize_image(sample_image, (400, 300), keep_aspect_ratio=True)
        # 应该保持宽高比 800:600 = 4:3
        assert resized.width == 400
        assert resized.height == 300

    def test_crop_image(self, sample_image):
        """测试裁剪图像"""
        cropped = crop_image(sample_image, (100, 100, 400, 300))
        assert cropped.size == (300, 200)

    def test_crop_image_invalid_bbox(self, sample_image):
        """测试无效的裁剪区域"""
        with pytest.raises(ValueError):
            crop_image(sample_image, (100, 100, 50, 50))  # right < left

    def test_save_image(self, sample_image):
        """测试保存图像"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jpg"
            save_image(sample_image, output_path, quality=90)
            assert output_path.exists()

    def test_get_image_info(self, sample_image):
        """测试获取图像信息"""
        info = get_image_info(sample_image)
        assert info["width"] == 800
        assert info["height"] == 600
        assert info["size"] == (800, 600)
        assert info["mode"] == "RGB"

    def test_extract_exif(self, sample_image_file):
        """测试提取 EXIF 数据"""
        exif_data = extract_exif(sample_image_file)
        # 测试图像可能没有 EXIF，但不应该抛出异常
        assert isinstance(exif_data, dict)
        # 清理
        sample_image_file.unlink()


class TestCacheUtils:
    """测试缓存工具"""

    def test_memory_cache_set_get(self):
        """测试内存缓存设置和获取"""
        cache = MemoryCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_memory_cache_ttl(self):
        """测试内存缓存 TTL"""
        cache = MemoryCache(default_ttl=1)
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        
        # 等待过期
        time.sleep(1.5)
        assert cache.get("key1") is None

    def test_memory_cache_delete(self):
        """测试删除缓存"""
        cache = MemoryCache()
        cache.set("key1", "value1")
        assert cache.exists("key1")
        
        cache.delete("key1")
        assert not cache.exists("key1")

    def test_memory_cache_clear(self):
        """测试清空缓存"""
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        assert not cache.exists("key1")
        assert not cache.exists("key2")

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        key1 = cache_key("arg1", "arg2", param1="value1")
        key2 = cache_key("arg1", "arg2", param1="value1")
        key3 = cache_key("arg1", "arg3", param1="value1")
        
        # 相同参数应该生成相同的键
        assert key1 == key2
        # 不同参数应该生成不同的键
        assert key1 != key3


class TestRetryUtils:
    """测试重试装饰器"""

    def test_retry_success(self):
        """测试成功执行（无需重试）"""
        @retry(max_retries=3)
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"

    def test_retry_with_failure(self):
        """测试失败后重试"""
        attempt_count = {"count": 0}
        
        @retry(max_retries=3, backoff_factor=0.1)
        def failing_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = failing_func()
        assert result == "success"
        assert attempt_count["count"] == 3

    def test_retry_max_attempts_exceeded(self):
        """测试超过最大重试次数"""
        @retry(max_retries=2, backoff_factor=0.1)
        def always_fail():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            always_fail()

    def test_retry_specific_exception(self):
        """测试只重试特定异常"""
        @retry(max_retries=3, backoff_factor=0.1, exceptions=(ValueError,))
        def specific_exception():
            raise TypeError("Wrong exception type")
        
        # TypeError 不在重试列表中，应该直接抛出
        with pytest.raises(TypeError):
            specific_exception()

    @pytest.mark.asyncio
    async def test_async_retry(self):
        """测试异步函数重试"""
        attempt_count = {"count": 0}
        
        @retry(max_retries=3, backoff_factor=0.1)
        async def async_failing_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = await async_failing_func()
        assert result == "success"
        assert attempt_count["count"] == 2

    def test_retry_on_exception_decorator(self):
        """测试 retry_on_exception 装饰器"""
        attempt_count = {"count": 0}
        
        @retry_on_exception(ValueError, max_retries=2, backoff_factor=0.1)
        def func_with_specific_retry():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise ValueError("Retry this")
            return "success"
        
        result = func_with_specific_retry()
        assert result == "success"
        assert attempt_count["count"] == 2


class TestIntegration:
    """测试工具集成"""

    def test_image_and_cache(self):
        """测试图像处理和缓存的集成"""
        # 创建图像
        img = Image.new("RGB", (100, 100), color="blue")
        
        # 使用缓存
        cache = MemoryCache()
        cache.set("test_image", img, ttl=60)
        
        # 从缓存获取
        cached_img = cache.get("test_image")
        assert cached_img is not None
        assert cached_img.size == (100, 100)

    def test_retry_with_cache(self):
        """测试重试和缓存的集成"""
        cache = MemoryCache()
        attempt_count = {"count": 0}
        
        @retry(max_retries=3, backoff_factor=0.1)
        def func_with_cache(key):
            # 先检查缓存
            cached = cache.get(key)
            if cached:
                return cached
            
            # 模拟可能失败的操作
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise ValueError("Temporary error")
            
            result = "computed_value"
            cache.set(key, result)
            return result
        
        result = func_with_cache("test_key")
        assert result == "computed_value"
        assert attempt_count["count"] == 2
        
        # 第二次调用应该从缓存获取
        attempt_count["count"] = 0
        result2 = func_with_cache("test_key")
        assert result2 == "computed_value"
        assert attempt_count["count"] == 0  # 没有重新计算

