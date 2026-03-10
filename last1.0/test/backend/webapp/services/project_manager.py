# -*- coding: utf-8 -*-
"""
项目管理器 - 扫描和管理outputs目录的视频项目
"""
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger

from ..config import OUTPUTS_DIR
from .metadata_manager import MetadataManager


class ProjectManager:
    """项目管理器 - 扫描和管理视频项目"""

    def __init__(self):
        self.outputs_dir = Path(OUTPUTS_DIR)
        self.metadata_manager = MetadataManager()

    async def list_all_projects(self) -> List[Dict]:
        """
        扫描outputs目录，返回所有项目列表

        Returns:
            项目摘要列表
        """
        projects = []

        if not self.outputs_dir.exists():
            logger.warning(f"输出目录不存在: {self.outputs_dir}")
            return []

        # 遍历所有 video_* 目录
        for project_dir in self.outputs_dir.iterdir():
            if not project_dir.is_dir():
                continue

            if not project_dir.name.startswith("video_"):
                continue

            try:
                # 加载元数据
                metadata = self.metadata_manager.load_metadata(project_dir)

                # 统计分镜数量
                video_files = list(project_dir.glob("scene_*.mp4"))
                shot_count = len(video_files)

                # 解析时间戳
                created_at = self._parse_timestamp(project_dir.name)

                # 获取第一个分镜作为缩略图
                thumbnail_url = ""
                if video_files:
                    first_video = sorted(video_files)[0]
                    thumbnail_url = f"/videos/{project_dir.name}/{first_video.name}"

                # 判断生成阶段 - 优先使用metadata中的stage，文件扫描作为补充
                generation_stage = metadata.get("generation_stage", "script")
                keyframe_files = list(project_dir.glob("keyframes/keyframe_*.png")) + list(project_dir.glob("keyframes/keyframe_*.jpg"))
                keyframes_ready = len(keyframe_files)
                videos_ready = len(video_files)

                # 只在metadata未明确设定时，用文件扫描判断
                if generation_stage == "script":
                    if videos_ready > 0:
                        generation_stage = "videos"
                    elif keyframes_ready > 0:
                        generation_stage = "keyframes"

                # 构建项目摘要
                project_summary = {
                    "project_id": project_dir.name,
                    "title": metadata.get("title", project_dir.name),
                    "topic": metadata.get("topic", ""),
                    "shot_count": shot_count if shot_count > 0 else len(metadata.get("shots", [])),
                    "total_duration": metadata.get("total_duration", 0.0),
                    "viral_score": metadata.get("viral_score", 0.0),
                    "created_at": created_at.isoformat() if created_at else None,
                    "thumbnail_url": thumbnail_url,
                    "generation_stage": generation_stage,
                    "keyframes_ready": keyframes_ready,
                    "videos_ready": videos_ready
                }

                projects.append(project_summary)

            except Exception as e:
                logger.error(f"处理项目失败 {project_dir.name}: {e}")
                continue

        # 按创建时间倒序排列（最新的在前）
        projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        logger.info(f"找到 {len(projects)} 个视频项目")
        return projects

    async def get_project_detail(self, project_id: str) -> Optional[Dict]:
        """
        获取项目详情（包含所有分镜）

        Args:
            project_id: 项目ID (video_20260208_221834)

        Returns:
            项目详情字典，如果不存在则返回None
        """
        project_dir = self.outputs_dir / project_id

        if not project_dir.exists():
            logger.warning(f"项目不存在: {project_id}")
            return None

        try:
            # 加载元数据
            metadata = self.metadata_manager.load_metadata(project_dir)

            # 获取所有分镜文件
            video_files = sorted(project_dir.glob("scene_*.mp4"))
            shots = []

            # 获取自定义顺序
            custom_order = self.metadata_manager.get_shot_order(project_dir)

            for video_file in video_files:
                # 提取分镜ID (scene_001.mp4 -> 1)
                shot_id = int(video_file.stem.split("_")[1])

                # 获取视频时长
                duration = self._get_video_duration(video_file)

                # 获取文件大小
                file_size = video_file.stat().st_size

                # 从元数据读取描述信息
                shot_metadata = self._get_shot_metadata(metadata, shot_id)

                shot_info = {
                    "shot_id": shot_id,
                    "filename": video_file.name,
                    "duration": duration,
                    "visual_description": shot_metadata.get("visual_description", ""),
                    "narration": shot_metadata.get("narration", ""),
                    "file_size": file_size,
                    "video_url": f"/videos/{project_id}/{video_file.name}",
                    "shot_type": shot_metadata.get("shot_type", "")
                }

                shots.append(shot_info)

            # 如果有自定义顺序，按自定义顺序排列
            if custom_order:
                shots = self._reorder_shots(shots, custom_order)

            # 计算总时长
            total_duration = sum(shot["duration"] for shot in shots)

            # 解析创建时间
            created_at = self._parse_timestamp(project_id)

            # 构建项目详情
            project_detail = {
                "project_id": project_id,
                "title": metadata.get("title", project_id),
                "topic": metadata.get("topic", ""),
                "shots": shots,
                "total_duration": total_duration,
                "total_shots": len(shots),
                "viral_score": metadata.get("viral_score", 0.0),
                "viral_probability": metadata.get("viral_probability", 0.0),
                "viral_breakdown": metadata.get("viral_breakdown", {}),
                "metadata": metadata,
                "created_at": created_at.isoformat() if created_at else None
            }

            return project_detail

        except Exception as e:
            logger.error(f"获取项目详情失败 {project_id}: {e}")
            raise

    def _parse_timestamp(self, project_name: str) -> Optional[datetime]:
        """
        从项目名称解析时间戳

        Args:
            project_name: video_20260208_221834

        Returns:
            datetime对象
        """
        try:
            # 提取时间部分: 20260208_221834
            timestamp_str = project_name.replace("video_", "")
            # 解析: 2026-02-08 22:18:34
            return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except Exception as e:
            logger.warning(f"解析时间戳失败 {project_name}: {e}")
            return None

    def _get_video_duration(self, video_path: Path) -> float:
        """
        使用ffprobe获取视频时长

        Args:
            video_path: 视频文件路径

        Returns:
            时长（秒）
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                logger.warning(f"ffprobe失败: {result.stderr}")
                return 5.0  # 默认5秒

        except Exception as e:
            logger.error(f"获取视频时长失败 {video_path}: {e}")
            return 5.0  # 默认5秒

    def _get_shot_metadata(self, metadata: Dict, shot_id: int) -> Dict:
        """
        从元数据中获取指定分镜的信息

        Args:
            metadata: 项目元数据
            shot_id: 分镜ID

        Returns:
            分镜元数据字典
        """
        # 从metadata中的shots列表查找
        shots_metadata = metadata.get("shots", [])

        for shot in shots_metadata:
            if shot.get("id") == shot_id:
                return shot

        # 如果找不到，返回空字典
        return {}

    def _reorder_shots(self, shots: List[Dict], custom_order: List[int]) -> List[Dict]:
        """
        按自定义顺序重排分镜

        Args:
            shots: 分镜列表
            custom_order: 自定义顺序 [3, 1, 2, 4]

        Returns:
            重排后的分镜列表
        """
        # 创建shot_id到shot的映射
        shot_map = {shot["shot_id"]: shot for shot in shots}

        # 按custom_order重排
        reordered = []
        for shot_id in custom_order:
            if shot_id in shot_map:
                reordered.append(shot_map[shot_id])

        # 添加不在custom_order中的分镜（以防万一）
        for shot in shots:
            if shot["shot_id"] not in custom_order:
                reordered.append(shot)

        return reordered

    async def reorder_shots(self, project_id: str, shot_order: List[int]) -> bool:
        """
        保存分镜的新顺序

        Args:
            project_id: 项目ID
            shot_order: 新的分镜顺序

        Returns:
            是否成功
        """
        project_dir = self.outputs_dir / project_id

        if not project_dir.exists():
            logger.warning(f"项目不存在: {project_id}")
            return False

        try:
            self.metadata_manager.save_shot_order(project_dir, shot_order)
            return True
        except Exception as e:
            logger.error(f"保存分镜顺序失败 {project_id}: {e}")
            return False
