# -*- coding: utf-8 -*-
"""
免费素材搜索服务 - Pexels/Pixabay商用视频素材
根据脚本镜头描述自动匹配、下载素材视频
"""
import os
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode
from loguru import logger

import httpx


# Pexels免费API Key（注册即得，无费用）
# 用户可在 https://www.pexels.com/api/ 免费注册
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "uGBeWKQqDe3VX7VVrHrN4lZGlo9BBe2mb7qfwM3qzqSYotAt4uWoBRiS")


class MaterialService:
    """免费商用素材搜索+下载服务"""

    def __init__(self, pexels_key: str = ""):
        self.pexels_key = pexels_key or PEXELS_API_KEY
        self._cache_dir: Optional[Path] = None

    def _get_cache_dir(self) -> Path:
        if not self._cache_dir:
            from ..config import OUTPUTS_DIR
            self._cache_dir = Path(OUTPUTS_DIR) / "_material_cache"
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        return self._cache_dir

    async def search_pexels_videos(
        self,
        query: str,
        orientation: str = "portrait",
        per_page: int = 15,
        min_duration: int = 3,
    ) -> List[Dict]:
        """
        搜索Pexels免费商用视频素材

        Args:
            query: 英文搜索词（如 "skincare close up"）
            orientation: portrait(竖屏) / landscape(横屏) / square
            per_page: 每页数量
            min_duration: 最短时长(秒)

        Returns:
            [{url, preview_url, duration, width, height, photographer}]
        """
        if not self.pexels_key:
            logger.warning("Pexels API Key未设置，跳过素材搜索")
            return []

        headers = {
            "Authorization": self.pexels_key,
            "User-Agent": "YuYiPro/1.0",
        }
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
        }
        url = f"https://api.pexels.com/videos/search?{urlencode(params)}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Pexels搜索失败: {resp.status_code} {resp.text[:200]}")
                    return []

                data = resp.json()
                videos = data.get("videos", [])
                results = []

                for v in videos:
                    duration = v.get("duration", 0)
                    if duration < min_duration:
                        continue

                    # 找最佳分辨率的文件
                    best_file = self._pick_best_file(v.get("video_files", []), orientation)
                    if not best_file:
                        continue

                    # 预览图
                    image = v.get("image", "")
                    video_pictures = v.get("video_pictures", [])
                    preview = video_pictures[0]["picture"] if video_pictures else image

                    results.append({
                        "id": v.get("id"),
                        "url": best_file["link"],
                        "preview_url": preview,
                        "duration": duration,
                        "width": best_file.get("width", 0),
                        "height": best_file.get("height", 0),
                        "photographer": v.get("user", {}).get("name", ""),
                        "source": "pexels",
                    })

                logger.info(f"Pexels搜索 '{query}': {len(results)}/{len(videos)} 可用")
                return results

        except Exception as e:
            logger.error(f"Pexels搜索异常: {e}")
            return []

    async def search_pexels_images(
        self,
        query: str,
        orientation: str = "portrait",
        per_page: int = 10,
    ) -> List[Dict]:
        """搜索Pexels免费商用图片素材"""
        if not self.pexels_key:
            return []

        headers = {"Authorization": self.pexels_key, "User-Agent": "YuYiPro/1.0"}
        params = {"query": query, "per_page": per_page, "orientation": orientation}
        url = f"https://api.pexels.com/v1/search?{urlencode(params)}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                results = []
                for photo in data.get("photos", []):
                    src = photo.get("src", {})
                    results.append({
                        "id": photo.get("id"),
                        "url": src.get("original", ""),
                        "preview_url": src.get("medium", src.get("small", "")),
                        "width": photo.get("width", 0),
                        "height": photo.get("height", 0),
                        "photographer": photo.get("photographer", ""),
                        "source": "pexels",
                    })
                return results
        except Exception as e:
            logger.error(f"Pexels图片搜索异常: {e}")
            return []

    async def search_for_shot(
        self,
        visual_description: str,
        shot_type: str = "medium",
        orientation: str = "portrait",
    ) -> List[Dict]:
        """
        根据镜头的visual_description搜索匹配素材

        Args:
            visual_description: 英文视觉描述
            shot_type: 镜头类型
            orientation: 视频方向

        Returns:
            最匹配的素材列表（视频+图片混合）
        """
        # 从visual_description提取搜索关键词（取前几个英文词）
        keywords = self._extract_keywords(visual_description)
        if not keywords:
            keywords = "product showcase"

        # 并行搜索视频和图片
        video_task = self.search_pexels_videos(keywords, orientation, per_page=5)
        image_task = self.search_pexels_images(keywords, orientation, per_page=3)

        videos, images = await asyncio.gather(video_task, image_task)

        # 视频优先，图片补充
        results = []
        for v in videos:
            v["type"] = "video"
            results.append(v)
        for img in images:
            img["type"] = "image"
            results.append(img)

        return results

    async def search_for_project(
        self,
        project_id: str,
        orientation: str = "portrait",
    ) -> Dict:
        """
        为项目所有镜头搜索匹配素材

        读取metadata.json中每个shot的visual_description，搜索匹配素材

        Returns:
            {shots: [{shot_id, materials: [...]}], total_found}
        """
        import json
        from ..config import OUTPUTS_DIR

        project_dir = Path(OUTPUTS_DIR) / project_id
        metadata_path = project_dir / "metadata.json"

        if not metadata_path.exists():
            raise ValueError(f"项目不存在: {project_id}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        shots = metadata.get("shots", [])
        results = []
        total_found = 0

        for shot in shots:
            shot_id = shot.get("shot_id", shot.get("id", 0))
            visual_desc = shot.get("visual_description", "")

            if not visual_desc:
                results.append({"shot_id": shot_id, "materials": [], "query": ""})
                continue

            keywords = self._extract_keywords(visual_desc)
            materials = await self.search_pexels_videos(
                keywords, orientation, per_page=4, min_duration=3
            )

            # 也搜一些图片
            images = await self.search_pexels_images(keywords, orientation, per_page=2)
            for img in images:
                img["type"] = "image"
            for m in materials:
                m["type"] = "video"

            all_materials = materials + images
            total_found += len(all_materials)

            results.append({
                "shot_id": shot_id,
                "query": keywords,
                "visual_description": visual_desc[:100],
                "materials": all_materials,
            })

        return {
            "shots": results,
            "total_found": total_found,
        }

    async def download_material(self, url: str, save_dir: Optional[str] = None) -> str:
        """下载素材到本地缓存"""
        if not save_dir:
            save_dir = str(self._get_cache_dir())

        os.makedirs(save_dir, exist_ok=True)

        # 用URL的md5作为文件名避免重复下载
        url_clean = url.split("?")[0]
        url_hash = hashlib.md5(url_clean.encode()).hexdigest()[:12]
        ext = ".mp4" if "video" in url or url_clean.endswith(".mp4") else ".jpg"
        filename = f"mat-{url_hash}{ext}"
        filepath = os.path.join(save_dir, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filepath

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    logger.info(f"素材下载完成: {filepath} ({len(resp.content)} bytes)")
                    return filepath
        except Exception as e:
            logger.error(f"素材下载失败: {e}")

        return ""

    @staticmethod
    def _extract_keywords(visual_description: str) -> str:
        """从visual_description提取搜索关键词"""
        # 去掉常见的非搜索词
        stop_words = {
            "shot", "scene", "showing", "with", "the", "and", "for", "this",
            "that", "from", "into", "close", "wide", "medium", "angle",
            "camera", "lighting", "light", "dramatic", "natural", "soft",
            "bright", "clean", "professional", "studio", "background",
        }
        words = visual_description.lower().replace(",", " ").replace(".", " ").split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        # 取前5个有意义的词
        return " ".join(keywords[:5])

    @staticmethod
    def _pick_best_file(video_files: List[Dict], orientation: str) -> Optional[Dict]:
        """从Pexels视频文件列表中选最佳分辨率"""
        target_w, target_h = {
            "portrait": (1080, 1920),
            "landscape": (1920, 1080),
            "square": (1080, 1080),
        }.get(orientation, (1080, 1920))

        # 先找精确匹配
        for f in video_files:
            if int(f.get("width", 0)) == target_w and int(f.get("height", 0)) == target_h:
                return f

        # 找最接近的
        best = None
        best_diff = float("inf")
        for f in video_files:
            w = int(f.get("width", 0))
            h = int(f.get("height", 0))
            if w == 0 or h == 0:
                continue
            diff = abs(w - target_w) + abs(h - target_h)
            if diff < best_diff:
                best_diff = diff
                best = f

        return best
