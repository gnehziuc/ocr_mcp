"""OCR MCP Server implementation.

基于MCP 2024-11-05协议的轻量级OCR服务器，提供验证码识别和图像预处理功能。
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from .tools.captcha_tool import CaptchaRecognizeTool
from .tools.preprocess_tool import ImagePreprocessTool
from .utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)


class OCRMCPServer:
    """OCR MCP服务器主类。
    
    实现MCP协议规范，提供验证码识别和图像预处理工具。
    """
    
    def __init__(self) -> None:
        """初始化OCR MCP服务器。"""
        self.server = Server("ocr-mcp")
        self.tools: Dict[str, Any] = {}
        self._setup_tools()
        self._setup_handlers()
        
    def _setup_tools(self) -> None:
        """设置可用工具。"""
        # 初始化工具实例
        captcha_tool = CaptchaRecognizeTool()
        preprocess_tool = ImagePreprocessTool()
        
        # 注册工具
        self.tools[captcha_tool.name] = captcha_tool
        self.tools[preprocess_tool.name] = preprocess_tool
        
        logger.info(f"已注册 {len(self.tools)} 个工具: {list(self.tools.keys())}")
        
    def _setup_handlers(self) -> None:
        """设置MCP协议处理器。"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """处理工具列表请求。"""
            tools = []
            for tool in self.tools.values():
                tools.append(
                    Tool(
                        name=tool.name,
                        description=tool.description,
                        inputSchema=tool.input_schema,
                    )
                )
            
            logger.debug(f"返回工具列表: {[t.name for t in tools]}")
            return ListToolsResult(tools=tools)
            
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """处理工具调用请求。"""
            tool_name = request.params.name
            arguments = request.params.arguments or {}
            
            logger.info(f"调用工具: {tool_name}")
            logger.debug(f"工具参数: {arguments}")
            
            if tool_name not in self.tools:
                error_msg = f"未知工具: {tool_name}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            try:
                tool = self.tools[tool_name]
                result = await tool.execute(**arguments)
                
                # 格式化返回结果
                if isinstance(result, str):
                    content = [TextContent(type="text", text=result)]
                elif isinstance(result, dict) and "text" in result:
                    content = [TextContent(type="text", text=result["text"])]
                else:
                    content = [TextContent(type="text", text=str(result))]
                    
                logger.info(f"工具 {tool_name} 执行成功")
                return CallToolResult(content=content)
                
            except Exception as e:
                error_msg = f"工具 {tool_name} 执行失败: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise RuntimeError(error_msg) from e
                
    async def run(self) -> None:
        """启动MCP服务器。"""
        logger.info("启动OCR MCP服务器...")
        
        try:
            async with stdio_server() as (read_stream, write_stream):
                logger.info("MCP服务器已启动，等待客户端连接...")
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭服务器...")
        except Exception as e:
            logger.error(f"服务器运行错误: {e}", exc_info=True)
            raise
        finally:
            logger.info("OCR MCP服务器已关闭")


def main() -> None:
    """主入口函数。"""
    # 设置日志级别
    log_level = logging.INFO
    if "--debug" in sys.argv:
        log_level = logging.DEBUG
        
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)]
    )
    
    # 创建并运行服务器
    server = OCRMCPServer()
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()