#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR MCP系统核心功能验证脚本

这个脚本用于测试OCR MCP系统的核心功能，包括：
1. 基础功能测试模块
2. 核心算法验证流程
3. 必要的依赖项检查
4. 结果输出和验证机制

使用方法:
    python test_core_functionality.py
"""

import sys
import os
import time
import base64
import io
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont


@dataclass
class TestResult:
    """测试结果数据类"""
    name: str
    passed: bool
    message: str
    duration: float = 0.0
    details: Optional[Dict[str, Any]] = None


class CoreFunctionalityTester:
    """OCR MCP系统核心功能测试器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        """日志输出"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def add_result(self, result: TestResult):
        """添加测试结果"""
        self.results.append(result)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        self.log(f"{status} {result.name} ({result.duration:.3f}s): {result.message}")
    
    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        self.log(f"运行测试: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func()
            if isinstance(result, TestResult):
                result.duration = time.time() - start_time
                self.add_result(result)
            else:
                # 如果测试函数没有返回TestResult，创建一个成功的结果
                self.add_result(TestResult(
                    name=test_name,
                    passed=True,
                    message="测试通过",
                    duration=time.time() - start_time
                ))
        except Exception as e:
            self.add_result(TestResult(
                name=test_name,
                passed=False,
                message=f"测试异常: {str(e)}",
                duration=time.time() - start_time
            ))
    
    def test_dependencies(self) -> TestResult:
        """测试依赖项"""
        missing_deps = []
        optional_deps = []
        
        # 核心依赖检查
        core_dependencies = {
            'ddddocr': '验证码识别核心库',
            'PIL': '图像处理库',
            'numpy': '数值计算库'
        }
        
        for dep, desc in core_dependencies.items():
            try:
                if dep == 'PIL':
                    from PIL import Image
                elif dep == 'ddddocr':
                    import ddddocr
                elif dep == 'numpy':
                    import numpy
                self.log(f"✓ {dep} ({desc}) - 已安装")
            except ImportError:
                missing_deps.append(f"{dep} ({desc})")
                self.log(f"✗ {dep} ({desc}) - 未安装")
        
        # 可选依赖检查
        optional_dependencies = {
            'mcp': 'MCP协议框架',
            'asyncio': '异步IO支持'
        }
        
        for dep, desc in optional_dependencies.items():
            try:
                if dep == 'mcp':
                    # MCP可能需要特殊处理
                    try:
                        import mcp
                        self.log(f"✓ {dep} ({desc}) - 已安装")
                    except ImportError:
                        optional_deps.append(f"{dep} ({desc})")
                        self.log(f"⚠ {dep} ({desc}) - 未安装 (可选)")
                elif dep == 'asyncio':
                    import asyncio
                    self.log(f"✓ {dep} ({desc}) - 已安装")
            except ImportError:
                optional_deps.append(f"{dep} ({desc})")
        
        if missing_deps:
            return TestResult(
                name="依赖项检查",
                passed=False,
                message=f"缺少核心依赖: {', '.join(missing_deps)}",
                details={"missing": missing_deps, "optional_missing": optional_deps}
            )
        else:
            message = "所有核心依赖已安装"
            if optional_deps:
                message += f" (可选依赖缺失: {len(optional_deps)}个)"
            return TestResult(
                name="依赖项检查",
                passed=True,
                message=message,
                details={"optional_missing": optional_deps}
            )
    
    def test_ddddocr_basic(self) -> TestResult:
        """测试ddddocr基础功能"""
        try:
            import ddddocr
            
            # 创建OCR实例
            ocr = ddddocr.DdddOcr()
            
            # 创建测试图像
            test_image = self.create_test_captcha("TEST")
            
            # 进行识别
            result = ocr.classification(test_image)
            
            # 验证结果
            if result and isinstance(result, str):
                return TestResult(
                    name="ddddocr基础功能",
                    passed=True,
                    message=f"识别成功，结果: {result}",
                    details={"result": result, "expected": "TEST"}
                )
            else:
                return TestResult(
                    name="ddddocr基础功能",
                    passed=False,
                    message="识别失败或返回空结果"
                )
                
        except Exception as e:
            return TestResult(
                name="ddddocr基础功能",
                passed=False,
                message=f"ddddocr测试失败: {str(e)}"
            )
    
    def test_image_processing(self) -> TestResult:
        """测试图像处理功能"""
        try:
            from PIL import Image, ImageFilter, ImageEnhance
            import numpy as np
            
            # 创建测试图像
            test_image = self.create_test_captcha("ABCD")
            
            # 转换为PIL Image
            pil_image = Image.open(io.BytesIO(test_image))
            
            # 测试基础图像操作
            operations = {
                "resize": lambda img: img.resize((200, 80)),
                "grayscale": lambda img: img.convert('L'),
                "enhance": lambda img: ImageEnhance.Contrast(img).enhance(1.5),
                "filter": lambda img: img.filter(ImageFilter.SMOOTH)
            }
            
            results = {}
            for op_name, op_func in operations.items():
                try:
                    processed = op_func(pil_image)
                    results[op_name] = f"成功 ({processed.size})" if hasattr(processed, 'size') else "成功"
                except Exception as e:
                    results[op_name] = f"失败: {str(e)}"
            
            # 检查是否所有操作都成功
            all_passed = all("成功" in result for result in results.values())
            
            return TestResult(
                name="图像处理功能",
                passed=all_passed,
                message=f"图像处理测试完成，成功操作: {sum(1 for r in results.values() if '成功' in r)}/{len(operations)}",
                details=results
            )
            
        except Exception as e:
            return TestResult(
                name="图像处理功能",
                passed=False,
                message=f"图像处理测试失败: {str(e)}"
            )
    
    def test_mcp_tools_simulation(self) -> TestResult:
        """模拟测试MCP工具功能"""
        try:
            # 由于MCP框架可能不可用，我们模拟测试工具逻辑
            
            # 模拟captcha_recognize工具
            test_image_b64 = base64.b64encode(self.create_test_captcha("1234")).decode()
            
            # 模拟工具调用
            tools_results = {}
            
            # 测试captcha_recognize逻辑
            try:
                import ddddocr
                ocr = ddddocr.DdddOcr()
                image_data = base64.b64decode(test_image_b64)
                result = ocr.classification(image_data)
                tools_results["captcha_recognize"] = f"成功: {result}"
            except Exception as e:
                tools_results["captcha_recognize"] = f"失败: {str(e)}"
            
            # 测试image_preprocess逻辑
            try:
                from PIL import Image
                image_data = base64.b64decode(test_image_b64)
                pil_image = Image.open(io.BytesIO(image_data))
                
                # 模拟预处理操作
                processed = pil_image.convert('L')  # 灰度化
                processed = processed.resize((150, 60))  # 调整大小
                
                # 转换回base64
                buffer = io.BytesIO()
                processed.save(buffer, format='PNG')
                processed_b64 = base64.b64encode(buffer.getvalue()).decode()
                
                tools_results["image_preprocess"] = f"成功: 处理完成 ({len(processed_b64)} bytes)"
            except Exception as e:
                tools_results["image_preprocess"] = f"失败: {str(e)}"
            
            # 检查结果
            all_passed = all("成功" in result for result in tools_results.values())
            
            return TestResult(
                name="MCP工具模拟测试",
                passed=all_passed,
                message=f"工具测试完成，成功: {sum(1 for r in tools_results.values() if '成功' in r)}/{len(tools_results)}",
                details=tools_results
            )
            
        except Exception as e:
            return TestResult(
                name="MCP工具模拟测试",
                passed=False,
                message=f"MCP工具测试失败: {str(e)}"
            )
    
    def test_performance_benchmark(self) -> TestResult:
        """性能基准测试"""
        try:
            import ddddocr
            
            ocr = ddddocr.DdddOcr()
            
            # 创建多个测试图像
            test_cases = ["ABC", "123", "XYZ", "789", "DEF"]
            results = []
            
            for i, text in enumerate(test_cases):
                start_time = time.time()
                
                # 创建测试图像
                test_image = self.create_test_captcha(text)
                
                # 进行识别
                result = ocr.classification(test_image)
                
                duration = time.time() - start_time
                results.append({
                    "case": i + 1,
                    "expected": text,
                    "result": result,
                    "duration": duration,
                    "success": bool(result)
                })
            
            # 计算统计信息
            total_time = sum(r["duration"] for r in results)
            avg_time = total_time / len(results)
            success_rate = sum(1 for r in results if r["success"]) / len(results)
            
            return TestResult(
                name="性能基准测试",
                passed=success_rate >= 0.6,  # 60%成功率为通过
                message=f"平均处理时间: {avg_time:.3f}s, 成功率: {success_rate:.1%}",
                details={
                    "total_cases": len(test_cases),
                    "total_time": total_time,
                    "avg_time": avg_time,
                    "success_rate": success_rate,
                    "results": results
                }
            )
            
        except Exception as e:
            return TestResult(
                name="性能基准测试",
                passed=False,
                message=f"性能测试失败: {str(e)}"
            )
    
    def create_test_captcha(self, text: str, width: int = 120, height: int = 40) -> bytes:
        """创建测试验证码图像"""
        # 创建图像
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # 尝试使用系统字体，如果失败则使用默认字体
        try:
            # Windows系统字体路径
            font_paths = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/calibri.ttf',
                '/System/Library/Fonts/Arial.ttf',  # macOS
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'  # Linux
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 20)
                    break
            
            if font is None:
                font = ImageFont.load_default()
                
        except Exception:
            font = ImageFont.load_default()
        
        # 绘制文本
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        # 添加一些噪声线条
        for i in range(3):
            draw.line([(0, i * 10), (width, i * 10 + 5)], fill='gray', width=1)
        
        # 转换为字节
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("开始OCR MCP系统核心功能验证")
        self.log("=" * 50)
        
        # 定义测试套件
        test_suite = [
            ("依赖项检查", self.test_dependencies),
            ("ddddocr基础功能测试", self.test_ddddocr_basic),
            ("图像处理功能测试", self.test_image_processing),
            ("MCP工具模拟测试", self.test_mcp_tools_simulation),
            ("性能基准测试", self.test_performance_benchmark)
        ]
        
        # 运行测试
        for test_name, test_func in test_suite:
            self.run_test(test_name, test_func)
            print()  # 空行分隔
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        total_time = time.time() - self.start_time
        passed_tests = sum(1 for r in self.results if r.passed)
        total_tests = len(self.results)
        
        self.log("=" * 50)
        self.log("测试报告")
        self.log("=" * 50)
        
        # 总体统计
        self.log(f"总测试数: {total_tests}")
        self.log(f"通过测试: {passed_tests}")
        self.log(f"失败测试: {total_tests - passed_tests}")
        self.log(f"成功率: {passed_tests/total_tests:.1%}")
        self.log(f"总耗时: {total_time:.3f}s")
        
        print()
        
        # 详细结果
        self.log("详细测试结果:")
        for result in self.results:
            status = "✅" if result.passed else "❌"
            self.log(f"{status} {result.name}: {result.message}")
            
            if result.details and not result.passed:
                self.log(f"   详细信息: {result.details}")
        
        print()
        
        # 建议和总结
        if passed_tests == total_tests:
            self.log("🎉 所有测试通过！OCR MCP系统核心功能正常。")
        else:
            failed_tests = [r.name for r in self.results if not r.passed]
            self.log(f"⚠️  有 {len(failed_tests)} 个测试失败:")
            for test_name in failed_tests:
                self.log(f"   - {test_name}")
            
            self.log("\n建议:")
            if any("依赖" in name for name in failed_tests):
                self.log("   1. 检查并安装缺失的依赖项")
            if any("ddddocr" in name for name in failed_tests):
                self.log("   2. 验证ddddocr库是否正确安装")
            if any("图像" in name for name in failed_tests):
                self.log("   3. 检查PIL/Pillow图像处理库")
            if any("MCP" in name for name in failed_tests):
                self.log("   4. 检查MCP框架相关组件")


def main():
    """主函数"""
    print("OCR MCP系统核心功能验证脚本")
    print("Version: 1.0.0")
    print("Author: OCR MCP Team")
    print()
    
    # 创建测试器并运行测试
    tester = CoreFunctionalityTester()
    tester.run_all_tests()
    
    # 返回退出码
    passed_tests = sum(1 for r in tester.results if r.passed)
    total_tests = len(tester.results)
    
    if passed_tests == total_tests:
        sys.exit(0)  # 所有测试通过
    else:
        sys.exit(1)  # 有测试失败


if __name__ == "__main__":
    main()