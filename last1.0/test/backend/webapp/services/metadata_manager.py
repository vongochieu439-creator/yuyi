# -*- coding: utf-8 -*-
"""
元数据管理器 - 存储和读取项目元数据
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

from ..config import OUTPUTS_DIR


class MetadataManager:
    """元数据管理器"""

    @staticmethod
    def get_metadata_file(project_dir: Path) -> Path:
        """获取元数据文件路径"""
        return project_dir / "metadata.json"

    @staticmethod
    def load_metadata(project_dir: Path) -> Dict:
        """
        加载项目元数据

        Args:
            project_dir: 项目目录路径

        Returns:
            元数据字典
        """
        metadata_file = MetadataManager.get_metadata_file(project_dir)

        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取元数据失败 {metadata_file}: {e}")
                return {}

        # 如果没有metadata.json，返回默认值
        return {
            "title": project_dir.name,
            "topic": "",
            "viral_score": 0.0,
            "total_duration": 0.0,
            "shot_count": 0,
            "created_at": None,
            "custom_shot_order": None
        }

    @staticmethod
    def save_metadata(project_dir: Path, data: Dict):
        """
        保存项目元数据

        Args:
            project_dir: 项目目录路径
            data: 元数据字典
        """
        metadata_file = MetadataManager.get_metadata_file(project_dir)

        # 添加更新时间
        data["updated_at"] = datetime.now().isoformat()

        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"元数据已保存: {metadata_file}")
        except Exception as e:
            logger.error(f"保存元数据失败 {metadata_file}: {e}")
            raise

    @staticmethod
    def update_metadata(project_dir: Path, updates: Dict):
        """
        更新项目元数据（部分更新）

        Args:
            project_dir: 项目目录路径
            updates: 要更新的字段
        """
        metadata = MetadataManager.load_metadata(project_dir)
        metadata.update(updates)
        MetadataManager.save_metadata(project_dir, metadata)

    @staticmethod
    def save_shot_order(project_dir: Path, shot_order: list):
        """
        保存分镜排序

        Args:
            project_dir: 项目目录路径
            shot_order: 分镜顺序列表 [1, 3, 2, 4]
        """
        MetadataManager.update_metadata(project_dir, {
            "custom_shot_order": shot_order
        })
        logger.info(f"分镜顺序已保存: {shot_order}")

    @staticmethod
    def get_shot_order(project_dir: Path) -> Optional[list]:
        """
        获取自定义分镜顺序

        Returns:
            分镜顺序列表，如果没有自定义顺序则返回None
        """
        metadata = MetadataManager.load_metadata(project_dir)
        return metadata.get("custom_shot_order")

    @staticmethod
    def load_metadata_from_project_id(project_id: str) -> Optional[Dict]:
        """
        通过project_id加载元数据

        Args:
            project_id: 项目ID (如: video_20260208_221834)

        Returns:
            元数据字典，如果项目不存在返回None
        """
        project_dir = Path(OUTPUTS_DIR) / project_id
        if not project_dir.exists():
            logger.warning(f"项目目录不存在: {project_dir}")
            return None
        return MetadataManager.load_metadata(project_dir)

    @staticmethod
    def save_metadata_to_project_id(project_id: str, data: Dict):
        """
        通过project_id保存元数据

        Args:
            project_id: 项目ID
            data: 元数据字典
        """
        project_dir = Path(OUTPUTS_DIR) / project_id
        if not project_dir.exists():
            raise FileNotFoundError(f"项目目录不存在: {project_dir}")
        MetadataManager.save_metadata(project_dir, data)
