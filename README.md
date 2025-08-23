# OCR MCP (Model Context Protocol) 系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP Protocol](https://img.shields.io/badge/MCP-2024--11--05-orange.svg)](https://modelcontextprotocol.io)

一个基于Python的轻量级OCR MCP服务器，专门为AI模型提供验证码识别和图像预处理功能。系统采用ddddocr引擎，符合MCP 2024-11-05协议标准，完全免费使用。

## ✨ 特性

- 🚀 **轻量级设计**: 无需数据库存储，内存处理，启动即用
- 🔒 **隐私保护**: 不存储任何用户数据，处理完即删除
- 🎯 **高精度识别**: 基于ddddocr引擎的验证码识别
- 🛠️ **图像预处理**: 支持去噪、增强、尺寸调整等操作
- 📡 **标准协议**: 完全符合MCP 2024-11-05协议规范
- 🆓 **完全免费**: 无需注册，无使用限制
- 🔧 **易于集成**: 支持Claude、ChatGPT等主流AI模型

## 🚀 快速开始

### 系统要求

- Python 3.10+ (推荐 3.13)
- Windows/Linux/macOS
- 至少 2GB 可用内存

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd free_ocr

# 安装依赖 (注意: 需要兼容的Pillow版本)
pip install -r requirements.txt

# 验证安装
python verify_mcp_installation.py
```

### 启动服务器

```bash
# 启动MCP服务器
python -m ocr_mcp.server

# 服务器启动成功后会显示:
# INFO - ddddocr引擎初始化成功
# INFO - 已注册 2 个工具: ['captcha_recognize', 'image_preprocess']
# INFO - MCP服务器已启动，等待客户端连接...
```

### 兼容性说明

**重要**: 由于ddddocr与新版Pillow的兼容性问题，本项目已配置使用Pillow 10.x版本。如果遇到 `PIL.Image.ANTIALIAS` 错误，请运行:

```bash
pip install "Pillow>=10.1.0,<11.0.0"
pip uninstall ddddocr -y
pip install ddddocr
```

### 基本使用示例

```python
import asyncio
import base64
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # 连接到OCR MCP服务器
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "ocr_mcp"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            # 获取可用工具列表
            tools = await session.list_tools()
            print(f"可用工具: {[tool.name for tool in tools.tools]}")
            
            # 读取验证码图片
            with open("captcha.png", "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # 调用验证码识别工具
            result = await session.call_tool(
                "captcha_recognize",
                {
                    "image_data": image_data,
                    "options": {
                        "preprocess": True,
                        "confidence_threshold": 0.8
                    }
                }
            )
            
            print(f"识别结果: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🛠️ 可用工具

### 1. captcha_recognize - 验证码识别

识别各种类型的验证码图片，基于ddddocr引擎提供高精度识别。

**参数:**
- `image_data` (string): Base64编码的图像数据
- `options` (object, 可选):
  - `preprocess` (boolean): 是否进行图像预处理，默认true
  - `confidence_threshold` (float): 置信度阈值(0-1)，默认0.8

**返回值:**
```json
{
  "type": "text",
  "text": "识别结果: ABCD\n置信度: 0.95\n处理时间: 0.12秒"
}
```

### 2. image_preprocess - 图像预处理

对图像进行预处理优化，包括去噪、对比度增强、尺寸调整等操作。

**参数:**
- `image_data` (string): Base64编码的图像数据
- `operations` (array): 预处理操作列表，可选值: ["denoise", "enhance", "resize"]
- `options` (object, 可选):
  - `contrast` (number): 对比度增强因子，默认1.5
  - `sharpness` (number): 锐化增强因子，默认1.2
  - `max_width` (integer): 最大宽度，默认800
  - `max_height` (integer): 最大高度，默认600
  - `return_processed_image` (boolean): 是否返回处理后的图像数据，默认false

**返回值:**
```json
{
  "type": "text",
  "text": "预处理完成\n应用操作: 去噪, 增强\n处理时间: 0.08秒"
}
```

## 🔧 使用模式

### 模式1: MCP服务器模式（推荐）

适用于AI模型集成，如Claude Desktop、ChatGPT等。

```bash
# 启动MCP服务器
python -m ocr_mcp.server
```

### 模式2: 独立OCR模式

适用于直接命令行使用，无需MCP框架。

```bash
# 单文件识别
python standalone_ocr.py captcha.png

# 批量识别
python standalone_ocr.py *.png --batch

# 跳过预处理（更快但可能精度较低）
python standalone_ocr.py image.jpg --no-preprocess

# 查看帮助
python standalone_ocr.py --help
```

**独立模式特性:**
- ✅ 无需MCP框架依赖
- ✅ 支持单文件和批量处理
- ✅ 可选图像预处理
- ✅ 详细的处理统计
- ✅ 命令行友好界面

## 🤖 AI模型集成

### Claude Desktop集成

在Claude Desktop配置文件中添加OCR服务器。详细配置选项请参考[服务器配置](#服务器配置)部分。

**基本配置:**
```json
{
  "mcpServers": {
    "ocr-server": {
      "command": "python",
      "args": ["-m", "ocr_mcp"]
    }
  }
}
```

### 自定义AI应用集成

```python
class OCRAssistant:
    def __init__(self):
        self.mcp_session = None
    
    async def connect_ocr_server(self):
        """连接到OCR MCP服务器"""
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "ocr_mcp"]
        )
        
        self.read, self.write = await stdio_client(server_params).__aenter__()
        self.mcp_session = await ClientSession(self.read, self.write).__aenter__()
        await self.mcp_session.initialize()
    
    async def recognize_captcha(self, image_path: str) -> str:
        """识别验证码"""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        result = await self.mcp_session.call_tool(
            "captcha_recognize",
            {"image_data": image_data}
        )
        
        return result.content[0].text
```

### NPX集成方式

使用npx可以快速启动OCR MCP服务器，无需手动安装Python依赖：

```bash
# 使用npx启动OCR服务器
npx @modelcontextprotocol/server-python python -m ocr_mcp

# 指定Python路径
npx @modelcontextprotocol/server-python /usr/bin/python3 -m ocr_mcp

# 带环境变量启动
OCR_LOG_LEVEL=DEBUG npx @modelcontextprotocol/server-python python -m ocr_mcp
```

**Claude Desktop配置（NPX方式）:**
```json
{
  "mcpServers": {
    "ocr-server": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-python",
        "python",
        "-m",
        "ocr_mcp"
      ],
      "env": {
        "OCR_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### UVX集成方式

使用uvx（uv的执行器）可以在隔离环境中运行OCR服务器：

```bash
# 使用uvx启动OCR服务器
uvx --from ocr-mcp ocr-mcp

# 指定Python版本
uvx --python 3.11 --from ocr-mcp ocr-mcp

# 带额外依赖启动
uvx --from ocr-mcp --with pillow==10.1.0 ocr-mcp

# 开发模式启动
uvx --from . ocr-mcp --debug
```

**Claude Desktop配置（UVX方式）:**
```json
{
  "mcpServers": {
    "ocr-server": {
      "command": "uvx",
      "args": [
        "--from",
        "ocr-mcp",
        "ocr-mcp"
      ],
      "env": {
        "OCR_LOG_LEVEL": "INFO",
        "UV_PYTHON": "3.11"
      }
    }
  }
}
```

**UVX优势:**
- 🔒 **隔离环境**: 自动创建独立的Python环境
- ⚡ **快速启动**: 缓存依赖，启动速度更快
- 🎯 **版本控制**: 精确控制Python和依赖版本
- 🛡️ **安全性**: 避免全局环境污染

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行测试并显示覆盖率
pytest --cov=ocr_mcp

# 运行特定测试文件
pytest tests/test_captcha_tool.py

# 运行测试并生成详细报告
pytest -v --cov=ocr_mcp --cov-report=html
```

## 📦 项目结构

```
free_ocr/
├── ocr_mcp/                 # 主包
│   ├── __init__.py
│   ├── __main__.py          # 入口模块
│   ├── server.py            # MCP服务器核心
│   ├── tools/               # 工具模块
│   │   ├── __init__.py
│   │   ├── base_tool.py     # 工具基类
│   │   ├── captcha_tool.py  # 验证码识别工具
│   │   └── preprocess_tool.py # 图像预处理工具
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── logger.py        # 日志工具
│       └── image_utils.py   # 图像处理工具
├── tests/                   # 测试文件
│   ├── __init__.py
│   ├── conftest.py          # 测试配置
│   ├── test_image_utils.py  # 图像工具测试
│   ├── test_captcha_tool.py # 验证码工具测试
│   └── test_preprocess_tool.py # 预处理工具测试
├── examples/                # 使用示例
├── requirements.txt         # 依赖列表
├── pyproject.toml          # 项目配置
└── README.md               # 项目文档
```

## ⚙️ 配置

### 服务器配置

#### MCP服务器启动参数

```bash
# 基本启动
python -m ocr_mcp

# 指定端口和主机
python -m ocr_mcp --host 0.0.0.0 --port 8080

# 启用调试模式
python -m ocr_mcp --debug

# 设置最大并发连接数
python -m ocr_mcp --max-connections 10
```

#### Claude Desktop配置

在Claude Desktop的配置文件中添加OCR服务器:

```json
{
  "mcpServers": {
    "ocr-server": {
      "command": "python",
      "args": ["-m", "ocr_mcp"],
      "env": {
        "OCR_LOG_LEVEL": "INFO",
        "OCR_MAX_IMAGE_SIZE": "5"
      }
    }
  }
}
```

#### 自定义应用配置

```python
from mcp import StdioServerParameters

# 服务器参数配置
server_params = StdioServerParameters(
    command="python",
    args=["-m", "ocr_mcp"],
    env={
        "OCR_LOG_LEVEL": "DEBUG",
        "OCR_MAX_IMAGE_SIZE": "10"
    }
)
```

### 环境变量

```bash
# 日志级别
export OCR_LOG_LEVEL=INFO

# 最大图像大小(MB)
export OCR_MAX_IMAGE_SIZE=5
```

### 性能优化建议

1. **图像质量**: 确保图像清晰度足够(建议最小尺寸: 100x40像素)
2. **图像格式**: 使用PNG或JPEG格式
3. **图像大小**: 控制在5MB以内
4. **预处理**: 对于模糊图像，启用预处理选项

## 🔧 开发

### 代码规范

```bash
# 代码格式化
black ocr_mcp/

# 代码检查
flake8 ocr_mcp/

# 类型检查
mypy ocr_mcp/
```

### 添加新工具

1. 继承`BaseTool`类
2. 实现必要的方法
3. 在服务器中注册工具
4. 添加相应的测试

```python
from ocr_mcp.tools.base_tool import BaseTool

class CustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "custom_tool"
    
    @property
    def description(self) -> str:
        return "自定义工具描述"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            },
            "required": ["param"]
        }
    
    async def execute(self, **kwargs) -> Any:
        # 实现工具逻辑
        return {"result": "success"}
```

## 🐛 故障排除

### 常见问题

**Q: 连接MCP服务器失败**
A: 检查Python环境和依赖安装，确保服务器进程正常启动

**Q: 识别准确率低**
A: 尝试启用图像预处理，或检查图像质量

**Q: 处理速度慢**
A: 减少图像尺寸，确保图像清晰度

### 错误码说明

| 错误码 | 错误类型 | 描述 |
|--------|----------|------|
| -32600 | Invalid Request | 无效的JSON-RPC请求 |
| -32601 | Method not found | 工具不存在 |
| -32602 | Invalid params | 参数格式错误 |
| -32603 | Internal error | 服务器内部错误 |
| -1001 | Image decode error | 图像解码失败 |
| -1002 | OCR processing error | OCR处理失败 |

## 📄 许可证

本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📞 支持

如果您在使用过程中遇到问题，请：

1. 查看[文档](docs/)
2. 搜索[Issues](../../issues)
3. 提交新的[Issue](../../issues/new)

## 🙏 致谢

- [ddddocr](https://github.com/sml2h3/ddddocr) - 优秀的OCR识别库
- [MCP](https://modelcontextprotocol.io) - Model Context Protocol标准
- [Pillow](https://pillow.readthedocs.io/) - Python图像处理库

---

**OCR MCP系统** - 为AI模型提供强大的验证码识别能力 🚀