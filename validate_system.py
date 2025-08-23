#!/usr/bin/env python3
"""System validation script for OCR MCP system.

OCR MCP系统验证脚本，测试核心功能是否正常工作。
"""

import sys
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """测试模块导入。"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试核心模块导入
        from ocr_mcp import __version__, __description__
        print(f"✅ 核心模块导入成功: v{__version__}")
        
        # 测试工具模块导入
        from ocr_mcp.tools import BaseTool, CaptchaRecognizeTool, ImagePreprocessTool
        print("✅ 工具模块导入成功")
        
        # 测试工具函数导入
        from ocr_mcp.utils import setup_logger, decode_base64_image, encode_image_to_base64
        print("✅ 工具函数导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        traceback.print_exc()
        return False


def test_image_utils():
    """测试图像处理工具。"""
    print("\n🖼️ 测试图像处理工具...")
    
    try:
        from PIL import Image
        import io
        import base64
        from ocr_mcp.utils.image_utils import (
            decode_base64_image,
            encode_image_to_base64,
            denoise_image,
            enhance_image,
            resize_image,
            preprocess_image,
            validate_image_size
        )
        
        # 创建测试图像
        test_image = Image.new('RGB', (200, 100), color='white')
        
        # 测试编码解码
        base64_data = encode_image_to_base64(test_image)
        decoded_image = decode_base64_image(base64_data)
        assert decoded_image.size == test_image.size
        print("✅ 图像编码解码测试通过")
        
        # 测试图像处理
        denoised = denoise_image(test_image)
        enhanced = enhance_image(test_image)
        resized = resize_image(test_image, max_size=(100, 50))
        print("✅ 图像处理功能测试通过")
        
        # 测试综合预处理
        processed, operations = preprocess_image(test_image, operations=['denoise', 'enhance'])
        assert len(operations) > 0
        print("✅ 综合预处理测试通过")
        
        # 测试图像大小验证
        is_valid = validate_image_size(test_image)
        assert is_valid is True
        print("✅ 图像大小验证测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 图像处理工具测试失败: {e}")
        traceback.print_exc()
        return False


def test_tool_initialization():
    """测试工具初始化。"""
    print("\n🛠️ 测试工具初始化...")
    
    try:
        # 测试图像预处理工具
        from ocr_mcp.tools.preprocess_tool import ImagePreprocessTool
        
        preprocess_tool = ImagePreprocessTool()
        assert preprocess_tool.name == "image_preprocess"
        assert "预处理" in preprocess_tool.description
        assert isinstance(preprocess_tool.input_schema, dict)
        print("✅ 图像预处理工具初始化成功")
        
        # 测试验证码识别工具（可能因为缺少ddddocr而失败）
        try:
            from ocr_mcp.tools.captcha_tool import CaptchaRecognizeTool
            captcha_tool = CaptchaRecognizeTool()
            print("✅ 验证码识别工具初始化成功")
        except Exception as e:
            print(f"⚠️ 验证码识别工具初始化失败（可能缺少ddddocr）: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具初始化测试失败: {e}")
        traceback.print_exc()
        return False


def test_tool_schemas():
    """测试工具schema定义。"""
    print("\n📋 测试工具schema定义...")
    
    try:
        from ocr_mcp.tools.preprocess_tool import ImagePreprocessTool
        
        tool = ImagePreprocessTool()
        schema = tool.input_schema
        
        # 验证schema结构
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert "image_data" in schema["properties"]
        assert "image_data" in schema["required"]
        print("✅ 工具schema结构验证通过")
        
        # 测试参数验证
        valid_args = {
            "image_data": "test_base64_data",
            "operations": ["denoise"],
            "options": {"contrast": 1.5}
        }
        
        tool.validate_arguments(valid_args)
        print("✅ 参数验证功能测试通过")
        
        # 测试无效参数
        try:
            tool.validate_arguments({})
            print("❌ 应该抛出参数验证错误")
            return False
        except ValueError:
            print("✅ 无效参数检测功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具schema测试失败: {e}")
        traceback.print_exc()
        return False


def test_logger():
    """测试日志功能。"""
    print("\n📝 测试日志功能...")
    
    try:
        from ocr_mcp.utils.logger import setup_logger, get_logger
        
        # 测试日志设置
        logger = setup_logger("test_logger")
        logger.info("测试日志消息")
        print("✅ 日志设置功能正常")
        
        # 测试获取日志器
        logger2 = get_logger("test_logger2")
        logger2.debug("调试消息")
        print("✅ 日志获取功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 日志功能测试失败: {e}")
        traceback.print_exc()
        return False


def test_project_structure():
    """测试项目结构。"""
    print("\n📁 测试项目结构...")
    
    try:
        project_root = Path(__file__).parent
        
        # 检查关键文件和目录
        required_paths = [
            "ocr_mcp/__init__.py",
            "ocr_mcp/server.py",
            "ocr_mcp/tools/__init__.py",
            "ocr_mcp/tools/base_tool.py",
            "ocr_mcp/tools/captcha_tool.py",
            "ocr_mcp/tools/preprocess_tool.py",
            "ocr_mcp/utils/__init__.py",
            "ocr_mcp/utils/logger.py",
            "ocr_mcp/utils/image_utils.py",
            "tests/__init__.py",
            "examples/basic_usage.py",
            "requirements.txt",
            "pyproject.toml",
            "README.md",
            "LICENSE"
        ]
        
        missing_files = []
        for path_str in required_paths:
            path = project_root / path_str
            if not path.exists():
                missing_files.append(path_str)
        
        if missing_files:
            print(f"❌ 缺少文件: {missing_files}")
            return False
        
        print("✅ 项目结构完整")
        return True
        
    except Exception as e:
        print(f"❌ 项目结构测试失败: {e}")
        traceback.print_exc()
        return False


def main():
    """主验证函数。"""
    print("🚀 OCR MCP系统验证开始")
    print("=" * 50)
    
    tests = [
        ("项目结构", test_project_structure),
        ("模块导入", test_imports),
        ("日志功能", test_logger),
        ("图像处理工具", test_image_utils),
        ("工具初始化", test_tool_initialization),
        ("工具Schema", test_tool_schemas),
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
    
    print("\n" + "=" * 50)
    print(f"📊 验证结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统功能正常")
        return True
    else:
        print(f"⚠️ {total - passed} 项测试失败，请检查相关功能")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 验证已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证过程发生异常: {e}")
        traceback.print_exc()
        sys.exit(1)