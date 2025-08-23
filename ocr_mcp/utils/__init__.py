"""OCR MCP Utils package.

包含日志、图像处理等通用工具函数。
"""

from .logger import setup_logger
from .image_utils import decode_base64_image, encode_image_to_base64

__all__ = ["setup_logger", "decode_base64_image", "encode_image_to_base64"]