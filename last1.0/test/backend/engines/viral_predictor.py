# -*- coding: utf-8 -*-
"""
爆款预测引擎
在生成前预测视频的传播潜力，并提供优化建议
"""

import sys
from pathlib import Path
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Tuple
from loguru import logger
import re

from models import Shot, VideoScript, ViralPrediction
from config import VIRAL_PREDICTION_WEIGHTS, VIRAL_SCORE_THRESHOLDS


class ViralPredictor:
    """爆款预测引擎"""

    def __init__(self):
        self.weights = VIRAL_PREDICTION_WEIGHTS
        self.thresholds = VIRAL_SCORE_THRESHOLDS
        logger.info("📊 爆款预测引擎初始化完成")

    def predict(self, script: VideoScript) -> ViralPrediction:
        """
        预测视频爆款潜力

        Args:
            script: 视频脚本

        Returns:
            ViralPrediction 预测结果
        """
        logger.info(f"🔮 开始预测爆款潜力: {script.title}")

        all_shots = script.get_all_shots()

        # 计算各维度得分
        hook_strength = self._analyze_hook_strength(all_shots)
        emotion_curve = self._analyze_emotion_curve(all_shots)
        visual_impact = self._analyze_visual_impact(all_shots)
        info_density = self._analyze_info_density(all_shots)
        cta_clarity = self._analyze_cta_clarity(all_shots)
        shareability = self._analyze_shareability(all_shots, script.topic)
        platform_fit = self._analyze_platform_fit(all_shots, script.target_duration)

        # 加权计算总分
        total_score = (
            hook_strength * self.weights["hook_strength"] +
            emotion_curve * self.weights["emotion_curve"] +
            visual_impact * self.weights["visual_impact"] +
            info_density * self.weights["info_density"] +
            cta_clarity * self.weights["cta_clarity"] +
            shareability * self.weights["shareability"] +
            platform_fit * self.weights["platform_fit"]
        ) * 100

        # 确定等级
        grade = self._get_grade(total_score)

        # 计算爆款概率
        viral_probability = self._calculate_viral_probability(total_score)

        logger.info(f"   总分: {total_score:.1f} ({grade})")
        logger.info(f"   爆款概率: {viral_probability:.1%}")

        # 生成优化建议
        suggestions, critical_issues = self._generate_suggestions(
            hook_strength, emotion_curve, visual_impact,
            info_density, cta_clarity, shareability, platform_fit,
            all_shots
        )

        return ViralPrediction(
            total_score=total_score,
            grade=grade,
            viral_probability=viral_probability,
            hook_strength=hook_strength,
            emotion_curve=emotion_curve,
            visual_impact=visual_impact,
            info_density=info_density,
            cta_clarity=cta_clarity,
            shareability=shareability,
            platform_fit=platform_fit,
            suggestions=suggestions,
            critical_issues=critical_issues,
        )

    def _analyze_hook_strength(self, shots: List[Shot]) -> float:
        """分析开头吸引力（前3秒）"""
        if not shots:
            return 0.0

        first_shot = shots[0]

        score = 0.5  # 基础分

        # 关键词检测
        hook_keywords = [
            "震惊", "必看", "揭秘", "秘密", "真相", "颠覆", "惊人",
            "不为人知", "千万别", "绝对", "一定要", "为什么", "如何",
            "教你", "亲测", "实测", "内幕", "曝光"
        ]

        narration = first_shot.narration
        visual = first_shot.visual_description

        # 检查口播文案
        hook_count = sum(1 for keyword in hook_keywords if keyword in narration)
        if hook_count > 0:
            score += 0.2

        # 冲突/疑问开头
        if any(punct in narration[:20] for punct in ["？", "?", "！", "!"]):
            score += 0.15

        # 视觉冲击
        impact_keywords = ["特写", "爆炸", "冲突", "对比", "震撼"]
        if any(keyword in visual for keyword in impact_keywords):
            score += 0.15

        return min(score, 1.0)

    def _analyze_emotion_curve(self, shots: List[Shot]) -> float:
        """分析情绪曲线（起承转合）"""
        if len(shots) < 4:
            return 0.5

        # 计算情绪变化
        emotions = [shot.emotion_score for shot in shots]

        # 理想情绪曲线：逐渐升高，有起伏
        # 检查是否有明显上升趋势
        avg_start = sum(emotions[:len(emotions)//3]) / (len(emotions)//3)
        avg_end = sum(emotions[-len(emotions)//3:]) / (len(emotions)//3)

        has_rise = avg_end > avg_start

        # 检查是否有起伏（不是一条直线）
        emotion_std = self._calculate_std(emotions)
        has_variation = emotion_std > 0.1

        # 检查是否有高潮（最高点在后半段）
        max_emotion = max(emotions)
        max_index = emotions.index(max_emotion)
        climax_in_later_half = max_index >= len(emotions) // 2

        score = 0.3
        if has_rise:
            score += 0.3
        if has_variation:
            score += 0.2
        if climax_in_later_half:
            score += 0.2

        return min(score, 1.0)

    def _analyze_visual_impact(self, shots: List[Shot]) -> float:
        """分析视觉冲击力"""
        if not shots:
            return 0.0

        # 统计高质量分镜占比
        high_quality_shots = [
            shot for shot in shots
            if shot.assigned_model and self._get_model_quality(shot.assigned_model) >= 90
        ]

        quality_ratio = len(high_quality_shots) / len(shots) if shots else 0

        # 检查视觉多样性（不同shot_type）
        shot_types = set(shot.shot_type for shot in shots)
        diversity_score = min(len(shot_types) / 5, 1.0)  # 最多5种类型

        # 综合评分
        score = quality_ratio * 0.6 + diversity_score * 0.4

        return score

    def _analyze_info_density(self, shots: List[Shot]) -> float:
        """分析信息密度"""
        if not shots:
            return 0.0

        # 计算平均每秒的信息量（字数）
        total_chars = sum(len(shot.narration) for shot in shots)
        total_duration = sum(shot.duration for shot in shots)

        if total_duration == 0:
            return 0.0

        chars_per_second = total_chars / total_duration

        # 理想范围：4-8字/秒
        if 4 <= chars_per_second <= 8:
            score = 1.0
        elif 3 <= chars_per_second < 4 or 8 < chars_per_second <= 10:
            score = 0.8
        elif 2 <= chars_per_second < 3 or 10 < chars_per_second <= 12:
            score = 0.6
        else:
            score = 0.4

        return score

    def _analyze_cta_clarity(self, shots: List[Shot]) -> float:
        """分析行动号召明确性"""
        if not shots:
            return 0.0

        last_shot = shots[-1]

        # CTA关键词
        cta_keywords = [
            "点赞", "关注", "评论", "分享", "转发", "收藏",
            "购买", "下单", "咨询", "联系", "扫码", "点击",
            "立即", "马上", "现在", "赶快"
        ]

        narration = last_shot.narration

        # 检查是否包含CTA
        cta_count = sum(1 for keyword in cta_keywords if keyword in narration)

        if cta_count >= 2:
            score = 1.0
        elif cta_count == 1:
            score = 0.7
        else:
            # 检查是否有疑问引导
            if "吗" in narration or "？" in narration:
                score = 0.5
            else:
                score = 0.3

        return score

    def _analyze_shareability(self, shots: List[Shot], topic: str) -> float:
        """分析传播意愿"""
        # 基于话题和内容类型判断
        shareable_topics = [
            "热点", "争议", "搞笑", "感动", "励志", "实用", "干货",
            "省钱", "赚钱", "健康", "教育", "美食", "旅游"
        ]

        score = 0.5

        # 检查话题
        if any(keyword in topic for keyword in shareable_topics):
            score += 0.2

        # 检查是否有争议点/讨论点
        all_narration = " ".join(shot.narration for shot in shots)
        controversial_keywords = ["但是", "然而", "其实", "真相", "不同", "对比"]
        if any(keyword in all_narration for keyword in controversial_keywords):
            score += 0.15

        # 检查是否有实用价值
        practical_keywords = ["方法", "技巧", "教程", "步骤", "如何", "怎么"]
        if any(keyword in all_narration for keyword in practical_keywords):
            score += 0.15

        return min(score, 1.0)

    def _analyze_platform_fit(self, shots: List[Shot], target_duration: int) -> float:
        """分析平台适配度（抖音/小红书）"""
        score = 0.5

        # 时长适配（抖音最佳：15-60秒，小红书最佳：30-90秒）
        if 15 <= target_duration <= 90:
            score += 0.3
        elif 10 <= target_duration < 15 or 90 < target_duration <= 120:
            score += 0.2
        else:
            score += 0.1

        # 竖屏优化（默认9:16，得分）
        score += 0.2

        return min(score, 1.0)

    def _get_grade(self, total_score: float) -> str:
        """获取等级"""
        if total_score >= self.thresholds["excellent"]:
            return "excellent"
        elif total_score >= self.thresholds["good"]:
            return "good"
        elif total_score >= self.thresholds["average"]:
            return "average"
        else:
            return "poor"

    def _calculate_viral_probability(self, total_score: float) -> float:
        """计算爆款概率"""
        # 使用Sigmoid函数映射
        # 90分 -> 80%, 80分 -> 50%, 70分 -> 20%
        if total_score >= 90:
            return 0.8 + (total_score - 90) * 0.02
        elif total_score >= 80:
            return 0.5 + (total_score - 80) * 0.03
        elif total_score >= 70:
            return 0.2 + (total_score - 70) * 0.03
        else:
            return max(0.05, total_score / 100 * 0.2)

    def _generate_suggestions(
        self,
        hook_strength: float,
        emotion_curve: float,
        visual_impact: float,
        info_density: float,
        cta_clarity: float,
        shareability: float,
        platform_fit: float,
        shots: List[Shot]
    ) -> Tuple[List[str], List[str]]:
        """生成优化建议"""
        suggestions = []
        critical_issues = []

        # 开头吸引力
        if hook_strength < 0.6:
            critical_issues.append("开头吸引力不足（前3秒）")
            suggestions.append("建议：开头使用冲突/疑问/震撼画面吸引注意力")
            suggestions.append("优化示例：'你知道吗？90%的人都不知道这个秘密' / '震惊！原来真相是这样的'")

        # 情绪曲线
        if emotion_curve < 0.6:
            suggestions.append("情绪曲线较平淡，建议增加起伏和高潮")
            suggestions.append("优化方法：在中后段设计情绪爆发点，营造惊喜/感动/共鸣")

        # 视觉冲击力
        if visual_impact < 0.7:
            suggestions.append("视觉冲击力可以加强")
            suggestions.append("建议：关键分镜使用高质量模型（veo3.1-pro / sora2-pro）")

        # 信息密度
        if info_density < 0.6:
            suggestions.append("信息密度需优化（建议4-8字/秒）")
            if info_density < 0.5:
                suggestions.append("当前可能过于冗长或过于简短，调整口播文案")

        # 行动号召
        if cta_clarity < 0.6:
            critical_issues.append("行动号召不明确")
            suggestions.append("建议：在结尾明确CTA，如'点赞+关注，下期更精彩' / '评论区告诉我你的看法'")

        # 传播性
        if shareability < 0.6:
            suggestions.append("传播潜力可提升")
            suggestions.append("建议：增加争议点、实用干货或情感共鸣点")

        # 平台适配
        if platform_fit < 0.7:
            suggestions.append("平台适配度可优化")
            total_duration = sum(shot.duration for shot in shots)
            if total_duration > 120:
                suggestions.append("时长偏长，建议控制在60-90秒内")
            elif total_duration < 15:
                suggestions.append("时长过短，建议扩展到30-60秒")

        return suggestions, critical_issues

    def _get_model_quality(self, model_id: str) -> float:
        """获取模型质量分数"""
        from config import VIDEO_MODELS
        return VIDEO_MODELS.get(model_id, {}).get("quality_score", 80)

    def _calculate_std(self, numbers: List[float]) -> float:
        """计算标准差"""
        if not numbers:
            return 0.0
        mean = sum(numbers) / len(numbers)
        variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
        return variance ** 0.5


# 测试
if __name__ == "__main__":
    from models import Shot, ShotType, ActType, Act, VideoScript

    predictor = ViralPredictor()

    # 创建测试脚本
    test_shots = [
        Shot(1, ShotType.TALKING_HEAD, ActType.ACT1, "震撼开场", "你知道吗？这个秘密90%的人都不知道！", 3.0, emotion_score=0.7),
        Shot(2, ShotType.SCENE, ActType.ACT1, "环境展示", "在这个快节奏的时代", 5.0, emotion_score=0.6),
        Shot(3, ShotType.PRODUCT, ActType.ACT2, "产品特写", "这就是我们的核心产品", 6.0, emotion_score=0.8),
        Shot(4, ShotType.HANDS_ON, ActType.ACT2, "使用演示", "使用非常简单", 5.0, emotion_score=0.85),
        Shot(5, ShotType.EFFECT, ActType.ACT2, "效果对比", "看看惊人的效果", 6.0, emotion_score=0.9),
        Shot(6, ShotType.TALKING_HEAD, ActType.ACT3, "行动号召", "点赞关注，下期更精彩！", 4.0, emotion_score=0.95),
    ]

    # 分配模型
    for shot in test_shots:
        shot.assigned_model = "sora2-new"

    # 创建脚本
    act1 = Act(ActType.ACT1, shots=[test_shots[0], test_shots[1]])
    act2 = Act(ActType.ACT2, shots=test_shots[2:5])
    act3 = Act(ActType.ACT3, shots=[test_shots[5]])

    script = VideoScript(
        title="测试视频",
        topic="产品营销",
        target_duration=30,
        acts=[act1, act2, act3]
    )

    # 预测
    prediction = predictor.predict(script)

    print(f"\n爆款预测结果:")
    print(f"总分: {prediction.total_score:.1f} ({prediction.grade})")
    print(f"爆款概率: {prediction.viral_probability:.1%}")
    print(f"\n各维度得分:")
    print(f"  开头吸引力: {prediction.hook_strength:.2f}")
    print(f"  情绪曲线: {prediction.emotion_curve:.2f}")
    print(f"  视觉冲击力: {prediction.visual_impact:.2f}")
    print(f"  信息密度: {prediction.info_density:.2f}")
    print(f"  行动号召: {prediction.cta_clarity:.2f}")
    print(f"  传播性: {prediction.shareability:.2f}")
    print(f"  平台适配: {prediction.platform_fit:.2f}")
    print(f"\n优化建议:")
    for suggestion in prediction.suggestions:
        print(f"  - {suggestion}")
    if prediction.critical_issues:
        print(f"\n严重问题:")
        for issue in prediction.critical_issues:
            print(f"  ⚠️  {issue}")
