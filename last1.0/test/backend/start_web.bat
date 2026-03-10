@echo off
REM 羽翼Pro V2 - 一键启动脚本（Windows）

echo ========================================
echo 羽翼Pro V2 - Web服务器启动
echo ========================================
echo.

REM 设置API Key
set NANOBANANA_API_KEY=sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq
set NANOBANANA_API_BASE_URL=https://api.remenbaike.com
set KLING_API_KEY=sk-gd4jp9vmEl0pwIFg0dA37MFtIuo0wRT0J6a0qMb8ZJWWHPxq
set KLING_API_BASE_URL=https://api.remenbaike.com

echo ✅ NanoBanana API Key已配置
echo ✅ Kling API Key已配置
echo ✅ Base URL: https://api.remenbaike.com
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或不在PATH中
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python已就绪
echo.

REM 启动Web服务器
echo 🚀 启动Web服务器...
echo 📍 访问地址: http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python -m webapp.main

pause
