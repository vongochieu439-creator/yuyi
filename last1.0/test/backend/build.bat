@echo off
chcp 65001 >nul
echo ===================================================
echo   羽翼Pro V2 - 打包构建脚本
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/4] 升级 PyInstaller ...
pip install "pyinstaller>=6.0" --quiet
if errorlevel 1 (
    echo 错误: PyInstaller 安装失败
    pause
    exit /b 1
)

echo [2/4] 安装项目依赖 ...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo [3/4] 开始 PyInstaller 打包 ...
pyinstaller yuyi_pro.spec --noconfirm --clean
if errorlevel 1 (
    echo 错误: 打包失败，请检查上方日志
    pause
    exit /b 1
)

echo [4/4] 创建运行时目录 ...
if not exist "dist\YuyiPro\outputs" mkdir "dist\YuyiPro\outputs"
if not exist "dist\YuyiPro\brand_profiles" mkdir "dist\YuyiPro\brand_profiles"
if not exist "dist\YuyiPro\logs" mkdir "dist\YuyiPro\logs"

echo.
echo ===================================================
echo   构建完成！
echo   输出目录: dist\YuyiPro\
echo   双击 dist\YuyiPro\YuyiPro.exe 启动
echo ===================================================
pause
