# -*- coding: utf-8 -*-
"""
性能和成本优化预设配置
提供不同场景下的最优配置方案
"""

from typing import Dict, List

# ==================== 优化预设 ====================

OPTIMIZATION_PRESETS = {
    # 超低成本模式 - 全部使用Kling (最便宜¥1.2)
    "ultra_low_cost": {
        "name": "超低成本模式",
        "description": "全部使用Kling v2.5 Turbo，成本最低，速度最快",
        "strategy": "cost_only",
        "force_model": "kling-v2.5-turbo",
        "quality_priority": False,
        "expected_cost_per_shot": 1.2,
        "expected_time_per_shot": 76,
        "best_for": ["大量分镜", "预算有限", "快速交付"],
        "trade_offs": ["质量中等（88分）", "不适合高端产品展示"]
    },

    # 速度优先模式 - 根据类型选择，优先Kling
    "speed_first": {
        "name": "速度优先模式",
        "description": "优先使用Kling，关键分镜用Grok",
        "strategy": "speed_priority",
        "model_rules": {
            "talking_head": "kling-v2.5-turbo",  # 人物口播
            "scene": "kling-v2.5-turbo",          # 场景
            "transition": "veo3.1-fast",          # 转场用最快的
            "hands_on": "kling-v2.5-turbo",       # 手部操作
            "product": "grok-video-3",            # 产品展示用高质量
            "effect": "grok-video-3"              # 效果展示用高质量
        },
        "quality_priority": False,
        "expected_cost_per_shot": 1.4,  # 平均成本
        "expected_time_per_shot": 85,   # 平均时间
        "best_for": ["时间紧迫", "中等预算", "需要一定质量"],
        "trade_offs": ["部分分镜质量中等"]
    },

    # 质量优先模式 - 关键分镜用Grok，其他用Kling
    "quality_first": {
        "name": "质量优先模式",
        "description": "关键分镜用Grok（高质量），其他用Kling（高性价比）",
        "strategy": "quality_priority",
        "model_rules": {
            "talking_head": "kling-v2.5-turbo",  # 口播不需要最高质量
            "scene": "kling-v2.5-turbo",          # 场景不需要最高质量
            "transition": "veo3.1-fast",          # 转场用最快的
            "hands_on": "grok-video-3",           # 手部操作需要高质量
            "product": "grok-video-3",            # 产品展示需要高质量
            "effect": "grok-video-3"              # 效果展示需要高质量
        },
        "quality_priority": True,
        "expected_cost_per_shot": 1.5,
        "expected_time_per_shot": 95,
        "best_for": ["品牌宣传", "产品发布", "高端营销"],
        "trade_offs": ["成本稍高", "生成时间稍长"]
    },

    # 平衡模式 - 智能分配，兼顾质量和成本
    "balanced": {
        "name": "平衡模式",
        "description": "根据分镜重要性智能分配，平衡质量、速度和成本",
        "strategy": "smart_allocation",
        "act_rules": {
            # 第一幕：开头要快速吸引，用快速模型
            "act1": {
                "preferred_models": ["veo3.1-fast", "kling-v2.5-turbo"],
                "quality_weight": 0.3,
                "speed_weight": 0.5,
                "cost_weight": 0.2
            },
            # 第二幕：深度展开，用高质量模型
            "act2": {
                "preferred_models": ["grok-video-3", "kling-v2.5-turbo"],
                "quality_weight": 0.6,
                "speed_weight": 0.2,
                "cost_weight": 0.2
            },
            # 第三幕：结尾冲刺，平衡质量和速度
            "act3": {
                "preferred_models": ["kling-v2.5-turbo", "veo3.1-fast"],
                "quality_weight": 0.4,
                "speed_weight": 0.4,
                "cost_weight": 0.2
            }
        },
        "quality_priority": True,
        "expected_cost_per_shot": 1.45,
        "expected_time_per_shot": 90,
        "best_for": ["大多数场景", "追求性价比", "标准营销视频"],
        "trade_offs": ["无明显缺点"]
    },

    # 极致质量模式 - 尽可能使用Grok
    "ultimate_quality": {
        "name": "极致质量模式",
        "description": "优先使用Grok Video 3，追求最高质量",
        "strategy": "quality_only",
        "force_model": "grok-video-3",
        "quality_priority": True,
        "expected_cost_per_shot": 1.8,
        "expected_time_per_shot": 120,
        "best_for": ["旗舰产品", "重要发布会", "品牌形象片"],
        "trade_offs": ["成本最高", "生成时间最长"]
    }
}


# ==================== 场景推荐 ====================

SCENARIO_RECOMMENDATIONS = {
    "short_video_tiktok": {
        "name": "抖音/快手短视频",
        "recommended_preset": "speed_first",
        "duration": 15-30,
        "shot_count": 5-8,
        "reason": "短视频节奏快，观众注意力短，速度优先即可"
    },

    "product_launch": {
        "name": "产品发布视频",
        "recommended_preset": "quality_first",
        "duration": 60-180,
        "shot_count": 15-30,
        "reason": "产品发布需要高质量展示，塑造品牌形象"
    },

    "brand_story": {
        "name": "品牌故事片",
        "recommended_preset": "ultimate_quality",
        "duration": 120-300,
        "shot_count": 25-50,
        "reason": "品牌形象片追求极致质量，成本可以更高"
    },

    "tutorial_education": {
        "name": "教程/教育视频",
        "recommended_preset": "balanced",
        "duration": 180-600,
        "shot_count": 30-80,
        "reason": "教育内容需要平衡质量和成本，内容为王"
    },

    "social_media_ad": {
        "name": "社交媒体广告",
        "recommended_preset": "speed_first",
        "duration": 15-60,
        "shot_count": 5-15,
        "reason": "社交媒体广告需要快速产出，A/B测试，速度优先"
    },

    "bulk_content": {
        "name": "批量内容生产",
        "recommended_preset": "ultra_low_cost",
        "duration": 30-120,
        "shot_count": "any",
        "reason": "批量生产追求成本和速度，质量要求适中"
    }
}


# ==================== 成本估算工具 ====================

def estimate_cost(shot_count: int, preset_name: str = "balanced") -> Dict:
    """
    估算总成本和时间

    Args:
        shot_count: 分镜数量
        preset_name: 预设名称

    Returns:
        成本和时间估算
    """
    preset = OPTIMIZATION_PRESETS.get(preset_name)
    if not preset:
        preset = OPTIMIZATION_PRESETS["balanced"]

    cost_per_shot = preset["expected_cost_per_shot"]
    time_per_shot = preset["expected_time_per_shot"]

    total_cost = shot_count * cost_per_shot
    total_time_seconds = time_per_shot  # 并发生成，时间约等于单个最慢的

    return {
        "preset": preset_name,
        "preset_name": preset["name"],
        "shot_count": shot_count,
        "total_cost": total_cost,
        "cost_per_shot": cost_per_shot,
        "estimated_time_seconds": total_time_seconds,
        "estimated_time_minutes": total_time_seconds / 60,
        "description": preset["description"],
        "best_for": preset["best_for"],
        "trade_offs": preset["trade_offs"]
    }


def compare_presets(shot_count: int) -> List[Dict]:
    """
    比较所有预设的成本和时间

    Args:
        shot_count: 分镜数量

    Returns:
        所有预设的对比数据
    """
    comparisons = []

    for preset_name in OPTIMIZATION_PRESETS.keys():
        estimate = estimate_cost(shot_count, preset_name)
        comparisons.append(estimate)

    # 按成本排序
    comparisons.sort(key=lambda x: x["total_cost"])

    return comparisons


def recommend_preset(
    shot_count: int,
    budget: float = None,
    time_limit_minutes: int = None,
    quality_requirement: str = "medium"  # low / medium / high / ultimate
) -> str:
    """
    根据需求推荐预设

    Args:
        shot_count: 分镜数量
        budget: 预算限制（元）
        time_limit_minutes: 时间限制（分钟）
        quality_requirement: 质量要求

    Returns:
        推荐的预设名称
    """
    # 如果有预算限制，优先考虑成本
    if budget is not None:
        for preset_name in ["ultra_low_cost", "speed_first", "balanced", "quality_first", "ultimate_quality"]:
            estimate = estimate_cost(shot_count, preset_name)
            if estimate["total_cost"] <= budget:
                return preset_name
        return "ultra_low_cost"  # 预算太低，只能用最便宜的

    # 如果有时间限制，优先考虑速度
    if time_limit_minutes is not None:
        for preset_name in ["speed_first", "ultra_low_cost", "balanced", "quality_first", "ultimate_quality"]:
            estimate = estimate_cost(shot_count, preset_name)
            if estimate["estimated_time_minutes"] <= time_limit_minutes:
                return preset_name
        return "speed_first"  # 时间太紧，只能用最快的

    # 根据质量要求推荐
    quality_map = {
        "low": "ultra_low_cost",
        "medium": "balanced",
        "high": "quality_first",
        "ultimate": "ultimate_quality"
    }

    return quality_map.get(quality_requirement, "balanced")


# 测试
if __name__ == "__main__":
    print("="*60)
    print("性能和成本优化预设")
    print("="*60)

    # 测试1: 比较所有预设（30个分镜）
    print("\n测试1: 30个分镜的成本对比")
    print("-"*60)
    comparisons = compare_presets(30)

    for comp in comparisons:
        print(f"\n{comp['preset_name']}")
        print(f"  总成本: ¥{comp['total_cost']:.2f}")
        print(f"  单镜成本: ¥{comp['cost_per_shot']:.2f}")
        print(f"  预计时间: {comp['estimated_time_minutes']:.1f}分钟")
        print(f"  适合: {', '.join(comp['best_for'][:2])}")

    # 测试2: 推荐预设
    print("\n\n测试2: 智能推荐")
    print("-"*60)

    scenarios = [
        {"shot_count": 30, "budget": 40, "time_limit_minutes": None, "quality_requirement": "medium"},
        {"shot_count": 50, "budget": None, "time_limit_minutes": 3, "quality_requirement": "high"},
        {"shot_count": 20, "budget": None, "time_limit_minutes": None, "quality_requirement": "ultimate"},
    ]

    for scenario in scenarios:
        recommended = recommend_preset(**scenario)
        estimate = estimate_cost(scenario["shot_count"], recommended)

        print(f"\n场景: {scenario['shot_count']}个分镜")
        if scenario["budget"]:
            print(f"  预算限制: ¥{scenario['budget']}")
        if scenario["time_limit_minutes"]:
            print(f"  时间限制: {scenario['time_limit_minutes']}分钟")
        print(f"  质量要求: {scenario['quality_requirement']}")
        print(f"  👉 推荐: {estimate['preset_name']}")
        print(f"  预估成本: ¥{estimate['total_cost']:.2f}")
        print(f"  预估时间: {estimate['estimated_time_minutes']:.1f}分钟")

    # 测试3: 场景推荐
    print("\n\n测试3: 不同场景推荐")
    print("-"*60)

    for scenario_key, scenario_info in SCENARIO_RECOMMENDATIONS.items():
        print(f"\n{scenario_info['name']}")
        print(f"  推荐预设: {scenario_info['recommended_preset']}")
        print(f"  时长: {scenario_info['duration']}秒")
        print(f"  理由: {scenario_info['reason']}")
