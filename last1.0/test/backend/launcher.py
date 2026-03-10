# -*- coding: utf-8 -*-
"""
羽翼Pro V2 - PyInstaller 启动入口
双击 YuyiPro.exe 即可启动服务并自动打开浏览器
"""
import sys
import os
import socket
import threading
import webbrowser
import time
from pathlib import Path


def get_app_dir():
    """获取应用根目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def find_free_port(start=8082, end=8099):
    """从 start 开始寻找第一个可用端口"""
    for port in range(start, end + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return start  # fallback


def open_browser(port):
    """延迟2秒后自动打开浏览器"""
    time.sleep(2)
    webbrowser.open(f"http://127.0.0.1:{port}")


def main():
    app_dir = get_app_dir()

    # 设置工作目录为应用根目录
    os.chdir(str(app_dir))

    # 开发模式下确保项目根目录在 sys.path 中
    if not getattr(sys, 'frozen', False):
        sys.path.insert(0, str(app_dir))

    # 创建运行时目录
    for dirname in ("outputs", "brand_profiles", "logs"):
        (app_dir / dirname).mkdir(parents=True, exist_ok=True)

    # 寻找可用端口
    port = find_free_port()

    print("=" * 50)
    print("  羽翼Pro V2 - AI视频生成系统")
    print("=" * 50)
    print(f"  服务地址: http://127.0.0.1:{port}")
    print(f"  数据目录: {app_dir}")
    print("  按 Ctrl+C 停止服务")
    print("=" * 50)

    # 延迟打开浏览器
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # 导入并启动服务（必须在 sys.path 设置之后）
    import uvicorn
    from webapp.main import app
    from webapp.config import HOST

    uvicorn.run(app, host=HOST, port=port, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
