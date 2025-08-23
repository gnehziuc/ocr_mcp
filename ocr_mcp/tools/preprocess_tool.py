"""Image preprocessing tool implementation.

图像预处理工具，提供去噪、增强、尺寸调整等功能。
"""

import time
from typing import Any, Dict, List

from .base_tool import BaseTool
from ..utils.image_utils import (
    decode_base64_image,
    encode_image_to_base64,
    preprocess_image,
    validate_image_size
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ImagePreprocessTool(BaseTool):
    """图像预处理工具。
    
    提供图像去噪、增强、尺寸调整等预处理功能。
    """
    
    def __init__(self) -> None:
        """初始化图像预处理工具。"""
        super().__init__()
        
    @property
    def name(self) -> str:
        """工具名称。"""
        return "image_preprocess"
        
    @property
    def description(self) -> str:
        """工具描述。"""
        return "对图像进行预处理优化，包括去噪、对比度增强、锐化、尺寸调整等操作"
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        """输入参数schema。"""
        return {
            "type": "object",
            "properties": {
                "image_data": {
                    "type": "string",
                    "description": "Base64编码的图像数据"
                },
                "operations": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["denoise", "enhance", "resize"]
                    },
                    "description": "预处理操作列表，可选值: denoise(去噪), enhance(增强), resize(尺寸调整)",
                    "default": ["denoise", "enhance"]
                },
                "options": {
                    "type": "object",
                    "properties": {
                        "contrast": {
                            "type": "number",
                            "description": "对比度增强因子",
                            "default": 1.5,
                            "minimum": 0.1,
                            "maximum": 3.0
                        },
                        "sharpness": {
                            "type": "number",
                            "description": "锐化增强因子",
                            "default": 1.2,
                            "minimum": 0.1,
                            "maximum": 3.0
                        },
                        "max_width": {
                            "type": "integer",
                            "description": "最大宽度",
                            "default": 800,
                            "minimum": 100,
                            "maximum": 2000
                        },
                        "max_height": {
                            "type": "integer",
                            "description": "最大高度",
                            "default": 600,
                            "minimum": 100,
                            "maximum": 2000
                        },
                        "return_processed_image": {
                            "type": "boolean",
                            "description": "是否返回处理后的图像数据",
                            "default": False
                        }
                    },
                    "additionalProperties": False
                }
            },
            "required": ["image_data"],
            "additionalProperties": False
        }
        
    def validate_arguments(self, arguments: Dict[str, Any]) -> None:
        """验证输入参数。
        
        Args:
            arguments: 输入参数字典
            
        Raises:
            ValueError: 参数验证失败
        """
        if "image_data" not in arguments:
            raise ValueError("缺少必需参数: image_data")
            
        image_data = arguments["image_data"]
        if not isinstance(image_data, str) or not image_data.strip():
            raise ValueError("image_data必须是非空字符串")
            
        # 验证operations参数
        operations = arguments.get("operations", ["denoise", "enhance"])
        if not isinstance(operations, list):
            raise ValueError("operations必须是列表类型")
            
        valid_operations = {"denoise", "enhance", "resize"}
        for op in operations:
            if op not in valid_operations:
                raise ValueError(f"无效的预处理操作: {op}，支持的操作: {valid_operations}")
                
        # 验证options参数
        options = arguments.get("options", {})
        if not isinstance(options, dict):
            raise ValueError("options必须是字典类型")
            
        # 验证数值参数范围
        for param, (min_val, max_val) in [
            ("contrast", (0.1, 3.0)),
            ("sharpness", (0.1, 3.0)),
            ("max_width", (100, 2000)),
            ("max_height", (100, 2000))
        ]:
            if param in options:
                value = options[param]
                if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                    raise ValueError(f"{param}必须是{min_val}-{max_val}之间的数值")
    
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行图像预处理。
        
        Args:
            **kwargs: 工具参数
                - image_data: base64编码的图像数据
                - operations: 预处理操作列表
                - options: 可选参数字典
                
        Returns:
            预处理结果字典
            
        Raises:
            ValueError: 参数错误
            RuntimeError: 处理失败
        """
        start_time = time.time()
        
        try:
            # 验证参数
            self.validate_arguments(kwargs)
            
            image_data = kwargs["image_data"]
            operations = kwargs.get("operations", ["denoise", "enhance"])
            options = kwargs.get("options", {})
            
            logger.info(f"开始图像预处理，操作: {operations}")
            
            # 解码图像
            try:
                image = decode_base64_image(image_data)
                original_size = image.size
                logger.debug(f"原始图像尺寸: {original_size}")
            except Exception as e:
                raise ValueError(f"图像解码失败: {str(e)}") from e
                
            # 验证图像大小
            if not validate_image_size(image, max_size_mb=5.0):
                raise ValueError("图像文件过大，请确保小于5MB")
            
            # 准备预处理参数
            preprocess_kwargs = {
                "contrast": options.get("contrast", 1.5),
                "sharpness": options.get("sharpness", 1.2),
                "max_size": (
                    options.get("max_width", 800),
                    options.get("max_height", 600)
                )
            }
            
            # 执行图像预处理
            try:
                processed_image, applied_operations = preprocess_image(
                    image,
                    operations=operations,
                    **preprocess_kwargs
                )
                
                processed_size = processed_image.size
                logger.info(f"图像预处理完成: {applied_operations}")
                logger.debug(f"处理后图像尺寸: {processed_size}")
                
            except Exception as e:
                error_msg = f"图像预处理失败: {str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 构建返回结果
            result_text_parts = [
                "图像预处理完成",
                f"应用操作: {', '.join(applied_operations) if applied_operations else '无'}",
                f"原始尺寸: {original_size[0]}x{original_size[1]}",
                f"处理后尺寸: {processed_size[0]}x{processed_size[1]}",
                f"处理时间: {processing_time:.2f}秒"
            ]
            
            result = {
                "text": "\n".join(result_text_parts),
                "applied_operations": applied_operations,
                "original_size": original_size,
                "processed_size": processed_size,
                "processing_time": processing_time
            }
            
            # 如果需要返回处理后的图像数据
            if options.get("return_processed_image", False):
                try:
                    processed_image_data = encode_image_to_base64(processed_image)
                    result["processed_image_data"] = processed_image_data
                    logger.debug("已包含处理后的图像数据")
                except Exception as e:
                    logger.warning(f"编码处理后图像失败: {e}")
            
            logger.info(f"图像预处理完成，耗时: {processing_time:.2f}秒")
            return result
            
        except (ValueError, RuntimeError):
            # 重新抛出已知错误
            raise
        except Exception as e:
            # 捕获未知错误
            error_msg = f"图像预处理过程中发生未知错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
    
    def get_supported_operations(self) -> List[str]:
        """获取支持的预处理操作列表。
        
        Returns:
            支持的操作列表
        """
        return ["denoise", "enhance", "resize"]
    
    def get_operation_description(self, operation: str) -> str:
        """获取操作描述。
        
        Args:
            operation: 操作名称
            
        Returns:
            操作描述
        """
        descriptions = {
            "denoise": "图像去噪，使用中值滤波去除噪点",
            "enhance": "图像增强，提高对比度和锐化度",
            "resize": "尺寸调整，按比例缩放到指定最大尺寸"
        }
        return descriptions.get(operation, "未知操作")