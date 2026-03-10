# -*- coding: utf-8 -*-
"""
运行时路径解析 - 兼容 PyInstaller 冻结模式和开发模式
"""
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """
    获取应用根目录（存放 outputs/, logs/, brand_profiles/ 等运行时数据）
    - 冻结模式: exe 所在目录 (dist/YuyiPro/)
    - 开发模式: 项目根目录 (yuyi_pro_v2/)
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def get_bundle_dir() -> Path:
    """
    获取打包数据目录（存放 webapp/static/ 等只读资源）
    - 冻结模式: _MEIPASS 临时解压目录
    - 开发模式: 项目根目录（同 get_app_dir）
    """
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent
