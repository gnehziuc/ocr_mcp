#!/usr/bin/env python3
"""Claude integration example for OCR MCP system.

Claude集成示例，展示如何在Claude应用中使用OCR MCP系统。
"""

import asyncio
import base64
import json
from pathlib import Path
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ClaudeOCRIntegration:
    """Claude OCR集成类。
    
    提供与OCR MCP服务器的集成接口，方便在Claude应用中使用。
    """
    
    def __init__(self):
        """初始化Claude OCR集成。"""
        self.session: Optional[ClientSession] = None
        self.read_stream = None
        self.write_stream = None
        self.connected = False
    
    async def connect(self) -> bool:
        """连接到OCR MCP服务器。
        
        Returns:
            连接是否成功
        """
        try:
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "ocr_mcp"]
            )
            
            # 建立连接
            self.read_stream, self.write_stream = await stdio_client(server_params).__aenter__()
            self.session = await ClientSession(self.read_stream, self.write_stream).__aenter__()
            
            # 初始化会话
            await self.session.initialize()
            self.connected = True
            
            print("✅ 成功连接到OCR MCP服务器")
            return True
            
        except Exception as e:
            print(f"❌ 连接OCR服务器失败: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """断开与OCR MCP服务器的连接。"""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
            except Exception:
                pass
        
        if self.read_stream and self.write_stream:
            try:
                await stdio_client(None).__aexit__(None, None, None)
            except Exception:
                pass
        
        self.connected = False
        print("🔌 已断开OCR服务器连接")
    
    async def recognize_captcha_from_file(self, image_path: str, preprocess: bool = True) -> dict:
        """从文件识别验证码。
        
        Args:
            image_path: 图像文件路径
            preprocess: 是否进行预处理
            
        Returns:
            识别结果字典
        """
        if not self.connected:
            raise RuntimeError("未连接到OCR服务器")
        
        # 读取图像文件
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
        except Exception as e:
            raise ValueError(f"读取图像文件失败: {e}")
        
        return await self.recognize_captcha(image_data, preprocess)
    
    async def recognize_captcha(self, image_data: str, preprocess: bool = True) -> dict:
        """识别验证码。
        
        Args:
            image_data: base64编码的图像数据
            preprocess: 是否进行预处理
            
        Returns:
            识别结果字典
        """
        if not self.connected:
            raise RuntimeError("未连接到OCR服务器")
        
        try:
            result = await self.session.call_tool(
                "captcha_recognize",
                {
                    "image_data": image_data,
                    "options": {
                        "preprocess": preprocess,
                        "confidence_threshold": 0.7
                    }
                }
            )
            
            # 解析结果
            result_text = result.content[0].text
            
            # 提取关键信息
            lines = result_text.split('\n')
            extracted_text = ""
            confidence = 0.0
            processing_time = 0.0
            
            for line in lines:
                if line.startswith("识别结果: "):
                    extracted_text = line.replace("识别结果: ", "")
                elif line.startswith("置信度: "):
                    try:
                        confidence = float(line.replace("置信度: ", ""))
                    except ValueError:
                        pass
                elif line.startswith("处理时间: "):
                    try:
                        processing_time = float(line.replace("处理时间: ", "").replace("秒", ""))
                    except ValueError:
                        pass
            
            return {
                "success": True,
                "text": extracted_text,
                "confidence": confidence,
                "processing_time": processing_time,
                "raw_result": result_text
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "confidence": 0.0,
                "processing_time": 0.0
            }
    
    async def preprocess_image(self, image_data: str, operations: list = None) -> dict:
        """预处理图像。
        
        Args:
            image_data: base64编码的图像数据
            operations: 预处理操作列表
            
        Returns:
            预处理结果字典
        """
        if not self.connected:
            raise RuntimeError("未连接到OCR服务器")
        
        if operations is None:
            operations = ["denoise", "enhance"]
        
        try:
            result = await self.session.call_tool(
                "image_preprocess",
                {
                    "image_data": image_data,
                    "operations": operations,
                    "options": {
                        "contrast": 1.5,
                        "sharpness": 1.2,
                        "return_processed_image": True
                    }
                }
            )
            
            return {
                "success": True,
                "result": result.content[0].text
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_available_tools(self) -> list:
        """获取可用工具列表。
        
        Returns:
            工具名称列表
        """
        if not self.connected:
            raise RuntimeError("未连接到OCR服务器")
        
        try:
            tools_result = await self.session.list_tools()
            return [tool.name for tool in tools_result.tools]
        except Exception as e:
            print(f"获取工具列表失败: {e}")
            return []


async def demo_claude_integration():
    """演示Claude集成功能。"""
    print("🤖 Claude OCR集成示例")
    print("=" * 40)
    
    # 创建集成实例
    ocr_integration = ClaudeOCRIntegration()
    
    try:
        # 连接到服务器
        if not await ocr_integration.connect():
            return
        
        # 获取可用工具
        tools = await ocr_integration.get_available_tools()
        print(f"📋 可用工具: {', '.join(tools)}")
        print()
        
        # 创建测试图像
        test_image = create_test_captcha_image()
        
        # 示例1: 验证码识别
        print("🔍 验证码识别示例:")
        result = await ocr_integration.recognize_captcha(test_image)
        
        if result["success"]:
            print(f"✅ 识别成功: {result['text']}")
            print(f"📊 置信度: {result['confidence']:.2f}")
            print(f"⏱️ 处理时间: {result['processing_time']:.2f}秒")
        else:
            print(f"❌ 识别失败: {result['error']}")
        
        print()
        
        # 示例2: 图像预处理
        print("🖼️ 图像预处理示例:")
        preprocess_result = await ocr_integration.preprocess_image(
            test_image,
            operations=["denoise", "enhance"]
        )
        
        if preprocess_result["success"]:
            print("✅ 预处理成功")
            print(preprocess_result["result"])
        else:
            print(f"❌ 预处理失败: {preprocess_result['error']}")
        
    finally:
        # 断开连接
        await ocr_integration.disconnect()


def create_test_captcha_image() -> str:
    """创建测试验证码图像。
    
    Returns:
        base64编码的图像字符串
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # 创建验证码样式的图像
        image = Image.new('RGB', (120, 40), color='white')
        draw = ImageDraw.Draw(image)
        
        # 绘制验证码文字
        draw.text((10, 10), "A3B7", fill='black')
        
        # 添加一些噪点
        import random
        for _ in range(50):
            x = random.randint(0, 119)
            y = random.randint(0, 39)
            draw.point((x, y), fill='gray')
        
        # 转换为base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        return base64.b64encode(image_bytes).decode('utf-8')
        
    except ImportError:
        print("⚠️ PIL库未安装，使用简单测试图像")
        # 返回一个最小的PNG图像
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="


def generate_claude_config():
    """生成Claude Desktop配置文件示例。"""
    config = {
        "mcpServers": {
            "ocr-server": {
                "command": "python",
                "args": ["-m", "ocr_mcp"],
                "env": {
                    "OCR_LOG_LEVEL": "INFO"
                }
            }
        }
    }
    
    print("📝 Claude Desktop配置文件示例:")
    print("文件路径: ~/.config/claude-desktop/claude_desktop_config.json")
    print()
    print(json.dumps(config, indent=2, ensure_ascii=False))
    print()


async def main():
    """主函数。"""
    print("🚀 启动Claude OCR集成示例")
    print()
    
    # 生成配置文件示例
    generate_claude_config()
    
    # 运行集成示例
    await demo_claude_integration()
    
    print("\n🎉 Claude集成示例完成！")
    print("\n💡 使用提示:")
    print("1. 将配置添加到Claude Desktop配置文件")
    print("2. 重启Claude Desktop")
    print("3. 在Claude中使用OCR功能")


if __name__ == "__main__":
    print("Claude OCR集成示例")
    print("请确保OCR MCP服务器已安装并可用")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 示例已中断")
    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")