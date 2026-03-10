# -*- coding: utf-8 -*-
"""
AI质量评分器 - 自动评估关键帧图片质量
"""
import asyncio
from typing import Dict, List, Optional
from loguru import logger


class AIScorer:
    """AI质量评分器 - 评估图片的质量、相关性、构图等"""

    def __init__(self):
        # TODO: 可以集成视觉模型API（如GPT-4 Vision, Claude Vision等）
        pass

    async def score_keyframe(
        self,
        image_url: str,
        prompt: str,
        shot_type: Optional[str] = None
    ) -> Dict[str, float]:
        """
        为单个关键帧评分

        Args:
            image_url: 图片URL
            prompt: 生成提示词
            shot_type: 分镜类型

        Returns:
            Dict包含各项评分:
            - overall_score: 总分 (0-100)
            - quality: 图片质量 (0-100)
            - relevance: 与提示词相关性 (0-100)
            - composition: 构图 (0-100)
            - lighting: 光照 (0-100)
            - color_harmony: 色彩和谐度 (0-100)
        """
        logger.info(f"开始评分关键帧: {image_url[:50]}...")

        try:
            # TODO: 实际实现需要调用视觉AI模型
            # 示例：使用GPT-4 Vision API分析图片

            # 占位评分（随机生成用于演示）
            import random

            scores = {
                "quality": random.uniform(70, 95),
                "relevance": random.uniform(75, 95),
                "composition": random.uniform(65, 90),
                "lighting": random.uniform(70, 95),
                "color_harmony": random.uniform(75, 92)
            }

            # 计算总分（加权平均）
            weights = {
                "quality": 0.25,
                "relevance": 0.30,
                "composition": 0.20,
                "lighting": 0.15,
                "color_harmony": 0.10
            }

            overall_score = sum(scores[k] * weights[k] for k in scores.keys())
            scores["overall_score"] = round(overall_score, 1)

            logger.info(f"评分完成: 总分 {scores['overall_score']:.1f}")
            return scores

        except Exception as e:
            logger.error(f"评分失败: {e}")
            # 返回默认分数
            return {
                "overall_score": 75.0,
                "quality": 75.0,
                "relevance": 75.0,
                "composition": 75.0,
                "lighting": 75.0,
                "color_harmony": 75.0
            }

    async def batch_score_keyframes(
        self,
        keyframes: List[Dict]
    ) -> List[Dict]:
        """
        批量评分多个关键帧

        Args:
            keyframes: 关键帧列表，每个包含 image_url, prompt等

        Returns:
            List[Dict]: 添加了scores字段的关键帧列表
        """
        logger.info(f"批量评分 {len(keyframes)} 个关键帧")

        tasks = []
        for kf in keyframes:
            task = self.score_keyframe(
                image_url=kf.get("image_url"),
                prompt=kf.get("prompt", ""),
                shot_type=kf.get("shot_type")
            )
            tasks.append(task)

        # 并发执行评分
        scores_list = await asyncio.gather(*tasks)

        # 添加评分到原数据
        for kf, scores in zip(keyframes, scores_list):
            kf["scores"] = scores
            kf["quality_score"] = scores["overall_score"]

        return keyframes

    async def compare_versions(
        self,
        versions: List[Dict]
    ) -> Dict:
        """
        对比多个版本，推荐最佳版本

        Args:
            versions: 版本列表，每个包含 version_id, image_url, scores等

        Returns:
            Dict包含:
            - recommended_version_id: 推荐的版本ID
            - reason: 推荐理由
            - comparison: 各版本对比
        """
        if not versions:
            return {"recommended_version_id": None, "reason": "无可用版本"}

        # 评分所有版本（如果还没评分）
        for v in versions:
            if "scores" not in v or not v["scores"]:
                v["scores"] = await self.score_keyframe(
                    v.get("image_url"),
                    v.get("prompt", "")
                )

        # 找出最高分版本
        best = max(versions, key=lambda x: x["scores"]["overall_score"])

        reason = f"版本{best['version_id']}得分最高 ({best['scores']['overall_score']:.1f}分)"

        # 构建对比数据
        comparison = []
        for v in versions:
            comparison.append({
                "version_id": v["version_id"],
                "overall_score": v["scores"]["overall_score"],
                "strengths": self._analyze_strengths(v["scores"]),
                "weaknesses": self._analyze_weaknesses(v["scores"])
            })

        return {
            "recommended_version_id": best["version_id"],
            "reason": reason,
            "comparison": comparison
        }

    def _analyze_strengths(self, scores: Dict[str, float]) -> List[str]:
        """分析优势"""
        strengths = []
        if scores.get("quality", 0) > 85:
            strengths.append("图片质量优秀")
        if scores.get("relevance", 0) > 85:
            strengths.append("高度契合提示词")
        if scores.get("composition", 0) > 85:
            strengths.append("构图专业")
        if scores.get("lighting", 0) > 85:
            strengths.append("光照出色")
        if scores.get("color_harmony", 0) > 85:
            strengths.append("色彩和谐")
        return strengths or ["整体表现良好"]

    def _analyze_weaknesses(self, scores: Dict[str, float]) -> List[str]:
        """分析不足"""
        weaknesses = []
        if scores.get("quality", 100) < 70:
            weaknesses.append("图片质量有待提升")
        if scores.get("relevance", 100) < 70:
            weaknesses.append("与提示词偏离")
        if scores.get("composition", 100) < 70:
            weaknesses.append("构图需要优化")
        if scores.get("lighting", 100) < 70:
            weaknesses.append("光照处理欠佳")
        if scores.get("color_harmony", 100) < 70:
            weaknesses.append("色彩搭配一般")
        return weaknesses

    async def suggest_improvements(
        self,
        prompt: str,
        scores: Dict[str, float]
    ) -> List[str]:
        """
        根据评分提供改进建议

        Args:
            prompt: 当前提示词
            scores: 评分结果

        Returns:
            List[str]: 改进建议列表
        """
        suggestions = []

        if scores.get("quality", 100) < 75:
            suggestions.append("添加'high quality', '4K'等质量关键词")

        if scores.get("relevance", 100) < 75:
            suggestions.append("提示词需要更具体和详细")

        if scores.get("composition", 100) < 75:
            suggestions.append("尝试添加'professional composition', 'rule of thirds'")

        if scores.get("lighting", 100) < 75:
            suggestions.append("指定光照类型，如'natural lighting', 'cinematic lighting'")

        if scores.get("color_harmony", 100) < 75:
            suggestions.append("添加色彩风格，如'warm tones', 'vibrant colors'")

        if not suggestions:
            suggestions.append("当前提示词效果良好，可以直接使用")

        return suggestions
