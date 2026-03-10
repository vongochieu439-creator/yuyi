# -*- coding: utf-8 -*-
"""
智能模型调度引擎
根据分镜类型、预算、质量要求自动选择最优视频生成模型
"""

import sys
from pathlib import Path
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Optional, Tuple
from loguru import logger

from models import Shot, ShotType, ActType, ModelRecommendation, CostOptimizationPlan
from config import VIDEO_MODELS, SHOT_TYPES


class ModelScheduler:
    """智能模型调度引擎"""

    def __init__(self):
        self.models = VIDEO_MODELS
        self.shot_types = SHOT_TYPES
        logger.info("🧠 智能模型调度引擎初始化完成")
        logger.info(f"   支持模型: {len(self.models)} 个")

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

            score = self._calculate_model_score(
                model_info=model_info,
                shot_type=shot_type,
                act_type=act_type,
                is_typical=candidate["is_typical"],
                is_best_for=candidate["is_best_for"],
                quality_priority=quality_priority
            )

            scored_models.append({
                "id": model_id,
                "info": model_info,
                "score": score,
                "is_typical": candidate["is_typical"],
                "is_best_for": candidate["is_best_for"],
            })

        # 按得分排序
        scored_models.sort(key=lambda x: x["score"], reverse=True)
        best_model = scored_models[0]

        logger.debug(f"[分镜{shot.id}] 最佳模型: {best_model['id']} (得分: {best_model['score']:.2f})")

        # 生成推荐原因
        reasons = self._generate_reasons(
            best_model["id"],
            best_model["info"],
            shot_type,
            best_model["is_typical"],
            best_model["is_best_for"],
            quality_priority
        )

        return self._create_recommendation(
            best_model["id"],
            best_model["info"],
            confidence=min(best_model["score"] / 100, 1.0),
            reasons=reasons
        )

    def _calculate_model_score(
        self,
        model_info: Dict,
        shot_type: str,
        act_type: str,
        is_typical: bool,
        is_best_for: bool,
        quality_priority: bool
    ) -> float:
        """计算模型得分"""
        score = 0.0

        # 1. 类型匹配度 (30分)
        if is_best_for:
            score += 30
        elif is_typical:
            score += 20

        # 2. 质量得分 (40分)
        quality_score = model_info.get("quality_score", 80)
        if quality_priority:
            score += (quality_score / 100) * 40
        else:
            score += (quality_score / 100) * 20

        # 3. 速度得分 (20分)
        speed_score = model_info.get("speed_score", 70)
        if not quality_priority:
            score += (speed_score / 100) * 40
        else:
            score += (speed_score / 100) * 20

        # 4. 性价比 (10分)
        cost = model_info.get("cost_per_video", 2.0)
        cost_efficiency = (5.0 - cost) / 5.0  # 成本越低越好
        score += max(0, cost_efficiency) * 10

        return score

    def _generate_reasons(
        self,
        model_id: str,
        model_info: Dict,
        shot_type: str,
        is_typical: bool,
        is_best_for: bool,
        quality_priority: bool
    ) -> List[str]:
        """生成推荐原因"""
        reasons = []

        if is_best_for:
            reasons.append(f"最擅长 {shot_type} 类型分镜")

        if is_typical:
            reasons.append(f"推荐用于 {shot_type} 场景")

        strengths = model_info.get("strengths", [])
        if strengths:
            reasons.append(f"优势: {', '.join(strengths[:2])}")

        quality = model_info.get("quality_score", 80)
        if quality >= 90:
            reasons.append(f"顶级画质 ({quality}分)")
        elif quality >= 85:
            reasons.append(f"优质画面 ({quality}分)")

        cost = model_info.get("cost_per_video", 2.0)
        if cost <= 1.5:
            reasons.append(f"性价比高 (¥{cost}/片)")
        elif cost >= 3.0:
            reasons.append(f"高端模型 (¥{cost}/片)")

        return reasons

    def _create_recommendation(
        self,
        model_id: str,
        model_info: Dict,
        confidence: float,
        reasons: List[str]
    ) -> ModelRecommendation:
        """创建推荐对象"""
        return ModelRecommendation(
            model_id=model_id,
            model_name=model_info["name"],
            confidence=confidence,
            reasons=reasons,
            estimated_cost=model_info["cost_per_video"],
            estimated_quality=model_info.get("quality_score", 80) / 100,
            estimated_speed=model_info.get("speed_score", 70) / 100,
        )

    def optimize_cost(
        self,
        shots: List[Shot],
        budget: float,
        min_quality_score: float = 0.8
    ) -> CostOptimizationPlan:
        """
        成本优化：在预算内最大化质量

        Args:
            shots: 分镜列表
            budget: 总预算(元)
            min_quality_score: 最低质量要求 (0-1)

        Returns:
            CostOptimizationPlan 优化方案
        """
        logger.info(f"💰 成本优化: 预算={budget}元, 最低质量={min_quality_score}")

        # Step 1: 计算原始成本
        original_cost = sum(shot.estimated_cost for shot in shots)
        logger.info(f"   原始成本: {original_cost:.2f}元")

        if original_cost <= budget:
            logger.info("   预算充足，无需优化")
            return CostOptimizationPlan(
                original_cost=original_cost,
                optimized_cost=original_cost,
                savings=0,
                savings_percentage=0,
                quality_impact="无影响",
            )

        # Step 2: 识别可优化的分镜（非关键分镜）
        # 关键分镜：产品展示、效果展示
        critical_shot_types = [ShotType.PRODUCT, ShotType.EFFECT]

        optimizable_shots = []
        for shot in shots:
            if shot.shot_type not in critical_shot_types:
                optimizable_shots.append(shot)

        logger.info(f"   可优化分镜: {len(optimizable_shots)}/{len(shots)}")

        # Step 3: 降级策略
        actions = []
        total_savings = 0

        for shot in optimizable_shots:
            current_model_id = shot.assigned_model
            current_cost = shot.estimated_cost

            # 查找更便宜的替代模型
            cheaper_alternatives = []
            for model_id, model_info in self.models.items():
                if model_info["cost_per_video"] < current_cost:
                    quality_score = model_info.get("quality_score", 80) / 100
                    if quality_score >= min_quality_score:
                        cheaper_alternatives.append({
                            "id": model_id,
                            "cost": model_info["cost_per_video"],
                            "quality": quality_score,
                        })

            if cheaper_alternatives:
                # 选择质量最高的便宜替代
                cheaper_alternatives.sort(key=lambda x: x["quality"], reverse=True)
                best_alternative = cheaper_alternatives[0]

                saving = current_cost - best_alternative["cost"]
                total_savings += saving

                actions.append({
                    "shot_id": shot.id,
                    "original_model": current_model_id,
                    "new_model": best_alternative["id"],
                    "saving": saving,
                    "reason": f"替换为性价比更高的模型，节省¥{saving:.2f}",
                })

                # 更新分镜
                shot.assigned_model = best_alternative["id"]
                shot.estimated_cost = best_alternative["cost"]

                logger.debug(f"   [分镜{shot.id}] {current_model_id} → {best_alternative['id']}, 节省¥{saving:.2f}")

                # 检查是否达到预算
                if original_cost - total_savings <= budget:
                    break

        # Step 4: 生成优化方案
        optimized_cost = original_cost - total_savings
        savings_pct = (total_savings / original_cost * 100) if original_cost > 0 else 0

        quality_impact = "无影响" if savings_pct < 10 else ("轻微降低" if savings_pct < 20 else "明显降低")

        logger.info(f"   优化后成本: {optimized_cost:.2f}元")
        logger.info(f"   节省: {total_savings:.2f}元 ({savings_pct:.1f}%)")

        return CostOptimizationPlan(
            original_cost=original_cost,
            optimized_cost=optimized_cost,
            savings=total_savings,
            savings_percentage=savings_pct,
            quality_impact=quality_impact,
            optimization_actions=actions,
        )

    def batch_assign_models(
        self,
        shots: List[Shot],
        budget_per_shot: Optional[float] = None,
        total_budget: Optional[float] = None,
        quality_priority: bool = True
    ) -> Tuple[List[Shot], float]:
        """
        批量为分镜分配模型

        Args:
            shots: 分镜列表
            budget_per_shot: 单个分镜预算
            total_budget: 总预算
            quality_priority: 是否优先质量

        Returns:
            (更新后的shots, 总成本)
        """
        logger.info(f"🎯 批量分配模型: {len(shots)} 个分镜")

        # Step 1: 为每个分镜推荐模型
        for shot in shots:
            recommendation = self.recommend_model(
                shot=shot,
                budget_constraint=budget_per_shot,
                quality_priority=quality_priority
            )

            shot.assigned_model = recommendation.model_id
            shot.model_reason = "; ".join(recommendation.reasons)
            shot.estimated_cost = recommendation.estimated_cost

            logger.debug(f"[分镜{shot.id}] → {recommendation.model_name} (¥{recommendation.estimated_cost})")

        # Step 2: 计算总成本
        total_cost = sum(shot.estimated_cost for shot in shots)
        logger.info(f"   预估总成本: {total_cost:.2f}元")

        # Step 3: 如果超预算，优化成本
        if total_budget is not None and total_cost > total_budget:
            logger.warning(f"   超出预算! 开始优化...")
            optimization = self.optimize_cost(shots, total_budget)
            total_cost = optimization.optimized_cost
            logger.info(f"   优化后成本: {total_cost:.2f}元 (节省{optimization.savings:.2f}元)")

        return shots, total_cost


# 测试
if __name__ == "__main__":
    from models import Shot, ShotType, ActType

    scheduler = ModelScheduler()

    # 测试单个推荐
    test_shot = Shot(
        id=1,
        shot_type=ShotType.PRODUCT,
        act_type=ActType.ACT2,
        visual_description="产品特写",
        narration="这是我们的核心产品",
        duration=5.0
    )

    recommendation = scheduler.recommend_model(test_shot, quality_priority=True)
    print(f"\n推荐模型: {recommendation.model_name}")
    print(f"置信度: {recommendation.confidence:.2f}")
    print(f"原因: {recommendation.reasons}")
    print(f"成本: ¥{recommendation.estimated_cost}")

    # 测试批量分配
    test_shots = [
        Shot(i, ShotType.TALKING_HEAD, ActType.ACT1, f"场景{i}", f"文案{i}", 5.0)
        for i in range(1, 11)
    ]

    assigned_shots, total_cost = scheduler.batch_assign_models(
        test_shots,
        total_budget=20.0,
        quality_priority=True
    )

    print(f"\n批量分配结果:")
    for shot in assigned_shots:
        print(f"分镜{shot.id}: {shot.assigned_model} ¥{shot.estimated_cost}")
    print(f"总成本: ¥{total_cost:.2f}")
