# -*- coding: utf-8 -*-
"""
羽翼Pro V2 - 数据模型
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class ShotType(Enum):
    """分镜类型"""
    TALKING_HEAD = "talking_head"  # 人物口播
    PRODUCT = "product"            # 产品展示
    SCENE = "scene"                # 环境场景
    HANDS_ON = "hands_on"          # 手部操作
    EFFECT = "effect"              # 效果展示
    TRANSITION = "transition"      # 过渡转场


class ActType(Enum):
    """三幕类型"""
    ACT1 = "act1"  # 冲突引入
    ACT2 = "act2"  # 深度展开
    ACT3 = "act3"  # 行动号召


@dataclass
class Shot:
    """单个分镜"""
    id: int
    shot_type: ShotType
    act_type: ActType
    visual_description: str  # 视觉描述
    narration: str           # 口播文案
    duration: float          # 时长(秒)
    emotion_score: float = 0.5  # 情绪值 0-1

    # AI生成相关
    assigned_model: Optional[str] = None  # 分配的模型
    model_reason: Optional[str] = None    # 选择原因
    estimated_cost: float = 0.0           # 预估成本

    # 生成结果
    task_id: Optional[str] = None
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    generation_success: bool = False
    generation_error: Optional[str] = None


@dataclass
class Act:
    """一幕"""
    act_type: ActType
    shots: List[Shot] = field(default_factory=list)
    total_duration: float = 0.0
    theme: str = ""

    def calculate_total_duration(self):
        """计算总时长"""
        self.total_duration = sum(shot.duration for shot in self.shots)
        return self.total_duration

    def get_shot_count(self) -> int:
        """获取分镜数"""
        return len(self.shots)


@dataclass
class VideoScript:
    """完整视频脚本"""
    title: str
    topic: str  # 主题/热点
    target_duration: int  # 目标时长(秒)
    acts: List[Act] = field(default_factory=list)

    # 元数据
    shot_count: int = 0
    total_duration: float = 0.0
    total_cost: float = 0.0

    # 爆款预测
    viral_score: float = 0.0
    viral_breakdown: Dict[str, float] = field(default_factory=dict)
    optimization_suggestions: List[str] = field(default_factory=list)

    def calculate_totals(self):
        """计算总数据"""
        all_shots = []
        for act in self.acts:
            act.calculate_total_duration()
            all_shots.extend(act.shots)

        self.shot_count = len(all_shots)
        self.total_duration = sum(act.total_duration for act in self.acts)
        self.total_cost = sum(shot.estimated_cost for shot in all_shots)

        return {
            "shot_count": self.shot_count,
            "total_duration": self.total_duration,
            "total_cost": self.total_cost,
        }

    def get_all_shots(self) -> List[Shot]:
        """获取所有分镜"""
        all_shots = []
        for act in self.acts:
            all_shots.extend(act.shots)
        return all_shots


@dataclass
class ModelRecommendation:
    """模型推荐结果"""
    model_id: str
    model_name: str
    confidence: float  # 推荐置信度 0-1
    reasons: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_quality: float = 0.0
    estimated_speed: float = 0.0


@dataclass
class CostOptimizationPlan:
    """成本优化方案"""
    original_cost: float
    optimized_cost: float
    savings: float
    savings_percentage: float
    quality_impact: str  # "无影响" / "轻微降低" / "明显降低"
    optimization_actions: List[Dict[str, Any]] = field(default_factory=list)
    # 每个action: {"shot_id": int, "original_model": str, "new_model": str, "reason": str}


@dataclass
class ViralPrediction:
    """爆款预测结果"""
    total_score: float  # 总分 0-100
    grade: str  # 等级: "excellent" / "good" / "average" / "poor"
    viral_probability: float  # 爆款概率 0-1

    # 各维度得分
    hook_strength: float = 0.0
    emotion_curve: float = 0.0
    visual_impact: float = 0.0
    info_density: float = 0.0
    cta_clarity: float = 0.0
    shareability: float = 0.0
    platform_fit: float = 0.0

    # 优化建议
    suggestions: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)


@dataclass
class GenerationTask:
    """视频生成任务"""
    task_id: str
    shot: Shot
    status: str = "pending"  # pending / submitted / processing / completed / failed
    submitted_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0


@dataclass
class ProductProfile:
    """产品档案"""
    name: str
    category: str
    selling_points: List[str]
    core_value: str
    target_audience: str
    tone: str = "专业"
    keywords: List[str] = field(default_factory=list)
