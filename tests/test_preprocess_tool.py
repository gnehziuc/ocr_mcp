"""Tests for image preprocessing tool.

图像预处理工具的单元测试。
"""

import pytest
from unittest.mock import patch

from ocr_mcp.tools.preprocess_tool import ImagePreprocessTool


class TestImagePreprocessTool:
    """测试图像预处理工具。"""
    
    @pytest.fixture
    def preprocess_tool(self):
        """创建图像预处理工具实例。"""
        return ImagePreprocessTool()
    
    def test_tool_properties(self, preprocess_tool):
        """测试工具基本属性。"""
        assert preprocess_tool.name == "image_preprocess"
        assert "图像进行预处理优化" in preprocess_tool.description
        assert isinstance(preprocess_tool.input_schema, dict)
        assert "image_data" in preprocess_tool.input_schema["properties"]
    
    def test_input_schema_structure(self, preprocess_tool):
        """测试输入参数schema结构。"""
        schema = preprocess_tool.input_schema
        
        # 检查必需参数
        assert "image_data" in schema["required"]
        
        # 检查参数类型
        properties = schema["properties"]
        assert properties["image_data"]["type"] == "string"
        
        # 检查operations参数
        if "operations" in properties:
            operations_schema = properties["operations"]
            assert operations_schema["type"] == "array"
            assert "enum" in operations_schema["items"]
            valid_ops = operations_schema["items"]["enum"]
            assert "denoise" in valid_ops
            assert "enhance" in valid_ops
            assert "resize" in valid_ops
    
    def test_validate_arguments_valid(self, preprocess_tool, sample_base64_image):
        """测试有效参数验证。"""
        arguments = {
            "image_data": sample_base64_image,
            "operations": ["denoise", "enhance"],
            "options": {
                "contrast": 1.5,
                "sharpness": 1.2,
                "max_width": 800,
                "max_height": 600
            }
        }
        
        # 不应该抛出异常
        preprocess_tool.validate_arguments(arguments)
    
    def test_validate_arguments_missing_image_data(self, preprocess_tool):
        """测试缺少image_data参数。"""
        arguments = {}
        
        with pytest.raises(ValueError, match="缺少必需参数: image_data"):
            preprocess_tool.validate_arguments(arguments)
    
    def test_validate_arguments_empty_image_data(self, preprocess_tool):
        """测试空的image_data参数。"""
        arguments = {"image_data": ""}
        
        with pytest.raises(ValueError, match="image_data必须是非空字符串"):
            preprocess_tool.validate_arguments(arguments)
    
    def test_validate_arguments_invalid_operations_type(self, preprocess_tool, sample_base64_image):
        """测试无效的operations参数类型。"""
        arguments = {
            "image_data": sample_base64_image,
            "operations": "invalid_operations"
        }
        
        with pytest.raises(ValueError, match="operations必须是列表类型"):
            preprocess_tool.validate_arguments(arguments)
    
    def test_validate_arguments_invalid_operation(self, preprocess_tool, sample_base64_image):
        """测试无效的预处理操作。"""
        arguments = {
            "image_data": sample_base64_image,
            "operations": ["invalid_operation"]
        }
        
        with pytest.raises(ValueError, match="无效的预处理操作"):
            preprocess_tool.validate_arguments(arguments)
    
    def test_validate_arguments_invalid_options_type(self, preprocess_tool, sample_base64_image):
        """测试无效的options参数类型。"""
        arguments = {
            "image_data": sample_base64_image,
            "options": "invalid_options"
        }
        
        with pytest.raises(ValueError, match="options必须是字典类型"):
            preprocess_tool.validate_arguments(arguments)
    
    def test_validate_arguments_invalid_contrast_range(self, preprocess_tool, sample_base64_image):
        """测试无效的对比度范围。"""
        arguments = {
            "image_data": sample_base64_image,
            "options": {
                "contrast": 5.0  # 超出范围
            }
        }
        
        with pytest.raises(ValueError, match="contrast必须是0.1-3.0之间的数值"):
            preprocess_tool.validate_arguments(arguments)
    
    def test_validate_arguments_invalid_max_width_range(self, preprocess_tool, sample_base64_image):
        """测试无效的最大宽度范围。"""
        arguments = {
            "image_data": sample_base64_image,
            "options": {
                "max_width": 50  # 小于最小值
            }
        }
        
        with pytest.raises(ValueError, match="max_width必须是100-2000之间的数值"):
            preprocess_tool.validate_arguments(arguments)
    
    @pytest.mark.asyncio
    async def test_execute_success_default_operations(self, preprocess_tool, sample_base64_image):
        """测试使用默认操作成功执行预处理。"""
        arguments = {
            "image_data": sample_base64_image
        }
        
        result = await preprocess_tool.execute(**arguments)
        
        assert isinstance(result, dict)
        assert "text" in result
        assert "applied_operations" in result
        assert "original_size" in result
        assert "processed_size" in result
        assert "processing_time" in result
        assert result["processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_execute_success_custom_operations(self, preprocess_tool, large_image):
        """测试使用自定义操作成功执行预处理。"""
        # 先将large_image编码为base64
        from ocr_mcp.utils.image_utils import encode_image_to_base64
        large_base64 = encode_image_to_base64(large_image)
        
        arguments = {
            "image_data": large_base64,
            "operations": ["denoise", "enhance", "resize"],
            "options": {
                "contrast": 2.0,
                "sharpness": 1.5,
                "max_width": 400,
                "max_height": 300
            }
        }
        
        result = await preprocess_tool.execute(**arguments)
        
        assert isinstance(result, dict)
        assert "去噪" in result["applied_operations"]
        assert "增强" in result["applied_operations"]
        assert "尺寸调整" in result["applied_operations"]
        
        # 检查尺寸是否被正确调整
        processed_size = result["processed_size"]
        assert processed_size[0] <= 400
        assert processed_size[1] <= 300
    
    @pytest.mark.asyncio
    async def test_execute_empty_operations(self, preprocess_tool, sample_base64_image):
        """测试空操作列表的预处理。"""
        arguments = {
            "image_data": sample_base64_image,
            "operations": []
        }
        
        result = await preprocess_tool.execute(**arguments)
        
        assert isinstance(result, dict)
        assert result["applied_operations"] == []
        # 原始尺寸和处理后尺寸应该相同
        assert result["original_size"] == result["processed_size"]
    
    @pytest.mark.asyncio
    async def test_execute_with_return_processed_image(self, preprocess_tool, sample_base64_image):
        """测试返回处理后图像数据的预处理。"""
        arguments = {
            "image_data": sample_base64_image,
            "options": {
                "return_processed_image": True
            }
        }
        
        result = await preprocess_tool.execute(**arguments)
        
        assert isinstance(result, dict)
        assert "processed_image_data" in result
        assert isinstance(result["processed_image_data"], str)
        assert len(result["processed_image_data"]) > 0
    
    @pytest.mark.asyncio
    async def test_execute_invalid_image_data(self, preprocess_tool, invalid_base64_image):
        """测试无效图像数据的处理。"""
        arguments = {
            "image_data": invalid_base64_image
        }
        
        with pytest.raises(ValueError, match="图像解码失败"):
            await preprocess_tool.execute(**arguments)
    
    @pytest.mark.asyncio
    async def test_execute_preprocess_failure(self, preprocess_tool, sample_base64_image):
        """测试预处理失败的情况。"""
        with patch('ocr_mcp.utils.image_utils.preprocess_image', side_effect=Exception("Preprocess failed")):
            arguments = {"image_data": sample_base64_image}
            
            with pytest.raises(RuntimeError, match="图像预处理失败"):
                await preprocess_tool.execute(**arguments)
    
    @pytest.mark.asyncio
    async def test_execute_encode_failure_warning(self, preprocess_tool, sample_base64_image):
        """测试编码处理后图像失败的警告。"""
        arguments = {
            "image_data": sample_base64_image,
            "options": {
                "return_processed_image": True
            }
        }
        
        with patch('ocr_mcp.utils.image_utils.encode_image_to_base64', side_effect=Exception("Encode failed")):
            with patch('ocr_mcp.tools.preprocess_tool.logger') as mock_logger:
                result = await preprocess_tool.execute(**arguments)
                
                # 应该记录警告日志
                mock_logger.warning.assert_called_once()
                assert "编码处理后图像失败" in str(mock_logger.warning.call_args)
                
                # 结果中不应该包含processed_image_data
                assert "processed_image_data" not in result
    
    def test_get_supported_operations(self, preprocess_tool):
        """测试获取支持的操作列表。"""
        operations = preprocess_tool.get_supported_operations()
        assert isinstance(operations, list)
        assert "denoise" in operations
        assert "enhance" in operations
        assert "resize" in operations
    
    def test_get_operation_description(self, preprocess_tool):
        """测试获取操作描述。"""
        # 测试已知操作
        desc_denoise = preprocess_tool.get_operation_description("denoise")
        assert "去噪" in desc_denoise
        
        desc_enhance = preprocess_tool.get_operation_description("enhance")
        assert "增强" in desc_enhance
        
        desc_resize = preprocess_tool.get_operation_description("resize")
        assert "尺寸" in desc_resize
        
        # 测试未知操作
        desc_unknown = preprocess_tool.get_operation_description("unknown")
        assert desc_unknown == "未知操作"