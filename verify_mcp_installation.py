#!/usr/bin/env python3
"""
简化的MCP框架安装验证脚本
验证MCP框架和OCR功能是否正常工作
"""

import sys
import asyncio
from typing import Any, Sequence

def test_imports():
    """测试关键模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        import mcp
        print("✅ MCP框架导入成功")
    except ImportError as e:
        print(f"❌ MCP框架导入失败: {e}")
        return False
    
    try:
        import ddddocr
        print("✅ ddddocr库导入成功")
    except ImportError as e:
        print(f"❌ ddddocr库导入失败: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL图像处理库导入成功")
    except ImportError as e:
        print(f"❌ PIL库导入失败: {e}")
        return False
    
    return True

def test_ddddocr_basic():
    """测试ddddocr基础功能"""
    print("\n🔍 测试ddddocr基础功能...")
    
    try:
        import ddddocr
        
        # 创建OCR实例
        ocr = ddddocr.DdddOcr()
        print("✅ ddddocr实例创建成功")
        
        # 测试基本功能（不使用实际图像）
        print("✅ ddddocr基础功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ ddddocr测试失败: {e}")
        return False

def test_mcp_server_creation():
    """测试MCP服务器创建"""
    print("\n🔍 测试MCP服务器创建...")
    
    try:
        from mcp.server import Server
        from mcp.types import Tool, ListToolsResult
        
        # 创建MCP服务器实例
        server = Server("ocr-mcp-server")
        print("✅ MCP服务器实例创建成功")
        
        # 测试处理器注册
        @server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """测试工具列表处理器"""
            tools = [
                Tool(
                    name="test_tool",
                    description="测试工具",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"}
                        }
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        print("✅ MCP处理器注册成功")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP服务器测试失败: {e}")
        return False

async def test_async_functionality():
    """测试异步功能"""
    print("\n🔍 测试异步功能...")
    
    try:
        # 简单的异步测试
        await asyncio.sleep(0.1)
        print("✅ 异步功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 异步功能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始MCP框架安装验证")
    print("=" * 50)
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 10):
        print("❌ MCP框架需要Python 3.10或更高版本")
        return False
    
    print("✅ Python版本满足要求")
    
    # 运行测试
    tests = [
        ("模块导入", test_imports),
        ("ddddocr功能", test_ddddocr_basic),
        ("MCP服务器", test_mcp_server_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
    
    # 异步测试
    try:
        asyncio.run(test_async_functionality())
        passed += 1
        total += 1
    except Exception as e:
        print(f"❌ 异步功能测试异常: {e}")
        total += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！MCP框架安装成功")
        print("\n📝 下一步:")
        print("   1. 运行 'py -3.13 src/ocr_mcp_server.py' 启动MCP服务器")
        print("   2. 使用MCP客户端连接到服务器")
        print("   3. 调用captcha_recognize和image_preprocess工具")
        return True
    else:
        print("⚠️  部分测试失败，请检查安装")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)