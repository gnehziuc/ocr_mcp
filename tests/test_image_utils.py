"""Tests for image utilities.

图像处理工具的单元测试。
"""

import base64
import io
from unittest.mock import patch

import pytest
from PIL import Image

from ocr_mcp.utils.image_utils import (
    decode_base64_image,
    encode_image_to_base64,
    denoise_image,
    enhance_image,
    resize_image,
    preprocess_image,
    validate_image_size
)


class TestDecodeBase64Image:
    """测试base64图像解码功能。"""
    
    def test_decode_valid_base64_image(self, sample_base64_image):
        """测试解码有效的base64图像。"""
        image = decode_base64_image(sample_base64_image)
        assert isinstance(image, Image.Image)
        assert image.mode == 'RGB'
        assert image.size == (200, 100)
    
    def test_decode_base64_with_data_url_prefix(self, sample_base64_image):
        """测试解码带有数据URL前缀的base64图像。"""
        data_url = f"data:image/png;base64,{sample_base64_image}"
        image = decode_base64_image(data_url)
        assert isinstance(image, Image.Image)
        assert image.size == (200, 100)
    
    def test_decode_invalid_base64_image(self, invalid_base64_image):
        """测试解码无效的base64图像。"""
        with pytest.raises(ValueError, match="图像解码失败"):
            decode_base64_image(invalid_base64_image)
    
    def test_decode_empty_base64_image(self):
        """测试解码空的base64字符串。"""
        with pytest.raises(ValueError, match="图像解码失败"):
            decode_base64_image("")


class TestEncodeImageToBase64:
    """测试图像base64编码功能。"""
    
    def test_encode_image_to_base64_png(self, sample_image):
        """测试将图像编码为PNG格式的base64。"""
        base64_string = encode_image_to_base64(sample_image, format='PNG')
        assert isinstance(base64_string, str)
        assert len(base64_string) > 0
        
        # 验证可以解码回图像
        decoded_image = decode_base64_image(base64_string)
        assert decoded_image.size == sample_image.size
    
    def test_encode_image_to_base64_jpeg(self, sample_image):
        """测试将图像编码为JPEG格式的base64。"""
        base64_string = encode_image_to_base64(sample_image, format='JPEG')
        assert isinstance(base64_string, str)
        assert len(base64_string) > 0


class TestDenoiseImage:
    """测试图像去噪功能。"""
    
    def test_denoise_image_success(self, sample_image):
        """测试成功的图像去噪。"""
        denoised = denoise_image(sample_image)
        assert isinstance(denoised, Image.Image)
        assert denoised.size == sample_image.size
    
    @patch('ocr_mcp.utils.image_utils.logger')
    def test_denoise_image_failure(self, mock_logger, sample_image):
        """测试图像去噪失败的情况。"""
        with patch.object(sample_image, 'filter', side_effect=Exception("Filter error")):
            result = denoise_image(sample_image)
            assert result == sample_image  # 应该返回原图像
            mock_logger.warning.assert_called_once()


class TestEnhanceImage:
    """测试图像增强功能。"""
    
    def test_enhance_image_default_params(self, sample_image):
        """测试使用默认参数的图像增强。"""
        enhanced = enhance_image(sample_image)
        assert isinstance(enhanced, Image.Image)
        assert enhanced.size == sample_image.size
    
    def test_enhance_image_custom_params(self, sample_image):
        """测试使用自定义参数的图像增强。"""
        enhanced = enhance_image(sample_image, contrast=2.0, sharpness=1.5)
        assert isinstance(enhanced, Image.Image)
        assert enhanced.size == sample_image.size
    
    @patch('ocr_mcp.utils.image_utils.logger')
    def test_enhance_image_failure(self, mock_logger, sample_image):
        """测试图像增强失败的情况。"""
        with patch('PIL.ImageEnhance.Contrast', side_effect=Exception("Enhance error")):
            result = enhance_image(sample_image)
            assert result == sample_image  # 应该返回原图像
            mock_logger.warning.assert_called_once()


class TestResizeImage:
    """测试图像尺寸调整功能。"""
    
    def test_resize_large_image(self, large_image):
        """测试调整大图像尺寸。"""
        resized = resize_image(large_image, max_size=(800, 600))
        assert isinstance(resized, Image.Image)
        assert resized.size[0] <= 800
        assert resized.size[1] <= 600
    
    def test_resize_small_image_no_change(self, sample_image):
        """测试小图像不需要调整尺寸。"""
        original_size = sample_image.size
        resized = resize_image(sample_image, max_size=(800, 600))
        assert resized.size == original_size
    
    def test_resize_maintain_aspect_ratio(self):
        """测试调整尺寸时保持宽高比。"""
        # 创建一个宽高比为2:1的图像
        image = Image.new('RGB', (1000, 500), color='red')
        resized = resize_image(image, max_size=(400, 400))
        
        # 调整后应该保持2:1的宽高比
        assert resized.size == (400, 200)
    
    @patch('ocr_mcp.utils.image_utils.logger')
    def test_resize_image_failure(self, mock_logger, sample_image):
        """测试图像尺寸调整失败的情况。"""
        with patch.object(sample_image, 'resize', side_effect=Exception("Resize error")):
            result = resize_image(sample_image)
            assert result == sample_image  # 应该返回原图像
            mock_logger.warning.assert_called_once()


class TestPreprocessImage:
    """测试综合图像预处理功能。"""
    
    def test_preprocess_image_default_operations(self, sample_image):
        """测试使用默认操作的图像预处理。"""
        processed, operations = preprocess_image(sample_image)
        assert isinstance(processed, Image.Image)
        assert isinstance(operations, list)
        assert '去噪' in operations
        assert '增强' in operations
    
    def test_preprocess_image_custom_operations(self, large_image):
        """测试使用自定义操作的图像预处理。"""
        processed, operations = preprocess_image(
            large_image,
            operations=['denoise', 'enhance', 'resize'],
            max_size=(400, 300)
        )
        assert isinstance(processed, Image.Image)
        assert '去噪' in operations
        assert '增强' in operations
        assert '尺寸调整' in operations
        assert processed.size[0] <= 400
        assert processed.size[1] <= 300
    
    def test_preprocess_image_empty_operations(self, sample_image):
        """测试空操作列表的图像预处理。"""
        processed, operations = preprocess_image(sample_image, operations=[])
        assert processed.size == sample_image.size
        assert operations == []
    
    def test_preprocess_image_unknown_operation(self, sample_image):
        """测试未知操作的图像预处理。"""
        with patch('ocr_mcp.utils.image_utils.logger') as mock_logger:
            processed, operations = preprocess_image(
                sample_image,
                operations=['unknown_operation']
            )
            mock_logger.warning.assert_called_once()
    
    @patch('ocr_mcp.utils.image_utils.logger')
    def test_preprocess_image_failure(self, mock_logger, sample_image):
        """测试图像预处理失败的情况。"""
        with patch('ocr_mcp.utils.image_utils.denoise_image', side_effect=Exception("Process error")):
            processed, operations = preprocess_image(sample_image)
            assert processed == sample_image  # 应该返回原图像
            assert operations == []
            mock_logger.error.assert_called_once()


class TestValidateImageSize:
    """测试图像大小验证功能。"""
    
    def test_validate_small_image_size(self, sample_image):
        """测试验证小图像大小。"""
        is_valid = validate_image_size(sample_image, max_size_mb=5.0)
        assert is_valid is True
    
    def test_validate_large_image_size(self, large_image):
        """测试验证大图像大小。"""
        is_valid = validate_image_size(large_image, max_size_mb=0.1)  # 很小的限制
        assert is_valid is False
    
    @patch('ocr_mcp.utils.image_utils.logger')
    def test_validate_image_size_failure(self, mock_logger, sample_image):
        """测试图像大小验证失败的情况。"""
        with patch.object(sample_image, 'save', side_effect=Exception("Save error")):
            is_valid = validate_image_size(sample_image)
            assert is_valid is False
            mock_logger.error.assert_called_once()