"""
图像处理工具

提供图像加载、裁剪、EXIF 提取等功能。
"""

from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import exifread
from PIL import Image

from geomind.utils.logging import get_logger

logger = get_logger(__name__)


def load_image(
    image_source: Union[str, Path, bytes, BytesIO],
    max_size: Optional[Tuple[int, int]] = None,
) -> Image.Image:
    """
    加载图像

    Args:
        image_source: 图像来源（文件路径、字节流或 BytesIO）
        max_size: 最大尺寸 (width, height)，超过则缩放

    Returns:
        PIL Image 对象

    Raises:
        FileNotFoundError: 图像文件不存在
        ValueError: 图像格式不支持
    """
    try:
        # 从不同来源加载图像
        if isinstance(image_source, (str, Path)):
            image_path = Path(image_source)
            if not image_path.exists():
                raise FileNotFoundError(f"图像文件不存在: {image_path}")
            image = Image.open(image_path)
            logger.debug("从文件加载图像", path=str(image_path))
        elif isinstance(image_source, bytes):
            image = Image.open(BytesIO(image_source))
            logger.debug("从字节流加载图像", size=len(image_source))
        elif isinstance(image_source, BytesIO):
            image = Image.open(image_source)
            logger.debug("从 BytesIO 加载图像")
        else:
            raise ValueError(f"不支持的图像源类型: {type(image_source)}")

        # 转换为 RGB（如果需要）
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
            logger.debug("转换图像模式为 RGB", original_mode=image.mode)

        # 缩放（如果需要）
        if max_size:
            image = resize_image(image, max_size)

        return image

    except Exception as e:
        logger.error("加载图像失败", error=str(e))
        raise


def resize_image(
    image: Image.Image,
    max_size: Tuple[int, int],
    keep_aspect_ratio: bool = True,
) -> Image.Image:
    """
    调整图像大小

    Args:
        image: PIL Image 对象
        max_size: 最大尺寸 (width, height)
        keep_aspect_ratio: 是否保持宽高比

    Returns:
        调整后的 PIL Image 对象
    """
    width, height = image.size
    max_width, max_height = max_size

    if width <= max_width and height <= max_height:
        # 不需要缩放
        return image

    if keep_aspect_ratio:
        # 保持宽高比
        ratio = min(max_width / width, max_height / height)
        new_size = (int(width * ratio), int(height * ratio))
    else:
        new_size = max_size

    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    logger.debug(
        "调整图像大小",
        original_size=(width, height),
        new_size=new_size,
        keep_aspect_ratio=keep_aspect_ratio,
    )
    return resized


def crop_image(
    image: Image.Image,
    bbox: Tuple[int, int, int, int],
) -> Image.Image:
    """
    裁剪图像

    Args:
        image: PIL Image 对象
        bbox: 裁剪区域 (left, top, right, bottom)

    Returns:
        裁剪后的 PIL Image 对象
    """
    left, top, right, bottom = bbox

    # 验证裁剪区域
    width, height = image.size
    if left < 0 or top < 0 or right > width or bottom > height:
        raise ValueError(f"裁剪区域超出图像边界: {bbox}, 图像大小: {(width, height)}")

    if left >= right or top >= bottom:
        raise ValueError(f"裁剪区域无效: {bbox}")

    cropped = image.crop(bbox)
    logger.debug("裁剪图像", bbox=bbox, original_size=(width, height))
    return cropped


def extract_exif(image_source: Union[str, Path, bytes, BytesIO]) -> Dict[str, any]:
    """
    提取 EXIF 数据

    Args:
        image_source: 图像来源（文件路径、字节流或 BytesIO）

    Returns:
        EXIF 数据字典

    Raises:
        FileNotFoundError: 图像文件不存在
    """
    exif_data = {}

    try:
        # 打开文件或流
        if isinstance(image_source, (str, Path)):
            image_path = Path(image_source)
            if not image_path.exists():
                raise FileNotFoundError(f"图像文件不存在: {image_path}")
            with open(image_path, "rb") as f:
                tags = exifread.process_file(f, details=False)
        elif isinstance(image_source, bytes):
            tags = exifread.process_file(BytesIO(image_source), details=False)
        elif isinstance(image_source, BytesIO):
            tags = exifread.process_file(image_source, details=False)
        else:
            raise ValueError(f"不支持的图像源类型: {type(image_source)}")

        # 转换为普通字典
        for tag, value in tags.items():
            # 跳过缩略图数据
            if "thumbnail" in tag.lower():
                continue
            exif_data[tag] = str(value)

        logger.debug("提取 EXIF 数据", tags_count=len(exif_data))
        return exif_data

    except Exception as e:
        logger.warning("提取 EXIF 数据失败", error=str(e))
        return {}


def get_gps_info(exif_data: Dict[str, any]) -> Optional[Tuple[float, float]]:
    """
    从 EXIF 数据中提取 GPS 坐标

    Args:
        exif_data: EXIF 数据字典

    Returns:
        GPS 坐标 (纬度, 经度)，如果没有则返回 None
    """
    try:
        # 查找 GPS 标签
        gps_lat = exif_data.get("GPS GPSLatitude")
        gps_lat_ref = exif_data.get("GPS GPSLatitudeRef")
        gps_lon = exif_data.get("GPS GPSLongitude")
        gps_lon_ref = exif_data.get("GPS GPSLongitudeRef")

        if not (gps_lat and gps_lon and gps_lat_ref and gps_lon_ref):
            return None

        # 转换坐标
        lat = _convert_to_degrees(gps_lat)
        if gps_lat_ref == "S":
            lat = -lat

        lon = _convert_to_degrees(gps_lon)
        if gps_lon_ref == "W":
            lon = -lon

        logger.debug("提取 GPS 坐标", latitude=lat, longitude=lon)
        return (lat, lon)

    except Exception as e:
        logger.warning("提取 GPS 坐标失败", error=str(e))
        return None


def _convert_to_degrees(value: str) -> float:
    """
    将 EXIF GPS 坐标转换为十进制度数

    Args:
        value: GPS 坐标字符串，格式如 "[45, 30, 15]"

    Returns:
        十进制度数
    """
    # 解析字符串，格式可能是 "[45, 30, 15]" 或 "45, 30, 15"
    value = value.strip("[]")
    parts = [float(x.strip()) for x in value.split(",")]

    if len(parts) != 3:
        raise ValueError(f"无效的 GPS 坐标格式: {value}")

    degrees, minutes, seconds = parts
    return degrees + minutes / 60.0 + seconds / 3600.0


def save_image(
    image: Image.Image,
    output_path: Union[str, Path],
    format: Optional[str] = None,
    quality: int = 95,
) -> None:
    """
    保存图像

    Args:
        image: PIL Image 对象
        output_path: 输出路径
        format: 图像格式（如 JPEG, PNG），默认从文件扩展名推断
        quality: JPEG 质量（1-100）

    Raises:
        ValueError: 无效的格式或质量参数
    """
    output_path = Path(output_path)

    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 推断格式
    if format is None:
        format = output_path.suffix.lstrip(".").upper()
        if not format:
            format = "JPEG"

    # 保存参数
    save_kwargs = {}
    if format in ("JPEG", "JPG"):
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True

    # 保存图像
    image.save(output_path, format=format, **save_kwargs)
    logger.debug(
        "保存图像",
        path=str(output_path),
        format=format,
        size=image.size,
    )


def get_image_info(image: Image.Image) -> Dict[str, any]:
    """
    获取图像信息

    Args:
        image: PIL Image 对象

    Returns:
        图像信息字典
    """
    info = {
        "size": image.size,
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "format": image.format,
    }

    # 添加 EXIF 信息（如果有）
    if hasattr(image, "_getexif") and image._getexif():
        info["has_exif"] = True
    else:
        info["has_exif"] = False

    return info


# 导出主要接口
__all__ = [
    "load_image",
    "resize_image",
    "crop_image",
    "extract_exif",
    "get_gps_info",
    "save_image",
    "get_image_info",
]

