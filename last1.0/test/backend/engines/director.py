# -*- coding: utf-8 -*-
"""
超长视频导演系统
支持3-10分钟长视频的AI自动导演，三幕式结构，智能节奏控制
"""

import sys
from pathlib import Path
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Tuple, Optional
from loguru import logger
import math

from models import Shot, ShotType, ActType, Act, VideoScript, ProductProfile
from config import THREE_ACT_STRUCTURE, SHOT_TYPES, VIDEO_LENGTH_PRESETS


class Director:
    """超长视频导演系统"""

    def __init__(self):
        self.act_structure = THREE_ACT_STRUCTURE
        self.shot_types = SHOT_TYPES
        self.length_presets = VIDEO_LENGTH_PRESETS
        logger.info("🎬 超长视频导演系统初始化完成")

    def create_video_plan(
        self,
        topic: str,
        target_duration: int,
        product: Optional[ProductProfile] = None,
        style: str = "marketing"  # marketing / documentary / narrative
    ) -> Dict:
        """
        创建视频规划

        Args:
            topic: 主题/热点
            target_duration: 目标时长(秒) 60-600
            product: 产品信息(可选)
            style: 视频风格

        Returns:
            视频规划字典
        """
        logger.info(f"🎬 开始规划视频: {topic}")
        logger.info(f"   目标时长: {target_duration}秒 ({target_duration//60}分{target_duration%60}秒)")

        # Step 1: 确定视频长度类型
        length_type = self._determine_length_type(target_duration)
        logger.info(f"   长度类型: {self.length_presets[length_type]['name']}")

        # Step 2: 计算三幕时长和分镜数
        act_durations = self._calculate_act_durations(target_duration)
        act_shot_counts = self._calculate_act_shot_counts(target_duration, length_type)

        logger.info(f"   三幕时长: 第一幕{act_durations['act1']}s, 第二幕{act_durations['act2']}s, 第三幕{act_durations['act3']}s")
        logger.info(f"   三幕分镜数: 第一幕{act_shot_counts['act1']}个, 第二幕{act_shot_counts['act2']}个, 第三幕{act_shot_counts['act3']}个")

        # Step 3: 为每一幕分配分镜类型
        act_plans = {}
        for act_id in ["act1", "act2", "act3"]:
            act_config = self.act_structure[act_id]
            shot_count = act_shot_counts[act_id]
            duration = act_durations[act_id]

            act_plans[act_id] = self._plan_act(
                act_type=ActType[act_id.upper()],
                shot_count=shot_count,
                total_duration=duration,
                preferred_shot_types=act_config["shot_types"],
                emotion_curve=act_config["emotion_curve"],
                pace=act_config["pace"]
            )

        total_shots = sum(len(plan["shots"]) for plan in act_plans.values())

        return {
            "topic": topic,
            "target_duration": target_duration,
            "length_type": length_type,
            "total_shots": total_shots,
            "act_plans": act_plans,
            "style": style,
        }

    def generate_script_structure(
        self,
        video_plan: Dict,
        product: Optional[ProductProfile] = None
    ) -> VideoScript:
        """
        根据视频规划生成脚本结构

        Args:
            video_plan: 视频规划
            product: 产品信息

        Returns:
            VideoScript 脚本对象（框架，内容待填充）
        """
        logger.info(f"📝 生成脚本结构...")

        topic = video_plan["topic"]
        target_duration = video_plan["target_duration"]
        act_plans = video_plan["act_plans"]

        acts = []
        shot_id_counter = 1

        for act_id in ["act1", "act2", "act3"]:
            act_plan = act_plans[act_id]
            act_type = ActType[act_id.upper()]

            shots = []
            for shot_info in act_plan["shots"]:
                shot = Shot(
                    id=shot_id_counter,
                    shot_type=ShotType(shot_info["shot_type"]),
                    act_type=act_type,
                    visual_description=f"[待生成] {shot_info['shot_type']} 场景",
                    narration=f"[待生成] 第{shot_id_counter}镜文案",
                    duration=shot_info["duration"],
                    emotion_score=shot_info["emotion_score"]
                )
                shots.append(shot)
                shot_id_counter += 1

            act = Act(
                act_type=act_type,
                shots=shots,
                theme=self.act_structure[act_id]["name"]
            )
            acts.append(act)

        script = VideoScript(
            title=f"{topic} - AI生成视频",
            topic=topic,
            target_duration=target_duration,
            acts=acts
        )

        script.calculate_totals()

        logger.info(f"✅ 脚本结构生成完成:")
        logger.info(f"   总分镜数: {script.shot_count}")
        logger.info(f"   总时长: {script.total_duration:.1f}秒")

        return script

    def _determine_length_type(self, target_duration: int) -> str:
        """确定视频长度类型"""
        if target_duration <= 75:
            return "short"
        elif target_duration <= 150:
            return "medium"
        elif target_duration <= 240:
            return "long"
        else:
            return "ultra_long"

    def _calculate_act_durations(self, total_duration: int) -> Dict[str, int]:
        """计算每幕的时长"""
        act1_duration = int(total_duration * self.act_structure["act1"]["duration_ratio"])
        act2_duration = int(total_duration * self.act_structure["act2"]["duration_ratio"])
        act3_duration = total_duration - act1_duration - act2_duration  # 剩余时长给第三幕

        return {
            "act1": act1_duration,
            "act2": act2_duration,
            "act3": act3_duration,
        }

    def _calculate_act_shot_counts(self, total_duration: int, length_type: str) -> Dict[str, int]:
        """计算每幕的分镜数"""
        preset = self.length_presets[length_type]
        min_shots, max_shots = preset["shot_count_range"]

        # 根据时长估算总分镜数（平均每镜4-6秒）
        avg_duration_per_shot = 5
        estimated_total_shots = int(total_duration / avg_duration_per_shot)
        estimated_total_shots = max(min_shots, min(max_shots, estimated_total_shots))

        # 按比例分配
        act1_shots = int(estimated_total_shots * self.act_structure["act1"]["shot_count_ratio"])
        act2_shots = int(estimated_total_shots * self.act_structure["act2"]["shot_count_ratio"])
        act3_shots = estimated_total_shots - act1_shots - act2_shots

        # 确保每幕至少3个镜头
        act1_shots = max(3, act1_shots)
        act2_shots = max(3, act2_shots)
        act3_shots = max(3, act3_shots)

        return {
            "act1": act1_shots,
            "act2": act2_shots,
            "act3": act3_shots,
        }

    def _plan_act(
        self,
        act_type: ActType,
        shot_count: int,
        total_duration: float,
        preferred_shot_types: List[str],
        emotion_curve: List[float],
        pace: str
    ) -> Dict:
        """
        规划单幕内容

        Args:
            act_type: 幕类型
            shot_count: 分镜数
            total_duration: 总时长
            preferred_shot_types: 偏好的分镜类型
            emotion_curve: 情绪曲线
            pace: 节奏

        Returns:
            幕规划
        """
        shots_plan = []

        # 平均每镜时长
        avg_duration = total_duration / shot_count

        # 根据节奏调整时长变化
        if pace == "快速":
            duration_variation = 0.3  # 时长变化幅度
        elif pace == "稳定":
            duration_variation = 0.2
        else:
            duration_variation = 0.15

        # 分配分镜类型（轮换）
        shot_type_pool = preferred_shot_types * (shot_count // len(preferred_shot_types) + 1)

        # 生成情绪曲线（插值）
        emotions = self._interpolate_emotions(emotion_curve, shot_count)

        for i in range(shot_count):
            shot_type = shot_type_pool[i]

            # 计算时长（加入随机变化）
            duration_factor = 1.0 + ((i % 2) - 0.5) * duration_variation  # 交替长短
            duration = avg_duration * duration_factor

            # 限制在合理范围
            shot_config = self.shot_types.get(shot_type, {})
            min_dur, max_dur = shot_config.get("duration_range", (3, 8))
            duration = max(min_dur, min(max_dur, duration))

            shots_plan.append({
                "shot_type": shot_type,
                "duration": duration,
                "emotion_score": emotions[i]
            })

        # 调整总时长（微调最后几个镜头）
        actual_total = sum(s["duration"] for s in shots_plan)
        if abs(actual_total - total_duration) > 1:
            diff = total_duration - actual_total
            # 分配差异到最后3个镜头
            for i in range(min(3, shot_count)):
                shots_plan[-(i+1)]["duration"] += diff / 3

        return {
            "act_type": act_type.value,
            "shot_count": shot_count,
            "total_duration": total_duration,
            "shots": shots_plan
        }

    def _interpolate_emotions(self, curve_points: List[float], target_count: int) -> List[float]:
        """插值情绪曲线"""
        if len(curve_points) == target_count:
            return curve_points

        # 线性插值
        result = []
        step = (len(curve_points) - 1) / (target_count - 1)

        for i in range(target_count):
            index = i * step
            lower_idx = int(index)
            upper_idx = min(lower_idx + 1, len(curve_points) - 1)
            fraction = index - lower_idx

            value = curve_points[lower_idx] * (1 - fraction) + curve_points[upper_idx] * fraction
            result.append(value)

        return result

    def optimize_pacing(self, script: VideoScript) -> VideoScript:
        """
        优化节奏（自动调整分镜时长以达到最佳节奏）

        Args:
            script: 原始脚本

        Returns:
            优化后的脚本
        """
        logger.info("⚡ 优化视频节奏...")

        all_shots = script.get_all_shots()

        # 识别关键镜头（需要更多时长）
        key_shot_types = [ShotType.PRODUCT, ShotType.EFFECT]

        for shot in all_shots:
            # 关键镜头：延长10%
            if shot.shot_type in key_shot_types:
                shot.duration *= 1.1

            # 过渡镜头：缩短15%
            elif shot.shot_type == ShotType.TRANSITION:
                shot.duration *= 0.85

        # 重新计算总时长
        script.calculate_totals()

        logger.info(f"   优化后总时长: {script.total_duration:.1f}秒")

        return script


# 测试
if __name__ == "__main__":
    from models import ProductProfile

    director = Director()

    # 测试短视频（60秒）
    print("\n=== 测试60秒视频 ===")
    plan_60s = director.create_video_plan(
        topic="AI视频生成革命",
        target_duration=60,
        style="marketing"
    )
    script_60s = director.generate_script_structure(plan_60s)
    print(f"总分镜数: {script_60s.shot_count}")
    print(f"总时长: {script_60s.total_duration:.1f}秒")

    # 测试中等长度（2分钟）
    print("\n=== 测试120秒视频 ===")
    plan_120s = director.create_video_plan(
        topic="产品深度评测",
        target_duration=120,
    )
    script_120s = director.generate_script_structure(plan_120s)
    print(f"总分镜数: {script_120s.shot_count}")
    print(f"总时长: {script_120s.total_duration:.1f}秒")

    # 测试长视频（3分钟）
    print("\n=== 测试180秒视频 ===")
    plan_180s = director.create_video_plan(
        topic="完整故事叙事",
        target_duration=180,
    )
    script_180s = director.generate_script_structure(plan_180s)
    print(f"总分镜数: {script_180s.shot_count}")
    print(f"总时长: {script_180s.total_duration:.1f}秒")

    # 测试超长视频（5分钟）
    print("\n=== 测试300秒视频 ===")
    plan_300s = director.create_video_plan(
        topic="深度教程",
        target_duration=300,
    )
    script_300s = director.generate_script_structure(plan_300s)
    print(f"总分镜数: {script_300s.shot_count}")
    print(f"总时长: {script_300s.total_duration:.1f}秒")

    # 测试节奏优化
    print("\n=== 测试节奏优化 ===")
    optimized_script = director.optimize_pacing(script_180s)
    print(f"优化后时长: {optimized_script.total_duration:.1f}秒")
