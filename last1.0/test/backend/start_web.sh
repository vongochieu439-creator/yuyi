#!/bin/bash
# 羽翼Pro V2 - 一键启动脚本（Linux/Mac）

echo "========================================"
echo "羽翼Pro V2 - Web服务器启动"
echo "========================================"
echo ""

# 设置API Key
export NANOBANANA_API_KEY="sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq"
export NANOBANANA_API_BASE_URL="https://api.remenbaike.com"
export KLING_API_KEY="sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq"
export KLING_API_BASE_URL="https://api.remenbaike.com"

echo "✅ NanoBanana API Key已配置"
echo "✅ Kling API Key已配置"
echo "✅ Base URL: https://api.remenbaike.com"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python未安装或不在PATH中"
    echo "请先安装Python 3.8+"
    exit 1
fi

echo "✅ Python已就绪"
echo ""

# 启动Web服务器
echo "🚀 启动Web服务器..."
echo "📍 访问地址: http://localhost:8080"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "========================================"
echo ""

python3 -m webapp.main
