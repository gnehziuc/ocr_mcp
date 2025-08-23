"""Captcha recognition tool implementation.

基于ddddocr引擎的验证码识别工具。
"""

import time
from typing import Any, Dict, Optional

# 修复Pillow 10.x与ddddocr的兼容性问题
try:
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        setattr(Image, 'ANTIALIAS', Image.LANCZOS)
except ImportError:
    pass

try:
    import ddddocr
except ImportError:
    ddddocr = None

from .base_tool import BaseTool
from ..utils.image_utils import decode_base64_image, preprocess_image, validate_image_size
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CaptchaRecognizeTool(BaseTool):
    """验证码识别工具。
    
    使用ddddocr引擎识别各种类型的验证码图片。
    """
    
    def __init__(self) -> None:
        """初始化验证码识别工具。"""
        super().__init__()
        self._ocr_engine: Optional[Any] = None
        self._init_ocr_engine()
        
    def _init_ocr_engine(self) -> None:
        """初始化OCR引擎。"""
        if ddddocr is None:
            raise RuntimeError("ddddocr库未安装，请运行: pip install ddddocr==1.5.6")
            
        try:
            self._ocr_engine = ddddocr.DdddOcr()
            logger.info("ddddocr引擎初始化成功")
        except Exception as e:
            logger.error(f"ddddocr引擎初始化失败: {e}")
            raise RuntimeError(f"OCR引擎初始化失败: {e}") from e
    
    @property
    def name(self) -> str:
        """工具名称。"""
        return "captcha_recognize"
        
    @property
    def description(self) -> str:
        """工具描述。"""
        return "识别验证码图片中的文字内容，基于ddddocr引擎提供高精度识别"
        
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
                "options": {
                    "type": "object",
                    "properties": {
                        "preprocess": {
                            "type": "boolean",
                            "description": "是否进行图像预处理",
                            "default": True
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "description": "置信度阈值(0-1)",
                            "default": 0.8,
                            "minimum": 0,
                            "maximum": 1
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
            
        # 验证options参数
        options = arguments.get("options", {})
        if not isinstance(options, dict):
            raise ValueError("options必须是字典类型")
            
        # 验证置信度阈值
        confidence_threshold = options.get("confidence_threshold", 0.8)
        if not isinstance(confidence_threshold, (int, float)) or not (0 <= confidence_threshold <= 1):
            raise ValueError("confidence_threshold必须是0-1之间的数值")
    
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行验证码识别。
        
        Args:
            **kwargs: 工具参数
                - image_data: base64编码的图像数据
                - options: 可选参数字典
                
        Returns:
            识别结果字典
            
        Raises:
            ValueError: 参数错误
            RuntimeError: 识别失败
        """
        start_time = time.time()
        
        try:
            # 验证参数
            self.validate_arguments(kwargs)
            
            image_data = kwargs["image_data"]
            options = kwargs.get("options", {})
            preprocess = options.get("preprocess", True)
            confidence_threshold = options.get("confidence_threshold", 0.8)
            
            logger.info(f"开始验证码识别，预处理: {preprocess}")
            
            # 解码图像
            try:
                image = decode_base64_image(image_data)
            except Exception as e:
                raise ValueError(f"图像解码失败: {str(e)}") from e
                
            # 验证图像大小
            if not validate_image_size(image, max_size_mb=5.0):
                raise ValueError("图像文件过大，请确保小于5MB")
                
            # 图像预处理
            processed_image = image
            applied_operations = []
            
            if preprocess:
                try:
                    processed_image, applied_operations = preprocess_image(
                        image,
                        operations=['denoise', 'enhance']
                    )
                    logger.debug(f"图像预处理完成: {applied_operations}")
                except Exception as e:
                    logger.warning(f"图像预处理失败: {e}，使用原图像")
                    processed_image = image
                    applied_operations = []
            
            # 执行OCR识别
            try:
                # 将PIL Image转换为bytes
                import io
                img_byte_arr = io.BytesIO()
                processed_image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                # 使用ddddocr进行识别
                result_text = self._ocr_engine.classification(img_bytes)
                
                if not result_text or not result_text.strip():
                    raise RuntimeError("OCR识别结果为空")
                    
                result_text = result_text.strip()
                logger.info(f"OCR识别成功: {result_text}")
                
            except Exception as e:
                error_msg = f"OCR识别失败: {str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 简单的置信度估算（基于结果长度和字符类型）
            confidence = self._estimate_confidence(result_text)
            
            # 检查置信度阈值
            if confidence < confidence_threshold:
                logger.warning(f"识别置信度 {confidence:.2f} 低于阈值 {confidence_threshold}")
            
            # 构建返回结果
            result = {
                "text": f"识别结果: {result_text}\n置信度: {confidence:.2f}\n处理时间: {processing_time:.2f}秒",
                "result": result_text,
                "confidence": confidence,
                "processing_time": processing_time,
                "preprocess_applied": applied_operations
            }
            
            logger.info(f"验证码识别完成，耗时: {processing_time:.2f}秒")
            return result
            
        except (ValueError, RuntimeError):
            # 重新抛出已知错误
            raise
        except Exception as e:
            # 捕获未知错误
            error_msg = f"验证码识别过程中发生未知错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
    
    def _estimate_confidence(self, text: str) -> float:
        """估算识别置信度。
        
        Args:
            text: 识别结果文本
            
        Returns:
            估算的置信度值(0-1)
        """
        if not text:
            return 0.0
            
        # 基础置信度
        base_confidence = 0.7
        
        # 根据文本长度调整
        length_factor = min(len(text) / 6.0, 1.0)  # 假设理想长度为6
        
        # 根据字符类型调整
        char_type_factor = 0.0
        if text.isalnum():  # 字母数字组合
            char_type_factor = 0.2
        elif text.isalpha():  # 纯字母
            char_type_factor = 0.15
        elif text.isdigit():  # 纯数字
            char_type_factor = 0.1
        
        # 计算最终置信度
        confidence = base_confidence + (length_factor * 0.2) + char_type_factor
        
        # 确保在合理范围内
        return min(max(confidence, 0.1), 0.99)