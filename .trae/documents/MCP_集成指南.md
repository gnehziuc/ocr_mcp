# 轻量级OCR MCP 系统集成指南

## 1. MCP协议概述

Model Context Protocol (MCP) 是一个开放标准，用于AI模型与外部工具和数据源的安全连接。本轻量级OCR MCP系统实现了极简的MCP服务器，为AI模型提供免费的验证码识别服务。

### 1.1 协议特性

- **标准化接口**: 符合MCP 2024-11-05规范
- **JSON-RPC 2.0**: 基于标准的远程过程调用协议
- **零配置**: 无需配置，启动即用
- **免费使用**: 无需认证，完全免费
- **轻量级**: 无数据存储，高性能

## 2. 快速开始

### 2.1 启动MCP服务器

```bash
# 安装核心依赖
pip install ddddocr==1.5.6 pillow mcp

# 启动轻量级MCP服务器
python -m ocr_mcp.server
```

### 2.2 基本连接示例

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # 连接到OCR MCP服务器
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "ocr_mcp.server"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            # 获取可用工具列表
            tools = await session.list_tools()
            print(f"可用工具: {[tool.name for tool in tools.tools]}")
            
            # 调用验证码识别工具
            result = await session.call_tool(
                "captcha_recognize",
                {
                    "image_data": "base64_encoded_image_data",
                    "options": {
                        "preprocess": True
                    }
                }
            )
            
            print(f"识别结果: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 3. 可用工具详解

### 3.1 captcha_recognize - 验证码识别

**功能**: 识别各种类型的验证码图片

**参数**:
- `image_data` (string): Base64编码的图像数据
- `options` (object, 可选):
  - `preprocess` (boolean): 是否预处理，默认true

**返回值**:
```json
{
  "type": "text",
  "text": "识别结果: ABCD\n置信度: 0.95"
}
```

**使用示例**:
```python
result = await session.call_tool(
    "captcha_recognize",
    {
        "image_data": base64_image,
        "options": {
            "preprocess": True
        }
    }
)
```

### 3.2 image_preprocess - 图像预处理

**功能**: 对图像进行预处理优化

**参数**:
- `image_data` (string): Base64编码的图像数据
- `operations` (array): 预处理操作列表，可选值: ["denoise", "enhance"]

**返回值**:
```json
{
  "type": "text",
  "text": "预处理完成\n应用操作: 去噪, 增强"
}
```

## 4. 与AI模型集成

### 4.1 Claude集成示例

```python
# Claude Desktop配置文件 (claude_desktop_config.json)
{
  "mcpServers": {
    "ocr-server": {
      "command": "python",
      "args": ["-m", "ocr_mcp.server"]
    }
  }
}
```

### 4.2 自定义AI应用集成

```python
class OCRAssistant:
    def __init__(self):
        self.mcp_session = None
    
    async def connect_ocr_server(self):
        """连接到OCR MCP服务器"""
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "ocr_mcp.server"]
        )
        
        self.read, self.write = await stdio_client(server_params).__aenter__()
        self.mcp_session = await ClientSession(self.read, self.write).__aenter__()
        await self.mcp_session.initialize()
    
    async def recognize_captcha(self, image_path: str) -> str:
        """识别验证码"""
        # 读取并编码图像
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 调用OCR工具
        result = await self.mcp_session.call_tool(
            "captcha_recognize",
            {"image_data": image_data}
        )
        
        return result.content[0].text
    
    async def preprocess_image(self, image_path: str) -> str:
        """预处理图像"""
        # 读取并编码图像
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 调用预处理工具
        result = await self.mcp_session.call_tool(
            "image_preprocess",
            {
                "image_data": image_data,
                "operations": ["denoise", "enhance"]
            }
        )
        
        return result.content[0].text
```

## 5. 错误处理

### 5.1 常见错误码

| 错误码 | 错误类型 | 描述 |
|--------|----------|------|
| -32600 | Invalid Request | 无效的JSON-RPC请求 |
| -32601 | Method not found | 工具不存在 |
| -32602 | Invalid params | 参数格式错误 |
| -32603 | Internal error | 服务器内部错误 |
| -1001 | Image decode error | 图像解码失败 |
| -1002 | OCR processing error | OCR处理失败 |

### 5.2 错误处理示例

```python
try:
    result = await session.call_tool(
        "captcha_recognize",
        {"image_data": invalid_image_data}
    )
except McpError as e:
    if e.code == -1001:
        print("图像格式不支持或数据损坏")
    elif e.code == -1002:
        print("OCR处理失败，请检查图像质量")
    else:
        print(f"处理失败: {e.message}")
```

## 6. 性能优化

### 6.1 图像预处理建议

- 确保图像清晰度足够 (建议最小尺寸: 100x40像素)
- 使用PNG或JPEG格式
- 避免过度压缩的图像
- 对于模糊图像，启用预处理选项

### 6.2 使用建议

- 单次处理图像，避免并发过多请求
- 图像大小控制在5MB以内
- 优先使用预处理功能提高识别率

## 7. 部署和配置

### 7.1 简单部署

```bash
# 安装依赖
pip install ddddocr==1.5.6 pillow mcp

# 直接启动
python -m ocr_mcp.server
```

### 7.2 Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN pip install ddddocr==1.5.6 pillow mcp

COPY ocr_mcp/ ./ocr_mcp/

CMD ["python", "-m", "ocr_mcp.server"]
```

## 8. 故障排除

### 8.1 常见问题

**Q: 连接MCP服务器失败**
A: 检查Python环境和依赖安装，确保服务器进程正常启动

**Q: 识别准确率低**
A: 尝试启用图像预处理，或检查图像质量

**Q: 处理速度慢**
A: 减少图像尺寸，确保图像清晰度

### 8.2 调试建议

- 检查图像是否正确编码为base64
- 确认图像格式为PNG或JPEG
- 验证图像内容是否为验证码
- 尝试使用预处理功能

## 9. 总结

本轻量级OCR MCP系统提供了：

- **简单易用**: 零配置，启动即用
- **完全免费**: 无需注册，无使用限制
- **高性能**: 基于ddddocr的高精度识别
- **标准协议**: 符合MCP规范，兼容各种AI模型
- **隐私保护**: 不存储任何数据，处理完即删除

通过本指南，您可以快速将OCR功能集成到AI应用中，为AI模型提供强大的验证码识别能力。系统专注于核心功能，确保高效、安全、易用。