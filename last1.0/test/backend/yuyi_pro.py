# -*- coding: utf-8 -*-
"""
羽翼Pro V2 - 主程序
颠覆性AI视频生成系统
"""

import sys
import asyncio
from pathlib import Path
from loguru import logger
from typing import Optional

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from models import ProductProfile, VideoScript
from engines.director import Director
from engines.model_scheduler import ModelScheduler
from engines.viral_predictor import ViralPredictor
from modules.video_generator import VideoGenerator
from config import LOG_LEVEL, LOG_FORMAT, LOGS_DIR, OUTPUTS_DIR


# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level=LOG_LEVEL,
    colorize=True
)
logger.add(
    LOGS_DIR / "yuyi_pro_{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="1 day",
    retention="7 days"
)


class YuyiPro:
    """羽翼Pro主控制器"""

    def __init__(self):
        self.director = Director()
        self.scheduler = ModelScheduler()
        self.predictor = ViralPredictor()
        self.generator = VideoGenerator()

        logger.info("=" * 60)
        logger.info("🚀 羽翼Pro V2 - 颠覆性AI视频生成系统")
        logger.info("=" * 60)

    async def create_video(
        self,
        topic: str,
        target_duration: int = 180,  # 默认3分钟
        product: Optional[ProductProfile] = None,
        total_budget: Optional[float] = None,
        quality_priority: bool = True,
        style: str = "marketing",
        output_dir: Optional[str] = None
    ) -> dict:
        """
        创建完整视频（全流程）

        Args:
            topic: 主题/热点
            target_duration: 目标时长(秒) 60-600
            product: 产品信息
            total_budget: 总预算(元)
            quality_priority: 是否优先质量
            style: 视频风格
            output_dir: 输出目录

        Returns:
            生成结果
        """
        logger.info(f"\n🎬 开始创建视频")
        logger.info(f"   主题: {topic}")
        logger.info(f"   目标时长: {target_duration}秒 ({target_duration//60}分{target_duration%60}秒)")
        logger.info(f"   预算: {'无限制' if total_budget is None else f'¥{total_budget}'}")

        # Step 1: AI导演 - 创建视频规划
        logger.info(f"\n{'='*60}")
        logger.info(f"📋 Step 1/6: AI导演规划视频结构")
        logger.info(f"{'='*60}")

        video_plan = self.director.create_video_plan(
            topic=topic,
            target_duration=target_duration,
            product=product,
            style=style
        )

        script = self.director.generate_script_structure(video_plan, product)
        logger.info(f"✅ 视频结构规划完成:")
        logger.info(f"   总分镜数: {script.shot_count}")
        logger.info(f"   预计时长: {script.total_duration:.1f}秒")

        # Step 2: 智能模型调度 - 为每个分镜选择最优模型
        logger.info(f"\n{'='*60}")
        logger.info(f"🧠 Step 2/6: 智能模型调度")
        logger.info(f"{'='*60}")

        all_shots = script.get_all_shots()
        assigned_shots, estimated_cost = self.scheduler.batch_assign_models(
            shots=all_shots,
            total_budget=total_budget,
            quality_priority=quality_priority
        )

        script.total_cost = estimated_cost
        logger.info(f"✅ 模型分配完成:")
        logger.info(f"   预估成本: ¥{estimated_cost:.2f}")
        logger.info(f"   平均每镜: ¥{estimated_cost/len(all_shots):.2f}")

        # 显示模型使用统计
        model_usage = {}
        for shot in all_shots:
            model_usage[shot.assigned_model] = model_usage.get(shot.assigned_model, 0) + 1

        logger.info(f"   模型使用:")
        for model_id, count in sorted(model_usage.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"     - {model_id}: {count}个分镜")

        # Step 3: 爆款预测 - 预测传播潜力
        logger.info(f"\n{'='*60}")
        logger.info(f"🔮 Step 3/6: 爆款潜力预测")
        logger.info(f"{'='*60}")

        prediction = self.predictor.predict(script)
        script.viral_score = prediction.total_score
        script.viral_breakdown = {
            "hook_strength": prediction.hook_strength,
            "emotion_curve": prediction.emotion_curve,
            "visual_impact": prediction.visual_impact,
            "info_density": prediction.info_density,
            "cta_clarity": prediction.cta_clarity,
            "shareability": prediction.shareability,
            "platform_fit": prediction.platform_fit,
        }
        script.optimization_suggestions = prediction.suggestions

        logger.info(f"✅ 预测完成:")
        logger.info(f"   总分: {prediction.total_score:.1f}/100 ({prediction.grade})")
        logger.info(f"   爆款概率: {prediction.viral_probability:.1%}")
        logger.info(f"   各维度得分:")
        logger.info(f"     - 开头吸引力: {prediction.hook_strength:.2f}")
        logger.info(f"     - 情绪曲线: {prediction.emotion_curve:.2f}")
        logger.info(f"     - 视觉冲击力: {prediction.visual_impact:.2f}")
        logger.info(f"     - 信息密度: {prediction.info_density:.2f}")
        logger.info(f"     - 行动号召: {prediction.cta_clarity:.2f}")
        logger.info(f"     - 传播性: {prediction.shareability:.2f}")
        logger.info(f"     - 平台适配: {prediction.platform_fit:.2f}")

        if prediction.critical_issues:
            logger.warning(f"   ⚠️  严重问题:")
            for issue in prediction.critical_issues:
                logger.warning(f"     - {issue}")

        if prediction.suggestions:
            logger.info(f"   💡 优化建议:")
            for suggestion in prediction.suggestions[:3]:  # 只显示前3条
                logger.info(f"     - {suggestion}")

        # Step 4: 节奏优化
        logger.info(f"\n{'='*60}")
        logger.info(f"⚡ Step 4/6: 视频节奏优化")
        logger.info(f"{'='*60}")

        optimized_script = self.director.optimize_pacing(script)
        logger.info(f"✅ 节奏优化完成")

        # Step 5: 全并发生成视频
        logger.info(f"\n{'='*60}")
        logger.info(f"🎥 Step 5/6: 全并发生成视频")
        logger.info(f"{'='*60}")

        if output_dir is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = str(OUTPUTS_DIR / f"video_{timestamp}")

        generation_result = await self.generator.generate_all(
            script=optimized_script,
            output_dir=output_dir
        )

        # Step 6: 生成报告
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 Step 6/6: 生成完成报告")
        logger.info(f"{'='*60}")

        success_count = generation_result["success_count"]
        failed_count = generation_result["failed_count"]
        total_duration = generation_result["total_duration"]

        logger.info(f"✅ 视频生成完成!")
        logger.info(f"   成功: {success_count}/{script.shot_count} ({success_count/script.shot_count*100:.1f}%)")
        logger.info(f"   失败: {failed_count}")
        logger.info(f"   总耗时: {total_duration/60:.1f}分钟")
        logger.info(f"   实际成本: ¥{estimated_cost:.2f}")
        logger.info(f"   输出目录: {output_dir}")

        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 全部完成! 颠覆性体验已送达!")
        logger.info(f"{'='*60}\n")

        return {
            "success": success_count > 0,
            "script": optimized_script,
            "prediction": prediction,
            "generation_result": generation_result,
            "output_dir": output_dir,
            "stats": {
                "total_shots": script.shot_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "total_duration_seconds": total_duration,
                "estimated_cost": estimated_cost,
                "viral_score": prediction.total_score,
                "viral_probability": prediction.viral_probability,
            }
        }


# 测试入口
async def main():
    """测试主流程"""
    yuyi = YuyiPro()

    # 测试180秒视频（3分钟）
    result = await yuyi.create_video(
        topic="AI视频生成革命",
        target_duration=180,  # 3分钟
        total_budget=100.0,   # 预算100元
        quality_priority=True,
        style="marketing"
    )

    if result["success"]:
        print("\n" + "="*60)
        print("🎉 测试成功!")
        print("="*60)
        print(f"总分镜数: {result['stats']['total_shots']}")
        print(f"成功生成: {result['stats']['success_count']}")
        print(f"总耗时: {result['stats']['total_duration_seconds']/60:.1f}分钟")
        print(f"实际成本: ¥{result['stats']['estimated_cost']:.2f}")
        print(f"爆款分数: {result['stats']['viral_score']:.1f}/100")
        print(f"爆款概率: {result['stats']['viral_probability']:.1%}")
        print(f"输出目录: {result['output_dir']}")
        print("="*60)
    else:
        print("\n❌ 测试失败")


if __name__ == "__main__":
    # 设置Windows事件循环策略
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
