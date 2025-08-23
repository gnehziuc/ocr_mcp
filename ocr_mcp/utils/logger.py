"""Logging utilities for OCR MCP server.

提供统一的日志配置和管理功能。
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """设置日志记录器。
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        format_string: 日志格式字符串
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    
    # 设置日志格式
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器。
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)