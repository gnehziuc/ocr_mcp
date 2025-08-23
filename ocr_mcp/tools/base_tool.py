"""Base tool class for OCR MCP tools.

定义所有OCR工具的基础接口和通用功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseTool(ABC):
    """OCR工具基类。
    
    所有OCR工具都应该继承此类并实现必要的方法。
    """
    
    def __init__(self) -> None:
        """初始化工具。"""
        self._name: Optional[str] = None
        self._description: Optional[str] = None
        self._input_schema: Optional[Dict[str, Any]] = None
        
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称。"""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述。"""
        pass
        
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """输入参数schema。"""
        pass
        
    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """执行工具功能。
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 参数错误
            RuntimeError: 执行错误
        """
        pass
        
    def validate_arguments(self, arguments: Dict[str, Any]) -> None:
        """验证输入参数。
        
        Args:
            arguments: 输入参数字典
            
        Raises:
            ValueError: 参数验证失败
        """
        # 基础验证逻辑可以在这里实现
        # 子类可以重写此方法添加特定验证
        pass