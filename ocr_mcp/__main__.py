"""OCR MCP Server entry point.

允许通过 python -m ocr_mcp 启动服务器。
"""

from .server import main

if __name__ == "__main__":
    main()