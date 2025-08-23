"""Tests for captcha recognition tool.

验证码识别工具的单元测试。
"""

import pytest
from unittest.mock import patch, MagicMock

from ocr_mcp.tools.captcha_tool import CaptchaRecognizeTool


class TestCaptchaRecognizeTool:
    """测试验证码识别工具。"""
    
    @pytest.fixture
    def captcha_tool(self, mock_ddddocr):
        """创建验证码识别工具实例。"""
        return CaptchaRecognizeTool()
    
    def test_tool_properties(self, captcha_tool):
        """测试工具基本属性。"""
        assert captcha_tool.name == "captcha_recognize"
        assert "识别验证码图片" in captcha_tool.description
        assert isinstance(captcha_tool.input_schema, dict)
        assert "image_data" in captcha_tool.input_schema["properties"]
    
    def test_input_schema_structure(self, captcha_tool):
        """测试输入参数schema结构。"""
        schema = captcha_tool.input_schema
        
        # 检查必需参数
        assert "image_data" in schema["required"]
        
        # 检查参数类型
        properties = schema["properties"]
        assert properties["image_data"]["type"] == "string"
        
        # 检查可选参数
        if "options" in properties:
            options_props = properties["options"]["properties"]
            assert "preprocess" in options_props
            assert "confidence_threshold" in options_props
    
    def test_validate_arguments_valid(self, captcha_tool, sample_base64_image):
        """测试有效参数验证。"""
        arguments = {
            "image_data": sample_base64_image,
            "options": {
                "preprocess": True,
                "confidence_threshold": 0.8
            }
        }
        
        # 不应该抛出异常
        captcha_tool.validate_arguments(arguments)
    
    def test_validate_arguments_missing_image_data(self, captcha_tool):
        """测试缺少image_data参数。"""
        arguments = {}
        
        with pytest.raises(ValueError, match="缺少必需参数: image_data"):
            captcha_tool.validate_arguments(arguments)
    
    def test_validate_arguments_empty_image_data(self, captcha_tool):
        """测试空的image_data参数。"""
        arguments = {"image_data": ""}
        
        with pytest.raises(ValueError, match="image_data必须是非空字符串"):
            captcha_tool.validate_arguments(arguments)
    
    def test_validate_arguments_invalid_options_type(self, captcha_tool, sample_base64_image):
        """测试无效的options参数类型。"""
        arguments = {
            "image_data": sample_base64_image,
            "options": "invalid_options"
        }
        
        with pytest.raises(ValueError, match="options必须是字典类型"):
            captcha_tool.validate_arguments(arguments)
    
    def test_validate_arguments_invalid_confidence_threshold(self, captcha_tool, sample_base64_image):
        """测试无效的置信度阈值。"""
        arguments = {
            "image_data": sample_base64_image,
            "options": {
                "confidence_threshold": 1.5  # 超出范围
            }
        }
        
        with pytest.raises(ValueError, match="confidence_threshold必须是0-1之间的数值"):
            captcha_tool.validate_arguments(arguments)
    
    @pytest.mark.asyncio
    async def test_execute_success(self, captcha_tool, captcha_base64_image):
        """测试成功执行验证码识别。"""
        arguments = {
            "image_data": captcha_base64_image,
            "options": {
                "preprocess": True,
                "confidence_threshold": 0.5
            }
        }
        
        result = await captcha_tool.execute(**arguments)
        
        assert isinstance(result, dict)
        assert "text" in result
        assert "result" in result
        assert "confidence" in result
        assert "processing_time" in result
        assert result["result"] == "TEST"  # 来自mock
        assert 0 <= result["confidence"] <= 1
        assert result["processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_execute_without_preprocess(self, captcha_tool, captcha_base64_image):
        """测试不进行预处理的验证码识别。"""
        arguments = {
            "image_data": captcha_base64_image,
            "options": {
                "preprocess": False
            }
        }
        
        result = await captcha_tool.execute(**arguments)
        
        assert isinstance(result, dict)
        assert result["result"] == "TEST"
        assert "preprocess_applied" in result
        assert result["preprocess_applied"] == []
    
    @pytest.mark.asyncio
    async def test_execute_invalid_image_data(self, captcha_tool, invalid_base64_image):
        """测试无效图像数据的处理。"""
        arguments = {
            "image_data": invalid_base64_image
        }
        
        with pytest.raises(ValueError, match="图像解码失败"):
            await captcha_tool.execute(**arguments)
    
    @pytest.mark.asyncio
    async def test_execute_ocr_engine_failure(self, captcha_tool, captcha_base64_image):
        """测试OCR引擎失败的情况。"""
        # 模拟OCR引擎失败
        with patch.object(captcha_tool._ocr_engine, 'classification', side_effect=Exception("OCR failed")):
            arguments = {"image_data": captcha_base64_image}
            
            with pytest.raises(RuntimeError, match="OCR识别失败"):
                await captcha_tool.execute(**arguments)
    
    @pytest.mark.asyncio
    async def test_execute_empty_ocr_result(self, captcha_tool, captcha_base64_image):
        """测试OCR返回空结果的情况。"""
        # 模拟OCR引擎返回空结果
        with patch.object(captcha_tool._ocr_engine, 'classification', return_value=""):
            arguments = {"image_data": captcha_base64_image}
            
            with pytest.raises(RuntimeError, match="OCR识别结果为空"):
                await captcha_tool.execute(**arguments)
    
    @pytest.mark.asyncio
    async def test_execute_low_confidence_warning(self, captcha_tool, captcha_base64_image):
        """测试低置信度警告。"""
        arguments = {
            "image_data": captcha_base64_image,
            "options": {
                "confidence_threshold": 0.95  # 很高的阈值
            }
        }
        
        with patch('ocr_mcp.tools.captcha_tool.logger') as mock_logger:
            result = await captcha_tool.execute(**arguments)
            
            # 应该记录警告日志
            mock_logger.warning.assert_called_once()
            assert "置信度" in str(mock_logger.warning.call_args)
    
    def test_estimate_confidence_empty_text(self, captcha_tool):
        """测试空文本的置信度估算。"""
        confidence = captcha_tool._estimate_confidence("")
        assert confidence == 0.0
    
    def test_estimate_confidence_alphanumeric(self, captcha_tool):
        """测试字母数字组合的置信度估算。"""
        confidence = captcha_tool._estimate_confidence("ABC123")
        assert 0.8 <= confidence <= 0.99
    
    def test_estimate_confidence_alpha_only(self, captcha_tool):
        """测试纯字母的置信度估算。"""
        confidence = captcha_tool._estimate_confidence("ABCDEF")
        assert 0.7 <= confidence <= 0.99
    
    def test_estimate_confidence_digits_only(self, captcha_tool):
        """测试纯数字的置信度估算。"""
        confidence = captcha_tool._estimate_confidence("123456")
        assert 0.6 <= confidence <= 0.99
    
    def test_estimate_confidence_short_text(self, captcha_tool):
        """测试短文本的置信度估算。"""
        confidence = captcha_tool._estimate_confidence("AB")
        assert 0.1 <= confidence <= 0.99
    
    def test_init_without_ddddocr(self):
        """测试在没有ddddocr库的情况下初始化。"""
        with patch('ocr_mcp.tools.captcha_tool.ddddocr', None):
            with pytest.raises(RuntimeError, match="ddddocr库未安装"):
                CaptchaRecognizeTool()
    
    def test_init_ddddocr_failure(self, mock_ddddocr):
        """测试ddddocr初始化失败的情况。"""
        # 模拟ddddocr初始化失败
        mock_ddddocr.DdddOcr.side_effect = Exception("Init failed")
        
        with pytest.raises(RuntimeError, match="OCR引擎初始化失败"):
            CaptchaRecognizeTool()