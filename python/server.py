#!/usr/bin/env python3
"""
基于ddddocr的MCP验证码识别服务器

这是一个遵循MCP（Model Context Protocol）标准的验证码识别服务器，
使用ddddocr库提供高精度的图形验证码识别功能。
"""

import asyncio
import base64
import io
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)
from PIL import Image

# 修复ddddocr与新版本Pillow的兼容性问题
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

try:
    import ddddocr
except ImportError:
    logger.error("ddddocr库未安装，请运行: pip install ddddocr")
    sys.exit(1)


class CaptchaRecognitionServer:
    """验证码识别MCP服务器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化服务器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.ocr_engine = None
        self.server = Server("ddddocr-mcp-server")
        self._setup_handlers()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server": {
                "name": "ddddocr-mcp-server",
                "version": "1.0.0",
                "transport": "stdio"
            },
            "recognition": {
                "engine": "ddddocr",
                "max_image_size": 5242880,
                "supported_formats": ["png", "jpg", "jpeg", "bmp", "gif", "webp"],
                "timeout": 30
            },
            "logging": {
                "level": "INFO",
                "format": "json"
            }
        }
    
    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get("logging", {})
        log_level = log_config.get("level", "INFO")
        
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台输出
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        # 添加文件输出（如果配置了）
        log_file = log_config.get("file")
        if log_file:
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_file,
                level=log_level,
                rotation=log_config.get("max_size", "10MB"),
                retention=log_config.get("backup_count", 5),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
            )
    
    def _setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """列出可用的工具函数"""
            return [
                Tool(
                    name="recognize_captcha",
                    description="识别图形验证码，返回识别结果和置信度",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_data": {
                                "type": "string",
                                "description": "验证码图片数据（base64编码）"
                            },
                            "image_format": {
                                "type": "string",
                                "description": "图片数据格式，默认为base64",
                                "default": "base64"
                            }
                        },
                        "required": ["image_data"]
                    }
                ),
                Tool(
                    name="recognize_captcha_from_file",
                    description="从图片文件识别验证码，支持JPG、PNG、BMP、GIF、WEBP等常见格式",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "图片文件的完整路径"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="recognize_captcha_batch",
                    description="批量识别多个图片文件中的验证码",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "图片文件路径列表"
                            }
                        },
                        "required": ["file_paths"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用"""
            if name == "recognize_captcha":
                return await self._handle_recognize_captcha(arguments)
            elif name == "recognize_captcha_from_file":
                return await self._handle_recognize_captcha_from_file(arguments)
            elif name == "recognize_captcha_batch":
                return await self._handle_recognize_captcha_batch(arguments)
            else:
                raise ValueError(f"未知的工具: {name}")
    
    async def _handle_recognize_captcha(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理验证码识别请求"""
        try:
            start_time = time.time()
            
            # 获取参数
            image_data = arguments.get("image_data")
            image_format = arguments.get("image_format", "base64")
            
            if not image_data:
                raise ValueError("缺少image_data参数")
            
            # 初始化OCR引擎（延迟加载）
            if self.ocr_engine is None:
                self.ocr_engine = ddddocr.DdddOcr()
            
            # 处理图片数据
            if image_format == "base64":
                try:
                    # 移除可能的数据URL前缀
                    if image_data.startswith("data:image/"):
                        image_data = image_data.split(",", 1)[1]
                    
                    image_bytes = base64.b64decode(image_data)
                except Exception as e:
                    raise ValueError(f"base64解码失败: {e}")
            else:
                raise ValueError(f"不支持的图片格式: {image_format}")
            
            # 验证图片大小
            max_size = self.config.get("recognition", {}).get("max_image_size", 5242880)
            if len(image_bytes) > max_size:
                raise ValueError(f"图片大小超过限制 ({max_size} bytes)")
            
            # 验证图片格式
            try:
                with Image.open(io.BytesIO(image_bytes)) as img:
                    img_format = img.format.lower() if img.format else "unknown"
                    supported_formats = self.config.get("recognition", {}).get("supported_formats", [])
                    if img_format not in supported_formats:
                        logger.warning(f"图片格式 {img_format} 可能不被支持")
            except Exception as e:
                raise ValueError(f"无效的图片数据: {e}")
            
            # 执行OCR识别
            try:
                recognized_text = self.ocr_engine.classification(image_bytes)
            except Exception as e:
                logger.error(f"OCR识别失败: {e}")
                raise ValueError(f"验证码识别失败: {e}")
            
            processing_time = time.time() - start_time
            
            # 构建结果
            result = {
                "success": True,
                "text": recognized_text or "",
                "confidence": 0.95,  # ddddocr不提供置信度，使用固定值
                "processing_time": round(processing_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            

            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"验证码识别处理失败: {e}")
            error_result = {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "processing_time": 0.0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False, indent=2)
            )]
    
    def _read_image_file(self, file_path: str) -> bytes:
        """读取图片文件并返回字节数据"""
        try:
            # 检查文件是否存在
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            if not path.is_file():
                raise ValueError(f"路径不是文件: {file_path}")
            
            # 检查文件扩展名
            supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']
            if path.suffix.lower() not in supported_extensions:
                logger.warning(f"文件扩展名 {path.suffix} 可能不被支持")
            
            # 读取文件
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            
            # 验证图片大小
            max_size = self.config.get("recognition", {}).get("max_image_size", 5242880)
            if len(image_bytes) > max_size:
                raise ValueError(f"图片大小超过限制 ({max_size} bytes)")
            
            # 验证图片格式
            try:
                with Image.open(io.BytesIO(image_bytes)) as img:
                    img_format = img.format.lower() if img.format else "unknown"
                    supported_formats = self.config.get("recognition", {}).get("supported_formats", [])
                    if img_format not in supported_formats:
                        logger.warning(f"图片格式 {img_format} 可能不被支持")
            except Exception as e:
                raise ValueError(f"无效的图片文件: {e}")
            
            return image_bytes
            
        except Exception as e:
            logger.error(f"读取图片文件失败 {file_path}: {e}")
            raise
    
    async def _handle_recognize_captcha_from_file(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理从文件识别验证码的请求"""
        try:
            start_time = time.time()
            
            # 获取参数
            file_path = arguments.get("file_path")
            if not file_path:
                raise ValueError("缺少file_path参数")
            
            # 初始化OCR引擎（延迟加载）
            if self.ocr_engine is None:
                self.ocr_engine = ddddocr.DdddOcr()
            
            # 读取图片文件
            image_bytes = self._read_image_file(file_path)
            
            # 执行OCR识别
            try:
                recognized_text = self.ocr_engine.classification(image_bytes)
            except Exception as e:
                logger.error(f"OCR识别失败: {e}")
                raise ValueError(f"验证码识别失败: {e}")
            
            processing_time = time.time() - start_time
            
            # 构建结果
            result = {
                "success": True,
                "file_path": file_path,
                "text": recognized_text or "",
                "confidence": 0.95,  # ddddocr不提供置信度，使用固定值
                "processing_time": round(processing_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            

            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"文件验证码识别处理失败: {e}")
            error_result = {
                "success": False,
                "file_path": arguments.get("file_path", ""),
                "text": "",
                "confidence": 0.0,
                "processing_time": 0.0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False, indent=2)
            )]
    
    async def _handle_recognize_captcha_batch(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理批量验证码识别请求"""
        try:
            start_time = time.time()
            
            # 获取参数
            file_paths = arguments.get("file_paths")
            if not file_paths:
                raise ValueError("缺少file_paths参数")
            
            if not isinstance(file_paths, list):
                raise ValueError("file_paths必须是数组")
            
            if len(file_paths) == 0:
                raise ValueError("file_paths不能为空")
            
            # 限制批量处理数量
            max_batch_size = 10
            if len(file_paths) > max_batch_size:
                raise ValueError(f"批量处理文件数量不能超过 {max_batch_size} 个")
            
            # 初始化OCR引擎（延迟加载）
            if self.ocr_engine is None:
                self.ocr_engine = ddddocr.DdddOcr()
            
            results = []
            successful_count = 0
            failed_count = 0
            
            # 逐个处理文件
            for i, file_path in enumerate(file_paths):
                file_start_time = time.time()
                try:
                    # 读取图片文件
                    image_bytes = self._read_image_file(file_path)
                    
                    # 执行OCR识别
                    recognized_text = self.ocr_engine.classification(image_bytes)
                    
                    file_processing_time = time.time() - file_start_time
                    
                    # 单个文件结果
                    file_result = {
                        "success": True,
                        "file_path": file_path,
                        "text": recognized_text or "",
                        "confidence": 0.95,
                        "processing_time": round(file_processing_time, 3)
                    }
                    
                    results.append(file_result)
                    successful_count += 1
                    

                    
                except Exception as e:
                    file_processing_time = time.time() - file_start_time
                    logger.error(f"文件 {file_path} 识别失败: {e}")
                    
                    # 单个文件错误结果
                    file_result = {
                        "success": False,
                        "file_path": file_path,
                        "text": "",
                        "confidence": 0.0,
                        "processing_time": round(file_processing_time, 3),
                        "error": str(e)
                    }
                    
                    results.append(file_result)
                    failed_count += 1
            
            total_processing_time = time.time() - start_time
            
            # 构建批量结果
            batch_result = {
                "success": True,
                "total_files": len(file_paths),
                "successful_count": successful_count,
                "failed_count": failed_count,
                "results": results,
                "total_processing_time": round(total_processing_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            

            
            return [TextContent(
                type="text",
                text=json.dumps(batch_result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"批量验证码识别处理失败: {e}")
            error_result = {
                "success": False,
                "total_files": len(arguments.get("file_paths", [])),
                "successful_count": 0,
                "failed_count": 0,
                "results": [],
                "total_processing_time": 0.0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False, indent=2)
            )]
    
    async def run_stdio(self):
        """运行stdio传输模式"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ddddocr-mcp-server",
                    server_version="1.0.0",
                    capabilities={}
                )
            )
    
    async def run_sse(self, host: str = "localhost", port: int = 8080):
        """运行SSE传输模式（暂不支持）"""
        logger.error("SSE模式暂不支持，请使用stdio模式")
        raise NotImplementedError("SSE模式暂不支持")


async def main():
    """主函数"""
    # 创建服务器实例
    server = CaptchaRecognitionServer()
    
    # 根据配置选择传输方式
    transport = server.config.get("server", {}).get("transport", "stdio")
    
    try:
        if transport == "stdio":
            await server.run_stdio()
        elif transport == "sse":
            host = server.config.get("server", {}).get("host", "localhost")
            port = server.config.get("server", {}).get("port", 8080)
            await server.run_sse(host, port)
        else:
            logger.error(f"不支持的传输方式: {transport}")
            sys.exit(1)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"服务器运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())