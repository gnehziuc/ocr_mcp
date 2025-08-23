#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立OCR工具 - 不依赖MCP框架的验证码识别工具
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

# 修复Pillow 10.x与ddddocr的兼容性问题
try:
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        setattr(Image, 'ANTIALIAS', Image.LANCZOS)
except ImportError:
    pass

# 检查依赖
try:
    import ddddocr
except ImportError:
    print("错误: 未安装ddddocr库")
    print("请运行: pip install ddddocr")
    sys.exit(1)

try:
    from PIL import Image, ImageEnhance
except ImportError:
    print("错误: 未安装Pillow库")
    print("请运行: pip install Pillow")
    sys.exit(1)


class StandaloneOCR:
    """独立OCR识别器"""
    
    def __init__(self):
        """初始化OCR引擎"""
        try:
            self.ocr_engine = ddddocr.DdddOcr()
            print("✅ OCR引擎初始化成功")
        except Exception as e:
            print(f"❌ OCR引擎初始化失败: {e}")
            sys.exit(1)
    
    def preprocess_image(self, image_path: str, enhance: bool = True) -> bytes:
        """预处理图像"""
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                if enhance:
                    # 增强对比度
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.5)
                    
                    # 增强锐度
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.2)
                
                # 调整尺寸（如果太大）
                if img.width > 800 or img.height > 600:
                    # 兼容不同Pillow版本的重采样方法
                    try:
                        img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                    except AttributeError:
                        # 旧版本Pillow使用LANCZOS常量
                        img.thumbnail((800, 600), Image.LANCZOS)
                
                # 转换为字节
                import io
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                return buffer.getvalue()
                
        except Exception as e:
            print(f"❌ 图像预处理失败: {e}")
            return None
    
    def recognize(self, image_path: str, preprocess: bool = True) -> Optional[str]:
        """识别验证码"""
        start_time = time.time()
        
        try:
            # 读取图像
            if preprocess:
                image_bytes = self.preprocess_image(image_path, enhance=True)
                if image_bytes is None:
                    return None
            else:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
            
            # 进行OCR识别
            result = self.ocr_engine.classification(image_bytes)
            
            processing_time = time.time() - start_time
            
            print(f"🎯 识别结果: {result}")
            print(f"⏱️  处理时间: {processing_time:.2f}秒")
            print(f"🔧 预处理: {'是' if preprocess else '否'}")
            
            return result
            
        except Exception as e:
            print(f"❌ 识别失败: {e}")
            return None
    
    def batch_recognize(self, image_paths: list, preprocess: bool = True) -> dict:
        """批量识别"""
        results = {}
        total_start = time.time()
        
        print(f"🚀 开始批量识别 {len(image_paths)} 个文件...")
        print("=" * 50)
        
        for i, image_path in enumerate(image_paths, 1):
            print(f"\n[{i}/{len(image_paths)}] 处理: {Path(image_path).name}")
            result = self.recognize(image_path, preprocess)
            results[image_path] = result
        
        total_time = time.time() - total_start
        success_count = sum(1 for r in results.values() if r is not None)
        
        print("\n" + "=" * 50)
        print(f"📊 批量识别完成")
        print(f"✅ 成功: {success_count}/{len(image_paths)}")
        print(f"⏱️  总时间: {total_time:.2f}秒")
        print(f"📈 平均时间: {total_time/len(image_paths):.2f}秒/张")
        
        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="独立OCR验证码识别工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python standalone_ocr.py captcha.png
    python standalone_ocr.py *.png --no-preprocess
    python standalone_ocr.py image1.jpg image2.png --batch
        """
    )
    
    parser.add_argument(
        'images',
        nargs='+',
        help='要识别的图像文件路径'
    )
    
    parser.add_argument(
        '--no-preprocess',
        action='store_true',
        help='跳过图像预处理'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        help='批量模式（显示详细统计）'
    )
    
    args = parser.parse_args()
    
    # 验证文件存在
    valid_images = []
    for image_path in args.images:
        if Path(image_path).exists():
            valid_images.append(image_path)
        else:
            print(f"⚠️  警告: 文件不存在 {image_path}")
    
    if not valid_images:
        print("❌ 错误: 没有找到有效的图像文件")
        sys.exit(1)
    
    # 初始化OCR
    ocr = StandaloneOCR()
    
    # 执行识别
    preprocess = not args.no_preprocess
    
    if len(valid_images) == 1 and not args.batch:
        # 单文件模式
        print(f"\n🔍 识别文件: {valid_images[0]}")
        result = ocr.recognize(valid_images[0], preprocess)
        if result:
            print(f"\n📋 可复制结果: {result}")
    else:
        # 批量模式
        results = ocr.batch_recognize(valid_images, preprocess)
        
        # 输出结果摘要
        print("\n📋 识别结果摘要:")
        for image_path, result in results.items():
            status = "✅" if result else "❌"
            print(f"{status} {Path(image_path).name}: {result or '识别失败'}")


if __name__ == "__main__":
    main()