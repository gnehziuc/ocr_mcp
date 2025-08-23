"""Image processing utilities for OCR MCP server.

提供图像编解码、预处理等通用功能。
"""

import base64
import io
from typing import Tuple, Optional

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

from .logger import get_logger

logger = get_logger(__name__)


def decode_base64_image(base64_data: str) -> Image.Image:
    """解码base64图像数据。
    
    Args:
        base64_data: base64编码的图像数据
        
    Returns:
        PIL Image对象
        
    Raises:
        ValueError: 图像数据无效
    """
    try:
        # 移除可能的数据URL前缀
        if ',' in base64_data:
            base64_data = base64_data.split(',', 1)[1]
            
        # 解码base64数据
        image_bytes = base64.b64decode(base64_data)
        
        # 创建PIL Image对象
        image = Image.open(io.BytesIO(image_bytes))
        
        # 确保图像模式为RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        logger.debug(f"成功解码图像，尺寸: {image.size}, 模式: {image.mode}")
        return image
        
    except Exception as e:
        error_msg = f"图像解码失败: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e


def encode_image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """将PIL Image编码为base64字符串。
    
    Args:
        image: PIL Image对象
        format: 图像格式 (PNG, JPEG等)
        
    Returns:
        base64编码的图像字符串
        
    Raises:
        ValueError: 编码失败
    """
    try:
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        image_bytes = buffer.getvalue()
        
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        logger.debug(f"成功编码图像为base64，格式: {format}")
        
        return base64_string
        
    except Exception as e:
        error_msg = f"图像编码失败: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e


def denoise_image(image: Image.Image) -> Image.Image:
    """图像去噪处理。
    
    Args:
        image: 输入图像
        
    Returns:
        去噪后的图像
    """
    try:
        # 使用中值滤波去噪
        denoised = image.filter(ImageFilter.MedianFilter(size=3))
        logger.debug("图像去噪处理完成")
        return denoised
        
    except Exception as e:
        logger.warning(f"图像去噪失败: {e}，返回原图像")
        return image


def enhance_image(image: Image.Image, contrast: float = 1.5, sharpness: float = 1.2) -> Image.Image:
    """图像增强处理。
    
    Args:
        image: 输入图像
        contrast: 对比度增强因子
        sharpness: 锐化增强因子
        
    Returns:
        增强后的图像
    """
    try:
        # 对比度增强
        contrast_enhancer = ImageEnhance.Contrast(image)
        enhanced = contrast_enhancer.enhance(contrast)
        
        # 锐化增强
        sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
        enhanced = sharpness_enhancer.enhance(sharpness)
        
        logger.debug(f"图像增强完成，对比度: {contrast}, 锐化: {sharpness}")
        return enhanced
        
    except Exception as e:
        logger.warning(f"图像增强失败: {e}，返回原图像")
        return image


def resize_image(image: Image.Image, max_size: Tuple[int, int] = (800, 600)) -> Image.Image:
    """调整图像尺寸。
    
    Args:
        image: 输入图像
        max_size: 最大尺寸 (width, height)
        
    Returns:
        调整尺寸后的图像
    """
    try:
        original_size = image.size
        
        # 如果图像已经小于最大尺寸，直接返回
        if original_size[0] <= max_size[0] and original_size[1] <= max_size[1]:
            return image
            
        # 计算缩放比例，保持宽高比
        ratio = min(max_size[0] / original_size[0], max_size[1] / original_size[1])
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
        
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        logger.debug(f"图像尺寸调整: {original_size} -> {new_size}")
        
        return resized
        
    except Exception as e:
        logger.warning(f"图像尺寸调整失败: {e}，返回原图像")
        return image


def preprocess_image(
    image: Image.Image,
    operations: list = None,
    **kwargs
) -> Tuple[Image.Image, list]:
    """综合图像预处理。
    
    Args:
        image: 输入图像
        operations: 预处理操作列表 ['denoise', 'enhance', 'resize']
        **kwargs: 其他参数
        
    Returns:
        (处理后的图像, 应用的操作列表)
    """
    if operations is None:
        operations = ['denoise', 'enhance']
        
    processed_image = image.copy()
    applied_operations = []
    
    try:
        for operation in operations:
            if operation == 'denoise':
                processed_image = denoise_image(processed_image)
                applied_operations.append('去噪')
                
            elif operation == 'enhance':
                contrast = kwargs.get('contrast', 1.5)
                sharpness = kwargs.get('sharpness', 1.2)
                processed_image = enhance_image(processed_image, contrast, sharpness)
                applied_operations.append('增强')
                
            elif operation == 'resize':
                max_size = kwargs.get('max_size', (800, 600))
                processed_image = resize_image(processed_image, max_size)
                applied_operations.append('尺寸调整')
                
            else:
                logger.warning(f"未知的预处理操作: {operation}")
                
        logger.info(f"图像预处理完成，应用操作: {applied_operations}")
        return processed_image, applied_operations
        
    except Exception as e:
        logger.error(f"图像预处理失败: {e}")
        return image, []


def validate_image_size(image: Image.Image, max_size_mb: float = 5.0) -> bool:
    """验证图像大小。
    
    Args:
        image: PIL Image对象
        max_size_mb: 最大文件大小(MB)
        
    Returns:
        是否符合大小限制
    """
    try:
        # 估算图像大小
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        size_bytes = len(buffer.getvalue())
        size_mb = size_bytes / (1024 * 1024)
        
        is_valid = size_mb <= max_size_mb
        logger.debug(f"图像大小验证: {size_mb:.2f}MB, 限制: {max_size_mb}MB, 有效: {is_valid}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"图像大小验证失败: {e}")
        return False