# -*- coding: utf-8 -*-
"""
视频深度分析器 - 单个视频的完整分析pipeline

整合TikHub(视频数据) + 阿里云ASR(语音转文字) + Gemini(视频理解)
对单个抖音视频进行三层并行分析:
1. 口播原文 (ASR)
2. 画面理解 (Gemini多模态)
3. 评论数据 (TikHub)
"""
import asyncio
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Callable, Awaitable
from loguru import logger

from .tikhub_client import TikHubClient
from .aliyun_asr_client import AliyunASRClient
from .gemini_client import GeminiClient


@dataclass
class VideoAnalysis:
    """单个视频的完整分析结果"""
    aweme_id: str = ""
    title: str = ""
    author: str = ""
    play_count: int = 0
    digg_count: int = 0
    comment_count: int = 0
    duration: int = 0
    cover_url: str = ""

    # 三层分析
    asr_text: str = ""              # 口播原文
    visual_analysis: str = ""       # 画面理解
    comments: List[Dict] = field(default_factory=list)

    # 综合深度分析
    deep_analysis: str = ""
    structured_analysis: Dict = field(default_factory=dict)  # structured JSON

    # Legacy fields for backward compat
    structure_analysis: str = ""    # 叙事结构
    creative_device: str = ""       # 创意装置
    speaking_style: str = ""        # 口播风格
    selling_method: str = ""        # 卖点植入方式
    success_factors: str = ""       # 成功核心

    def to_dict(self) -> dict:
        return asdict(self)


# 视频拆解Prompt
VIDEO_ANALYSIS_PROMPT = """你是抖音爆款内容分析专家。请结合视频画面进行深度结构化分析。

直接输出JSON，不要其他文字:
{
  "hook": {
    "type": "钩子类型（反常识/争议/悬念/痛点/视觉冲击/利益承诺）",
    "text": "原文开头第一句话",
    "mechanism": "为什么这个开头能留住人（一句话）"
  },
  "tension_beats": [
    {"time_range": "0-3s", "device": "用了什么手法", "function": "在叙事中的作用"},
    {"time_range": "3-8s", "device": "...", "function": "..."}
  ],
  "selling_point_insertion": {
    "method": "卖点植入方式（实验结果/使用演示/对比/口播/道具）",
    "timing": "在什么时刻植入",
    "naturalness": "植入自然度评分1-10"
  },
  "emotional_arc": ["情绪1", "情绪2", "情绪3", "情绪4"],
  "creative_device": {
    "type": "创意装置类型（实验对比/反转剧情/极致测试/街头互动/科普可视化/生活反差）",
    "description": "具体怎么实现的",
    "transferable_formula": "可迁移的公式：[X] x [Y] → [Z]"
  },
  "speaking_style": {
    "tone": "语气特点",
    "oral_fragments": ["口语碎片举例1", "口语碎片举例2"],
    "rhythm": "快/慢/快慢交替/渐进"
  },
  "success_core": "一句话总结为什么能爆"
}"""

DEEP_SYNTHESIS_PROMPT = """你是抖音爆款内容分析专家。以下是一个视频的三层数据:

## 口播原文
{asr_text}

## 画面分析
{visual_analysis}

## 评论区TOP热评（按点赞排序）
{comments_text}

## 视频基本信息
标题: {title}
播放量: {play_count}
点赞量: {digg_count}
时长: {duration}秒

---

请输出完整的结构化视频拆解，直接输出JSON，不要其他文字:
{{
  "hook": {{
    "type": "钩子类型",
    "text": "原文开头第一句",
    "mechanism": "留人原理"
  }},
  "tension_beats": [
    {{"time_range": "0-3s", "device": "手法", "function": "作用"}}
  ],
  "selling_point_insertion": {{
    "method": "植入方式",
    "timing": "植入时刻",
    "naturalness": 8
  }},
  "emotional_arc": ["情绪1", "情绪2", "情绪3"],
  "creative_device": {{
    "type": "创意装置类型",
    "description": "具体实现",
    "transferable_formula": "[X] x [Y] → [Z]"
  }},
  "speaking_style": {{
    "tone": "语气",
    "oral_fragments": ["碎片1", "碎片2"],
    "rhythm": "节奏"
  }},
  "comment_insights": {{
    "top_concerns": ["观众最关心的问题1", "问题2"],
    "emotional_triggers": ["引发强烈反应的点1"],
    "controversy": "最具争议性的话题（如有）"
  }},
  "success_core": "一句话总结"
}}"""


class VideoAnalyzer:
    """视频深度分析器"""

    def __init__(self):
        self.tikhub = TikHubClient()
        self.asr = AliyunASRClient()
        self.gemini = GeminiClient()

    async def analyze_video(
        self,
        aweme_id: str,
        on_progress: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> VideoAnalysis:
        """
        对单个视频进行完整的深度分析

        Args:
            aweme_id: 抖音视频ID
            on_progress: 进度回调函数

        Returns:
            VideoAnalysis 完整分析结果
        """
        analysis = VideoAnalysis(aweme_id=aweme_id)

        # Step 1: 获取视频基本信息
        if on_progress:
            await on_progress(f"获取视频信息: {aweme_id}")

        detail = await self.tikhub.get_video_detail(aweme_id)
        if detail:
            analysis.title = detail.get("desc", "")
            analysis.author = detail.get("author", "")
            analysis.play_count = detail.get("play_count", 0)
            analysis.digg_count = detail.get("digg_count", 0)
            analysis.comment_count = detail.get("comment_count", 0)
            analysis.duration = detail.get("duration", 0)
            analysis.cover_url = detail.get("cover_url", "")

        # Step 2: 获取视频下载URL
        if on_progress:
            await on_progress(f"获取视频下载链接: {aweme_id}")

        video_url = await self.tikhub.get_video_download_url(aweme_id)

        # Step 3: 并行三层分析
        if on_progress:
            await on_progress(f"并行分析中(ASR+Gemini+评论): {aweme_id}")

        tasks = []

        # ASR转写
        if video_url:
            tasks.append(self._safe_asr(video_url))
        else:
            tasks.append(self._return_empty("无法获取视频URL，跳过ASR"))

        # Gemini视频理解
        if video_url:
            asr_hint = f"视频标题: {analysis.title}" if analysis.title else ""
            prompt = VIDEO_ANALYSIS_PROMPT
            if asr_hint:
                prompt = f"{asr_hint}\n\n{prompt}"
            tasks.append(self._safe_gemini_video(video_url, prompt))
        else:
            tasks.append(self._return_empty("无法获取视频URL，跳过画面分析"))

        # 评论获取
        tasks.append(self._safe_comments(aweme_id))

        results = await asyncio.gather(*tasks)
        analysis.asr_text = results[0]
        analysis.visual_analysis = results[1]
        analysis.comments = results[2]

        # Step 4: 综合三层数据生成深度分析
        if on_progress:
            await on_progress(f"生成深度分析: {aweme_id}")

        # 仅当至少有一层数据时才做综合分析
        has_data = analysis.asr_text or analysis.visual_analysis or analysis.comments
        if has_data:
            analysis.deep_analysis = await self._synthesize(analysis)

        logger.info(
            f"视频分析完成: {aweme_id}, "
            f"ASR={len(analysis.asr_text)}字, "
            f"视觉={len(analysis.visual_analysis)}字, "
            f"评论={len(analysis.comments)}条"
        )

        return analysis

    async def analyze_videos_batch(
        self,
        aweme_ids: List[str],
        on_progress: Optional[Callable[[str], Awaitable[None]]] = None,
        max_concurrent: int = 2,
    ) -> List[VideoAnalysis]:
        """
        批量分析多个视频（控制并发）

        Args:
            aweme_ids: 视频ID列表
            on_progress: 进度回调
            max_concurrent: 最大并发数

        Returns:
            VideoAnalysis列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def analyze_one(aid: str) -> VideoAnalysis:
            async with semaphore:
                return await self.analyze_video(aid, on_progress)

        tasks = [analyze_one(aid) for aid in aweme_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤失败的
        valid = []
        for r in results:
            if isinstance(r, VideoAnalysis):
                valid.append(r)
            else:
                logger.error(f"视频分析失败: {r}")
        return valid

    async def _safe_asr(self, video_url: str) -> str:
        """安全的ASR调用，失败返回空字符串"""
        try:
            return await self.asr.transcribe_from_url(video_url)
        except Exception as e:
            logger.error(f"ASR转写失败: {e}")
            return ""

    async def _safe_gemini_video(self, video_url: str, prompt: str) -> str:
        """安全的Gemini视频分析，失败返回空字符串"""
        try:
            return await self.gemini.understand_video(video_url, prompt)
        except Exception as e:
            logger.error(f"Gemini视频分析失败: {e}")
            return ""

    async def _safe_comments(self, aweme_id: str) -> List[Dict]:
        """安全的评论获取，失败返回空列表"""
        try:
            return await self.tikhub.get_video_comments(aweme_id, count=50)
        except Exception as e:
            logger.error(f"获取评论失败: {e}")
            return []

    async def _return_empty(self, reason: str) -> str:
        """返回空字符串并记录原因"""
        logger.warning(reason)
        return ""

    def _parse_structured_analysis(self, text: str) -> Dict:
        """尝试从Gemini响应中解析结构化分析JSON"""
        import json
        text = text.strip()
        # Handle markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1].strip()
        # Find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning("结构化分析JSON解析失败，返回空dict")
        return {}

    async def _synthesize(self, analysis: VideoAnalysis) -> str:
        """综合三层数据生成深度分析"""
        # 格式化评论
        comments_text = ""
        if analysis.comments:
            top_comments = analysis.comments[:20]  # 取TOP20
            for i, c in enumerate(top_comments, 1):
                comments_text += f"{i}. [{c.get('digg_count', 0)}赞] {c.get('text', '')}\n"
        else:
            comments_text = "（无评论数据）"

        prompt = DEEP_SYNTHESIS_PROMPT.format(
            asr_text=analysis.asr_text or "（无口播转写数据）",
            visual_analysis=analysis.visual_analysis or "（无画面分析数据）",
            comments_text=comments_text,
            title=analysis.title,
            play_count=analysis.play_count,
            digg_count=analysis.digg_count,
            duration=analysis.duration // 1000 if analysis.duration > 1000 else analysis.duration,
        )

        try:
            result = await self.gemini.generate(prompt, max_tokens=4096)
            analysis.deep_analysis = result  # keep raw text
            analysis.structured_analysis = self._parse_structured_analysis(result)
            return result
        except Exception as e:
            logger.error(f"综合分析生成失败: {e}")
            return ""
