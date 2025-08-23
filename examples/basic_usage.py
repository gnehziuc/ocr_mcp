#!/usr/bin/env python3
"""Basic usage example for OCR MCP system.

OCR MCP系统的基本使用示例。
"""

import asyncio
import base64
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """主函数演示OCR MCP系统的基本使用。"""
    print("🚀 OCR MCP系统基本使用示例")
    print("=" * 50)
    
    # 连接到OCR MCP服务器
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "ocr_mcp"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ 成功连接到OCR MCP服务器")
                
                # 初始化连接
                await session.initialize()
                print("✅ MCP会话初始化完成")
                
                # 获取可用工具列表
                tools_result = await session.list_tools()
                tools = [tool.name for tool in tools_result.tools]
                print(f"📋 可用工具: {', '.join(tools)}")
                print()
                
                # 示例1: 验证码识别
                await demo_captcha_recognition(session)
                print()
                
                # 示例2: 图像预处理
                await demo_image_preprocessing(session)
                print()
                
                print("🎉 所有示例执行完成！")
                
    except Exception as e:
        print(f"❌ 连接服务器失败: {e}")
        print("请确保OCR MCP服务器正在运行")
        return


async def demo_captcha_recognition(session: ClientSession):
    """演示验证码识别功能。"""
    print("🔍 示例1: 验证码识别")
    print("-" * 30)
    
    # 创建一个简单的测试图像
    test_image_data = create_test_image()
    
    try:
        # 调用验证码识别工具
        result = await session.call_tool(
            "captcha_recognize",
            {
                "image_data": test_image_data,
                "options": {
                    "preprocess": True,
                    "confidence_threshold": 0.5
                }
            }
        )
        
        print("✅ 验证码识别成功:")
        print(result.content[0].text)
        
    except Exception as e:
        print(f"❌ 验证码识别失败: {e}")


async def demo_image_preprocessing(session: ClientSession):
    """演示图像预处理功能。"""
    print("🖼️ 示例2: 图像预处理")
    print("-" * 30)
    
    # 创建一个测试图像
    test_image_data = create_test_image()
    
    try:
        # 调用图像预处理工具
        result = await session.call_tool(
            "image_preprocess",
            {
                "image_data": test_image_data,
                "operations": ["denoise", "enhance"],
                "options": {
                    "contrast": 1.5,
                    "sharpness": 1.2,
                    "return_processed_image": False
                }
            }
        )
        
        print("✅ 图像预处理成功:")
        print(result.content[0].text)
        
    except Exception as e:
        print(f"❌ 图像预处理失败: {e}")


def create_test_image() -> str:
    """创建一个简单的测试图像并返回base64编码。
    
    Returns:
        base64编码的图像字符串
    """
    try:
        from PIL import Image, ImageDraw
        import io
        
        # 创建一个简单的测试图像
        image = Image.new('RGB', (200, 80), color='white')
        draw = ImageDraw.Draw(image)
        
        # 绘制简单的文字（模拟验证码）
        draw.text((20, 20), "TEST", fill='black')
        
        # 转换为base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        return base64.b64encode(image_bytes).decode('utf-8')
        
    except ImportError:
        print("⚠️ PIL库未安装，使用空白图像数据")
        # 返回一个最小的PNG图像的base64编码
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="


if __name__ == "__main__":
    print("启动OCR MCP基本使用示例...")
    print("请确保OCR MCP服务器已安装并可用")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 示例已中断")
    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")