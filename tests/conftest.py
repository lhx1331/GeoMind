"""
Pytest 配置和共享 fixtures

将在后续任务中完善
"""
import pytest
from pathlib import Path

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def test_data_dir():
    """返回测试数据目录路径"""
    return TEST_DATA_DIR


@pytest.fixture
def sample_image_path(test_data_dir):
    """返回示例图片路径（将在后续添加）"""
    image_path = test_data_dir / "images" / "sample.jpg"
    # 如果文件不存在，返回 None
    return image_path if image_path.exists() else None

