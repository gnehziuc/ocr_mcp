"""Pytest configuration and fixtures.

测试配置和通用测试夹具。
"""

import base64
import io
from typing import Generator

import pytest
from PIL import Image


@pytest.fixture
def sample_image() -> Image.Image:
    """创建测试用的样本图像。
    
    Returns:
        PIL Image对象
    """
    # 创建一个简单的测试图像
    image = Image.new('RGB', (200, 100), color='white')
    return image


@pytest.fixture
def sample_base64_image(sample_image: Image.Image) -> str:
    """创建base64编码的测试图像。
    
    Args:
        sample_image: 样本图像
        
    Returns:
        base64编码的图像字符串
    """
    buffer = io.BytesIO()
    sample_image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    return base64.b64encode(image_bytes).decode('utf-8')


@pytest.fixture
def captcha_image() -> Image.Image:
    """创建验证码样式的测试图像。
    
    Returns:
        验证码样式的PIL Image对象
    """
    from PIL import ImageDraw, ImageFont
    
    # 创建验证码图像
    image = Image.new('RGB', (120, 40), color='white')
    draw = ImageDraw.Draw(image)
    
    # 绘制简单的文字（模拟验证码）
    try:
        # 尝试使用默认字体
        draw.text((10, 10), "TEST", fill='black')
    except Exception:
        # 如果字体加载失败，使用简单绘制
        draw.rectangle([10, 10, 30, 30], fill='black')
        draw.rectangle([35, 10, 55, 30], fill='black')
        draw.rectangle([60, 10, 80, 30], fill='black')
        draw.rectangle([85, 10, 105, 30], fill='black')
    
    return image


@pytest.fixture
def captcha_base64_image(captcha_image: Image.Image) -> str:
    """创建base64编码的验证码测试图像。
    
    Args:
        captcha_image: 验证码图像
        
    Returns:
        base64编码的验证码图像字符串
    """
    buffer = io.BytesIO()
    captcha_image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    return base64.b64encode(image_bytes).decode('utf-8')


@pytest.fixture
def invalid_base64_image() -> str:
    """创建无效的base64图像数据。
    
    Returns:
        无效的base64字符串
    """
    return "invalid_base64_data"


@pytest.fixture
def large_image() -> Image.Image:
    """创建大尺寸测试图像。
    
    Returns:
        大尺寸的PIL Image对象
    """
    # 创建一个较大的图像用于测试尺寸限制
    return Image.new('RGB', (2000, 1500), color='blue')


@pytest.fixture
def mock_ddddocr(monkeypatch):
    """模拟ddddocr引擎。
    
    Args:
        monkeypatch: pytest的monkeypatch fixture
    """
    class MockDdddOcr:
        def __init__(self, show_ad=False):
            pass
            
        def classification(self, image_bytes: bytes) -> str:
            # 模拟OCR识别结果
            return "TEST"
    
    # 模拟ddddocr模块
    import sys
    from unittest.mock import MagicMock
    
    mock_ddddocr_module = MagicMock()
    mock_ddddocr_module.DdddOcr = MockDdddOcr
    
    monkeypatch.setitem(sys.modules, 'ddddocr', mock_ddddocr_module)
    
    return mock_ddddocr_module