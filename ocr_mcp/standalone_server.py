"""独立OCR服务器实现。

不依赖MCP框架的轻量级OCR服务器，提供HTTP API接口。
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse
from io import BytesIO

from .tools.captcha_tool import CaptchaRecognizeTool
from .tools.preprocess_tool import ImagePreprocessTool
from .utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name