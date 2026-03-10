# -*- coding: utf-8 -*-
"""
智能模型调度引擎 - Remenbaike版本
基于Veo、Kling、Grok三个模型的智能调度
"""

import sys
from pathlib import Path
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Optional, Tuple
from loguru import logger

from models import Shot, ShotType, ActType, ModelRecommendation, CostOptimizationPlan
from config_remenbaike import VIDEO_MODELS, SHOT_TYPES


class RembaikeModelScheduler:
    """Remenbaike智能模型调度引擎"""

    def __init__(self):
        self.models = VIDEO_MODELS
        self.shot_types = SHOT_TYPES
        logger.info("🧠 Remenbaike智能模型调度引擎初始化完成")
        logger.info(f"   支持模型: {len(self.models)} 个 (Veo, Kling, Grok)")

    def recommend_model(
        self,
        shot: Shot,
        budget_constraint: Optional[float] = None,
        quality_priority: bool = True
    ) -> ModelRecommendation:
        """
        为单个分镜推荐最优模型

        Args:
            shot: 分镜对象
            budget_constraint: 预算约束(元)，None表示无约束
            quality_priority: 是否优先质量（False则优先速度）

        Returns:
            ModelRecommendation 模型推荐结果
        """
        shot_type = shot.shot_type.value
        act_type = shot.act_type.value

        logger.debug(f"[分镜{shot.id}] 分析: {shot_type}, 第{act_type}幕")

        # Step 1: 根据分镜类型筛选候选模型
        shot_config = self.shot_types.get(shot_type, {})
        typical_models = shot_config.get("typical_models", [])

        candidate_models = []
        for model_id, model_info in self.models.items():
            # 优先选择典型模型
            is_typical = model_id in typical_models
            # 检查是否擅长此类型
            is_best_for = shot_type in model_info.get("best_for", [])

            if is_typical or is_best_for:
                candidate_models.append({
                    "id": model_id,
                    "info": model_info,
                    "is_typical": is_typical,
                    "is_best_for": is_best_for,
                })

        # 如果没有候选模型，使用所有模型
        if not candidate_models:
            candidate_models = [
                {"id": mid, "info": minfo, "is_typical": False, "is_best_for": False}
                for mid, minfo in self.models.items()
            ]

        logger.debug(f"[分镜{shot.id}] 候选模型: {len(candidate_models)} 个")

        # Step 2: 根据预算筛选
        if budget_constraint is not None:
            candidate_models = [
                m for m in candidate_models
                if m["info"]["cost_per_video"] <= budget_constraint
            ]
            logger.debug(f"[分镜{shot.id}] 预算筛选后: {len(candidate_models)} 个")

        if not candidate_models:
            # 预算太低，选最便宜的
            cheapest = min(self.models.items(), key=lambda x: x[1]["cost_per_video"])
            logger.warning(f"[分镜{shot.id}] 预算不足，选择最便宜模型: {cheapest[0]}")
            return self._create_recommendation(
                cheapest[0],
                cheapest[1],
                confidence=0.5,
                reasons=["预算限制，选择最低成本模型"]
            )

        # Step 3: 评分排序
        scored_models = []
        for candidate in candidate_models:
            model_id = candidate["id"]
            model_info = candidate["info"]

            # 计算综合得分
            score = self._calculate_score(
                model_info,
                shot,
                candidate["is_typical"],
                candidate["is_best_for"],
                quality_priority
            )

            scored_models.append({
                "id": model_id,
                "info": model_info,
                "score": score,
                "is_typical": candidate["is_typical"],
                "is_best_for": candidate["is_best_for"],
            })

        # 按分数排序
        scored_models.sort(key=lambda x: x["score"], reverse=True)

        # 选择最高分
        best = scored_models[0]
        reasons = self._generate_reasons(best, shot, quality_priority)

        logger.debug(f"[分镜{shot.id}] 推荐: {best['id']} (分数: {best['score']:.2f})")

        return self._create_recommendation(
            best["id"],
            best["info"],
            confidence=min(best["score"] / 100, 1.0),
            reasons=reasons
        )

    def _calculate_score(
        self,
        model_info: Dict,
        shot: Shot,
        is_typical: bool,
        is_best_for: bool,
        quality_priority: bool
    ) -> float:
        """计算模型得分"""
        score = 0.0

        # 基础分：质量和速度
        if quality_priority:
            score += model_info["quality_score"] * 0.6  # 质量权重60%
            score += model_info["speed_score"] * 0.2    # 速度权重20%
        else:
            score += model_info["quality_score"] * 0.3  # 质量权重30%
            score += model_info["speed_score"] * 0.5    # 速度权重50%

        # 成本分（成本越低分数越高）
        max_cost = max(m["cost_per_video"] for m in self.models.values())
        cost_ratio = 1 - (model_info["cost_per_video"] / max_cost)
        score += cost_ratio * 20  # 成本权重20%

        # 匹配度加分
        if is_typical:
            score += 10  # 典型模型加10分
        if is_best_for:
            score += 15  # 最擅长的加15分

        # 幕类型调整
        act_type = shot.act_type.value
        if act_type == "act1":
            # 第一幕：更看重速度（开头要快速吸引）
            score += model_info["speed_score"] * 0.1
        elif act_type == "act2":
            # 第二幕：更看重质量（深度展开）
            score += model_info["quality_score"] * 0.1
        elif act_type == "act3":
            # 第三幕：平衡速度和冲击力
            score += (model_info["speed_score"] + model_info["quality_score"]) * 0.05

        return score

    def _generate_reasons(
        self,
        best_model: Dict,
        shot: Shot,
        quality_priority: bool
    ) -> List[str]:
        """生成推荐理由"""
        reasons = []
        model_info = best_model["info"]

        # 匹配度理由
        if best_model["is_best_for"]:
            reasons.append(f"最擅长{shot.shot_type.value}类型分镜")
        elif best_model["is_typical"]:
            reasons.append(f"典型适用于{shot.shot_type.value}类型")

        # 质量理由
        if model_info["quality_score"] >= 90:
            reasons.append("顶级质量 (90+分)")
        elif model_info["quality_score"] >= 85:
            reasons.append("高质量 (85+分)")

        # 速度理由
        if model_info["speed_score"] >= 95:
            reasons.append("超快速度 (76秒)")
        elif model_info["speed_score"] >= 85:
            reasons.append("快速生成 (120秒)")

        # 成本理由
        if model_info["cost_per_video"] <= 1.3:
            reasons.append("成本低廉 (¥1.2-1.3)")
        elif model_info["cost_per_video"] <= 1.6:
            reasons.append("性价比高")

        # 优先级理由
        if quality_priority:
            reasons.append("质量优先策略")
        else:
            reasons.append("速度优先策略")

        return reasons

    def _create_recommendation(
        self,
        model_id: str,
        model_info: Dict,
        confidence: float,
        reasons: List[str]
    ) -> ModelRecommendation:
        """创建推荐结果"""
        return ModelRecommendation(
            model_id=model_id,
            model_name=model_info["name"],
            confidence=confidence,
            reasons=reasons,
            estimated_cost=model_info["cost_per_video"],
            estimated_quality=model_info["quality_score"],
            estimated_speed=model_info["speed_score"]
        )

    def batch_assign_models(
        self,
        shots: List[Shot],
        total_budget: Optional[float] = None,
        quality_priority: bool = True
    ) -> Tuple[List[Shot], float]:
        """
        批量为所有分镜分配模型

        Args:
            shots: 分镜列表
            total_budget: 总预算(元)，None表示无约束
            quality_priority: 是否优先质量

        Returns:
            (分配后的分镜列表, 总成本)
        """
        total_shots = len(shots)
        logger.info(f"🎯 开始批量分配模型: {total_shots} 个分镜")

        # 计算单个分镜预算
        per_shot_budget = None
        if total_budget is not None:
            per_shot_budget = total_budget / total_shots
            logger.info(f"   总预算: ¥{total_budget:.2f}")
            logger.info(f"   单镜预算: ¥{per_shot_budget:.2f}")

        # 为每个分镜推荐模型
        total_cost = 0.0
        for shot in shots:
            recommendation = self.recommend_model(
                shot,
                budget_constraint=per_shot_budget,
                quality_priority=quality_priority
            )

            # 应用推荐
            shot.assigned_model = recommendation.model_id
            shot.model_reason = ", ".join(recommendation.reasons)
            shot.estimated_cost = recommendation.estimated_cost

            total_cost += recommendation.estimated_cost

            logger.debug(
                f"[分镜{shot.id}] {recommendation.model_name} "
                f"(¥{recommendation.estimated_cost:.2f}, "
                f"置信度: {recommendation.confidence:.0%})"
            )

        # 检查预算
        if total_budget is not None and total_cost > total_budget:
            logger.warning(f"⚠️  总成本 ¥{total_cost:.2f} 超出预算 ¥{total_budget:.2f}")
            # 执行成本优化
            shots, total_cost = self._optimize_cost(shots, total_budget)

        logger.info(f"✅ 模型分配完成")
        logger.info(f"   预估总成本: ¥{total_cost:.2f}")

        return shots, total_cost

    def _optimize_cost(
        self,
        shots: List[Shot],
        target_budget: float
    ) -> Tuple[List[Shot], float]:
        """成本优化：超预算时降级部分模型"""
        logger.info(f"🔧 执行成本优化...")

        current_cost = sum(s.estimated_cost for s in shots)
        need_to_save = current_cost - target_budget

        logger.info(f"   需要节省: ¥{need_to_save:.2f}")

        # 找到最便宜的模型
        cheapest_model_id = min(self.models.items(), key=lambda x: x[1]["cost_per_video"])[0]
        cheapest_cost = self.models[cheapest_model_id]["cost_per_video"]

        # 按成本排序分镜（成本高的优先降级）
        shots_by_cost = sorted(shots, key=lambda s: s.estimated_cost, reverse=True)

        saved = 0.0
        downgraded_count = 0

        for shot in shots_by_cost:
            if saved >= need_to_save:
                break

            # 如果已经是最便宜的模型，跳过
            if shot.assigned_model == cheapest_model_id:
                continue

            # 降级到最便宜模型
            old_cost = shot.estimated_cost
            shot.assigned_model = cheapest_model_id
            shot.estimated_cost = cheapest_cost
            shot.model_reason = f"成本优化降级: {shot.model_reason}"

            saved += (old_cost - cheapest_cost)
            downgraded_count += 1

            logger.debug(f"[分镜{shot.id}] 降级到 {cheapest_model_id} (节省 ¥{old_cost-cheapest_cost:.2f})")

        new_total_cost = sum(s.estimated_cost for s in shots)

        logger.info(f"✅ 优化完成:")
        logger.info(f"   降级分镜数: {downgraded_count}")
        logger.info(f"   节省金额: ¥{saved:.2f}")
        logger.info(f"   新总成本: ¥{new_total_cost:.2f}")

        return shots, new_total_cost

    def get_optimization_plan(
        self,
        shots: List[Shot],
        target_budget: float
    ) -> CostOptimizationPlan:
        """
        生成成本优化方案（不实际修改）

        Args:
            shots: 分镜列表
            target_budget: 目标预算

        Returns:
            优化方案
        """
        current_cost = sum(s.estimated_cost for s in shots)

        if current_cost <= target_budget:
            return CostOptimizationPlan(
                original_cost=current_cost,
                optimized_cost=current_cost,
                savings=0.0,
                savings_percentage=0.0,
                quality_impact="无影响",
                optimization_actions=[]
            )

        # 模拟优化
        test_shots = [Shot(
            id=s.id,
            shot_type=s.shot_type,
            act_type=s.act_type,
            visual_description=s.visual_description,
            narration=s.narration,
            duration=s.duration,
            assigned_model=s.assigned_model,
            estimated_cost=s.estimated_cost
        ) for s in shots]

        optimized_shots, optimized_cost = self._optimize_cost(test_shots, target_budget)

        # 记录变更
        actions = []
        for original, optimized in zip(shots, optimized_shots):
            if original.assigned_model != optimized.assigned_model:
                actions.append({
                    "shot_id": original.id,
                    "original_model": original.assigned_model,
                    "new_model": optimized.assigned_model,
                    "reason": "成本优化",
                    "cost_saved": original.estimated_cost - optimized.estimated_cost
                })

        savings = current_cost - optimized_cost
        savings_pct = (savings / current_cost) * 100

        # 评估质量影响
        if len(actions) == 0:
            quality_impact = "无影响"
        elif len(actions) / len(shots) < 0.3:
            quality_impact = "轻微降低"
        else:
            quality_impact = "明显降低"

        return CostOptimizationPlan(
            original_cost=current_cost,
            optimized_cost=optimized_cost,
            savings=savings,
            savings_percentage=savings_pct,
            quality_impact=quality_impact,
            optimization_actions=actions
        )


# 测试
if __name__ == "__main__":
    from models import Shot, ShotType, ActType

    scheduler = RembaikeModelScheduler()

    # 创建测试分镜
    test_shots = [
        Shot(1, ShotType.TALKING_HEAD, ActType.ACT1, "人物口播", "开场", 5.0),
        Shot(2, ShotType.SCENE, ActType.ACT1, "环境场景", "展示", 5.0),
        Shot(3, ShotType.PRODUCT, ActType.ACT2, "产品特写", "产品", 5.0),
        Shot(4, ShotType.HANDS_ON, ActType.ACT2, "手部操作", "操作", 5.0),
        Shot(5, ShotType.EFFECT, ActType.ACT2, "效果展示", "效果", 5.0),
        Shot(6, ShotType.TALKING_HEAD, ActType.ACT3, "结尾", "总结", 5.0),
    ]

    print("\n测试1: 质量优先，无预算限制")
    print("="*60)
    assigned_shots, total_cost = scheduler.batch_assign_models(
        test_shots,
        total_budget=None,
        quality_priority=True
    )

    for shot in assigned_shots:
        print(f"分镜{shot.id}: {shot.assigned_model} (¥{shot.estimated_cost:.2f})")
        print(f"  理由: {shot.model_reason}")

    print(f"\n总成本: ¥{total_cost:.2f}")

    print("\n\n测试2: 速度优先，预算¥8")
    print("="*60)
    test_shots2 = [
        Shot(i, ShotType.TALKING_HEAD, ActType.ACT1, "测试", "测试", 5.0)
        for i in range(1, 7)
    ]

    assigned_shots2, total_cost2 = scheduler.batch_assign_models(
        test_shots2,
        total_budget=8.0,
        quality_priority=False
    )

    for shot in assigned_shots2:
        print(f"分镜{shot.id}: {shot.assigned_model} (¥{shot.estimated_cost:.2f})")

    print(f"\n总成本: ¥{total_cost2:.2f}")

    print("\n\n测试3: 成本优化方案")
    print("="*60)
    plan = scheduler.get_optimization_plan(assigned_shots, target_budget=8.0)

    print(f"原始成本: ¥{plan.original_cost:.2f}")
    print(f"优化后: ¥{plan.optimized_cost:.2f}")
    print(f"节省: ¥{plan.savings:.2f} ({plan.savings_percentage:.1f}%)")
    print(f"质量影响: {plan.quality_impact}")
    print(f"\n优化动作:")
    for action in plan.optimization_actions:
        print(f"  分镜{action['shot_id']}: {action['original_model']} → {action['new_model']} (省¥{action['cost_saved']:.2f})")
