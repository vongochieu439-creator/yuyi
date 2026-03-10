# -*- coding: utf-8 -*-
"""
TikHub API客户端 - 搜索抖音热门视频和话题
"""
import httpx
from typing import List, Dict
from loguru import logger

from ..config import TIKHUB_API_KEY, TIKHUB_BASE_URL


class TikHubClient:
    """TikHub API客户端 - 获取抖音竞品视频数据"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or TIKHUB_API_KEY
        self.base_url = base_url or TIKHUB_BASE_URL

    async def search_videos(self, keyword: str, count: int = 20, sort_type: int = 0) -> List[Dict]:
        """
        搜索抖音视频 (使用POST搜索端点)

        Args:
            keyword: 搜索关键词
            count: 返回数量 (默认20)
            sort_type: 排序方式 (0=综合, 1=最多点赞, 2=最新发布)

        Returns:
            视频列表, 每项含 video_id, description, play_count, digg_count 等
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            # POST搜索端点要求字符串类型参数
            payload = {
                "keyword": keyword,
                "count": str(count),
                "sort_type": str(sort_type),
                "offset": "0"
            }

            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                resp = await client.post(
                    f"{self.base_url}/api/v1/douyin/search/fetch_video_search_v1",
                    headers=headers,
                    json=payload
                )

                if resp.status_code != 200:
                    logger.error(f"TikHub搜索失败: status={resp.status_code}, body={resp.text[:200]}")
                    return []

                data = resp.json()
                videos = self._parse_search_results(data)
                logger.info(f"TikHub搜索'{keyword}'返回{len(videos)}条视频")
                return videos

        except Exception as e:
            logger.error(f"TikHub搜索异常: {e}")
            return []

    async def get_hot_topics(self) -> List[Dict]:
        """
        获取抖音热搜榜

        Returns:
            热搜列表, 每项含 title, hot_value, position
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/douyin/app/v3/fetch_hot_search_list",
                    headers=headers,
                    params={}
                )

                if resp.status_code != 200:
                    logger.error(f"TikHub热搜失败: status={resp.status_code}")
                    return []

                data = resp.json()
                topics = self._parse_hot_topics(data)
                logger.info(f"TikHub热搜返回{len(topics)}条")
                return topics

        except Exception as e:
            logger.error(f"TikHub热搜异常: {e}")
            return []

    def _parse_search_results(self, data: dict) -> List[Dict]:
        """解析搜索结果"""
        videos = []
        try:
            # TikHub API 返回结构: data.data 或 data.aweme_list
            raw_list = []
            if isinstance(data, dict):
                if "data" in data and isinstance(data["data"], dict):
                    raw_list = data["data"].get("data", []) or data["data"].get("aweme_list", [])
                elif "data" in data and isinstance(data["data"], list):
                    raw_list = data["data"]

            for item in raw_list:
                # 提取aweme_info（如果嵌套）
                aweme = item.get("aweme_info", item)

                statistics = aweme.get("statistics", {})
                desc = aweme.get("desc", "")
                hashtags = []
                for tag in aweme.get("text_extra", []):
                    if tag.get("hashtag_name"):
                        hashtags.append(tag["hashtag_name"])

                videos.append({
                    "video_id": aweme.get("aweme_id", ""),
                    "description": desc,
                    "play_count": statistics.get("play_count", 0),
                    "digg_count": statistics.get("digg_count", 0),
                    "comment_count": statistics.get("comment_count", 0),
                    "share_count": statistics.get("share_count", 0),
                    "duration": aweme.get("duration", 0),
                    "hashtags": hashtags
                })
        except Exception as e:
            logger.error(f"解析TikHub搜索结果失败: {e}")

        return videos

    async def get_video_download_url(self, aweme_id: str) -> str:
        """
        获取视频无水印高清下载URL

        Args:
            aweme_id: 视频ID

        Returns:
            无水印高清视频URL
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            params = {"aweme_id": aweme_id}

            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/douyin/app/v3/fetch_video_high_quality_play_url",
                    headers=headers,
                    params=params
                )

                if resp.status_code != 200:
                    logger.error(f"TikHub获取视频URL失败: status={resp.status_code}, body={resp.text[:200]}")
                    return ""

                data = resp.json()
                # 提取视频URL
                video_data = data.get("data", {})
                if isinstance(video_data, dict):
                    url = video_data.get("original_video_url", "")
                    if not url:
                        # 备选字段
                        url = video_data.get("video_url", "")
                    if url:
                        logger.info(f"TikHub获取视频URL成功: aweme_id={aweme_id}")
                        return url

                logger.warning(f"TikHub视频URL为空: aweme_id={aweme_id}, resp={str(data)[:300]}")
                return ""

        except Exception as e:
            logger.error(f"TikHub获取视频URL异常: {e}")
            return ""

    async def get_video_comments(self, aweme_id: str, count: int = 50) -> List[Dict]:
        """
        获取视频评论（按点赞排序）

        Args:
            aweme_id: 视频ID
            count: 返回数量

        Returns:
            评论列表, 每项含 text, digg_count, user_nickname
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            params = {
                "aweme_id": aweme_id,
                "count": count,
                "cursor": 0
            }

            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/douyin/app/v3/fetch_video_comments",
                    headers=headers,
                    params=params
                )

                if resp.status_code != 200:
                    logger.error(f"TikHub获取评论失败: status={resp.status_code}")
                    return []

                data = resp.json()
                comments = self._parse_comments(data)
                # 按点赞数排序
                comments.sort(key=lambda x: x.get("digg_count", 0), reverse=True)
                logger.info(f"TikHub获取评论成功: aweme_id={aweme_id}, count={len(comments)}")
                return comments

        except Exception as e:
            logger.error(f"TikHub获取评论异常: {e}")
            return []

    async def get_video_detail(self, aweme_id: str) -> Dict:
        """
        获取单个视频详细信息

        Args:
            aweme_id: 视频ID

        Returns:
            视频详情: video_id, desc, author, digg_count, comment_count, play_count, cover_url, duration
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            params = {"aweme_id": aweme_id}

            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/douyin/web/fetch_one_video",
                    headers=headers,
                    params=params
                )

                if resp.status_code != 200:
                    logger.error(f"TikHub获取视频详情失败: status={resp.status_code}")
                    return {}

                data = resp.json()
                detail = self._parse_video_detail(data)
                if detail:
                    logger.info(f"TikHub获取视频详情成功: aweme_id={aweme_id}")
                return detail

        except Exception as e:
            logger.error(f"TikHub获取视频详情异常: {e}")
            return {}

    def _parse_comments(self, data: dict) -> List[Dict]:
        """解析评论结果"""
        comments = []
        try:
            raw_list = []
            if isinstance(data, dict):
                if "data" in data:
                    d = data["data"]
                    if isinstance(d, dict):
                        raw_list = d.get("comments", []) or d.get("data", [])
                    elif isinstance(d, list):
                        raw_list = d

            for item in raw_list:
                if not item:
                    continue
                user = item.get("user", {})
                comments.append({
                    "text": item.get("text", ""),
                    "digg_count": item.get("digg_count", 0),
                    "user_nickname": user.get("nickname", "匿名用户"),
                    "create_time": item.get("create_time", 0),
                })
        except Exception as e:
            logger.error(f"解析TikHub评论失败: {e}")

        return comments

    def _parse_video_detail(self, data: dict) -> Dict:
        """解析单个视频详情"""
        try:
            aweme = {}
            if isinstance(data, dict):
                if "data" in data:
                    d = data["data"]
                    if isinstance(d, dict):
                        aweme = d.get("aweme_detail", d)

            if not aweme:
                return {}

            statistics = aweme.get("statistics", {})
            author = aweme.get("author", {})

            # 封面URL
            cover = aweme.get("video", {}).get("cover", {}).get("url_list", [""])[0]
            if not cover:
                cover = aweme.get("video", {}).get("origin_cover", {}).get("url_list", [""])[0]

            return {
                "video_id": aweme.get("aweme_id", ""),
                "desc": aweme.get("desc", ""),
                "author": author.get("nickname", ""),
                "author_id": author.get("uid", ""),
                "digg_count": statistics.get("digg_count", 0),
                "comment_count": statistics.get("comment_count", 0),
                "play_count": statistics.get("play_count", 0),
                "share_count": statistics.get("share_count", 0),
                "cover_url": cover,
                "duration": aweme.get("duration", 0),
                "create_time": aweme.get("create_time", 0),
            }
        except Exception as e:
            logger.error(f"解析TikHub视频详情失败: {e}")
            return {}

    def _parse_hot_topics(self, data: dict) -> List[Dict]:
        """解析热搜结果"""
        topics = []
        try:
            raw_list = []
            if isinstance(data, dict):
                if "data" in data:
                    d = data["data"]
                    if isinstance(d, dict):
                        raw_list = d.get("word_list", []) or d.get("data", [])
                    elif isinstance(d, list):
                        raw_list = d

            for i, item in enumerate(raw_list):
                topics.append({
                    "title": item.get("word", item.get("title", "")),
                    "hot_value": item.get("hot_value", 0),
                    "position": i + 1
                })
        except Exception as e:
            logger.error(f"解析TikHub热搜结果失败: {e}")

        return topics

    async def search_xiaohongshu(self, keyword: str, count: int = 10) -> List[Dict]:
        """
        搜索小红书笔记

        Args:
            keyword: 搜索关键词
            count: 返回数量

        Returns:
            笔记列表, 每项含 title, desc, liked_count 等
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            params = {
                "keyword": keyword,
                "sort": "general",
                "page": "1",
            }

            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/xiaohongshu/web/search_notes",
                    headers=headers,
                    params=params
                )

                if resp.status_code != 200:
                    logger.error(f"TikHub小红书搜索失败: status={resp.status_code}")
                    return []

                data = resp.json()
                return self._parse_xhs_results(data, count)

        except Exception as e:
            logger.error(f"TikHub小红书搜索异常: {e}")
            return []

    def _parse_xhs_results(self, data: dict, max_count: int = 10) -> List[Dict]:
        """解析小红书搜索结果"""
        notes = []
        try:
            raw = data.get("data", {})
            if isinstance(raw, dict):
                items = raw.get("items", raw.get("data", []))
                if isinstance(items, dict):
                    items = list(items.values()) if items else []
            else:
                items = raw if isinstance(raw, list) else []

            for item in items[:max_count]:
                if not item:
                    continue
                note_card = item.get("note_card", item) if isinstance(item, dict) else {}
                interact_info = note_card.get("interact_info", {})
                user = note_card.get("user", {})
                notes.append({
                    "title": note_card.get("display_title", note_card.get("title", "")),
                    "desc": note_card.get("desc", "")[:200],
                    "liked_count": interact_info.get("liked_count", "0"),
                    "author": user.get("nickname", ""),
                    "type": note_card.get("type", "normal"),
                })
        except Exception as e:
            logger.error(f"解析小红书结果失败: {e}")

        return notes
