# -*- coding: utf-8 -*-
"""
羽翼Pro V2 - 演示脚本
展示颠覆性功能（无需真实API调用）
"""

import sys
import io
from pathlib import Path

# 设置Windows输出编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from models import ProductProfile
from engines.director import Director
from engines.model_scheduler import ModelScheduler
from engines.viral_predictor import ViralPredictor


def demo_director():
    """演示1：超长视频导演系统"""
    print("\n" + "="*70)
    print("🎬 演示1：超长视频导演系统 - 支持3-10分钟长视频")
    print("="*70)

    director = Director()

    # 测试不同长度
    test_cases = [
        ("短视频", 60),
        ("中等长度", 120),
        ("长视频", 180),
        ("超长视频", 300),
    ]

    for name, duration in test_cases:
        print(f"\n>>> {name} ({duration}秒 = {duration//60}分{duration%60}秒)")

        plan = director.create_video_plan(
            topic=f"AI革命-{name}",
            target_duration=duration
        )

        script = director.generate_script_structure(plan)

        print(f"    ✅ 总分镜数: {script.shot_count}")
        print(f"    ✅ 第一幕: {len(script.acts[0].shots)}个分镜")
        print(f"    ✅ 第二幕: {len(script.acts[1].shots)}个分镜")
        print(f"    ✅ 第三幕: {len(script.acts[2].shots)}个分镜")
        print(f"    ✅ 总时长: {script.total_duration:.1f}秒")


def demo_model_scheduler():
    """演示2：智能模型调度引擎"""
    print("\n" + "="*70)
    print("🧠 演示2：智能模型调度引擎 - AI自动选择最优模型")
    print("="*70)

    director = Director()
    scheduler = ModelScheduler()

    # 创建测试脚本
    plan = director.create_video_plan("产品营销", 180)
    script = director.generate_script_structure(plan)

    print(f"\n>>> 场景：180秒视频，{script.shot_count}个分镜")

    # 测试不同预算
    budgets = [None, 150.0, 100.0, 50.0]

    for budget in budgets:
        all_shots = script.get_all_shots()

        # 分配模型
        assigned_shots, total_cost = scheduler.batch_assign_models(
            shots=all_shots,
            total_budget=budget,
            quality_priority=True
        )

        # 统计模型使用
        model_usage = {}
        for shot in assigned_shots:
            model_usage[shot.assigned_model] = model_usage.get(shot.assigned_model, 0) + 1

        budget_str = "无限制" if budget is None else f"¥{budget}"
        print(f"\n    预算: {budget_str}")
        print(f"    实际成本: ¥{total_cost:.2f}")
        print(f"    模型分配:")
        for model_id, count in sorted(model_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      - {model_id}: {count}个")


def demo_viral_predictor():
    """演示3：爆款预测引擎"""
    print("\n" + "="*70)
    print("🔮 演示3：爆款预测引擎 - 生成前预测传播潜力")
    print("="*70)

    director = Director()
    scheduler = ModelScheduler()
    predictor = ViralPredictor()

    # 创建测试脚本
    plan = director.create_video_plan("震撼揭秘", 120)
    script = director.generate_script_structure(plan)

    # 分配模型
    all_shots = script.get_all_shots()
    assigned_shots, _ = scheduler.batch_assign_models(all_shots, quality_priority=True)

    # 模拟填充内容（实际应该由AI生成）
    for i, shot in enumerate(assigned_shots):
        if i == 0:  # 第一镜：强开头
            shot.narration = "你知道吗？90%的人都不知道这个秘密！"
            shot.visual_description = "震撼特写镜头"
        elif shot.shot_type.value == "product":
            shot.narration = "看看这个惊人的产品"
            shot.visual_description = "产品360度展示"
        elif i == len(assigned_shots) - 1:  # 最后一镜：强CTA
            shot.narration = "点赞+关注，下期更精彩！评论区告诉我你的看法"
            shot.visual_description = "主播对镜头呼吁"
        else:
            shot.narration = f"第{i+1}镜内容"
            shot.visual_description = f"第{i+1}镜画面"

    # 预测
    prediction = predictor.predict(script)

    print(f"\n>>> 预测结果")
    print(f"    总分: {prediction.total_score:.1f}/100 ({prediction.grade})")
    print(f"    爆款概率: {prediction.viral_probability:.1%}")
    print(f"\n    各维度得分:")
    print(f"      - 开头吸引力: {prediction.hook_strength:.2f} (前3秒)")
    print(f"      - 情绪曲线: {prediction.emotion_curve:.2f} (起承转合)")
    print(f"      - 视觉冲击力: {prediction.visual_impact:.2f} (画面质量)")
    print(f"      - 信息密度: {prediction.info_density:.2f} (内容价值)")
    print(f"      - 行动号召: {prediction.cta_clarity:.2f} (CTA明确性)")
    print(f"      - 传播性: {prediction.shareability:.2f} (分享意愿)")
    print(f"      - 平台适配: {prediction.platform_fit:.2f} (平台匹配)")

    if prediction.critical_issues:
        print(f"\n    ⚠️  严重问题:")
        for issue in prediction.critical_issues:
            print(f"      - {issue}")

    if prediction.suggestions:
        print(f"\n    💡 优化建议 (前5条):")
        for suggestion in prediction.suggestions[:5]:
            print(f"      - {suggestion}")


def demo_complete_workflow():
    """演示4：完整工作流程"""
    print("\n" + "="*70)
    print("🚀 演示4：完整工作流程 - 端到端展示")
    print("="*70)

    director = Director()
    scheduler = ModelScheduler()
    predictor = ViralPredictor()

    print(f"\n>>> 场景：创建一个180秒（3分钟）的产品营销视频")
    print(f"    主题: AI视频生成革命")
    print(f"    预算: ¥100")

    # Step 1: 导演规划
    print(f"\n    Step 1: AI导演规划...")
    plan = director.create_video_plan("AI视频生成革命", 180)
    script = director.generate_script_structure(plan)
    print(f"    ✅ 规划完成: {script.shot_count}个分镜")

    # Step 2: 模型调度
    print(f"\n    Step 2: 智能模型调度...")
    all_shots = script.get_all_shots()
    assigned_shots, total_cost = scheduler.batch_assign_models(
        shots=all_shots,
        total_budget=100.0,
        quality_priority=True
    )
    print(f"    ✅ 模型分配完成: 预估成本¥{total_cost:.2f}")

    # Step 3: 爆款预测
    print(f"\n    Step 3: 爆款预测...")
    # 模拟填充内容
    for i, shot in enumerate(assigned_shots):
        if i == 0:
            shot.narration = "震撼！AI视频生成技术突破了！"
            shot.emotion_score = 0.7
        elif i == len(assigned_shots) - 1:
            shot.narration = "点赞关注，一起见证AI革命！"
            shot.emotion_score = 0.95
        else:
            shot.narration = f"精彩内容{i+1}"
            shot.emotion_score = 0.6 + (i / len(assigned_shots)) * 0.3

    prediction = predictor.predict(script)
    print(f"    ✅ 预测完成: {prediction.total_score:.1f}/100, 爆款概率{prediction.viral_probability:.1%}")

    # Step 4: 节奏优化
    print(f"\n    Step 4: 节奏优化...")
    optimized_script = director.optimize_pacing(script)
    print(f"    ✅ 优化完成: 最终时长{optimized_script.total_duration:.1f}秒")

    # Step 5: 模拟生成
    print(f"\n    Step 5: 全并发生成（实际需5-10分钟）...")
    print(f"    ⚡ 模拟：{script.shot_count}个分镜同时提交")
    print(f"    ⚡ 模拟：批量轮询状态")
    print(f"    ⚡ 模拟：批量下载视频")
    print(f"    ✅ 生成完成（模拟）")

    # 总结
    print(f"\n" + "="*70)
    print(f"📊 完成报告")
    print(f"="*70)
    print(f"    总分镜数: {script.shot_count}")
    print(f"    视频时长: {optimized_script.total_duration:.1f}秒")
    print(f"    预估成本: ¥{total_cost:.2f}")
    print(f"    爆款分数: {prediction.total_score:.1f}/100")
    print(f"    爆款概率: {prediction.viral_probability:.1%}")

    # 模型使用统计
    model_usage = {}
    for shot in assigned_shots:
        model_usage[shot.assigned_model] = model_usage.get(shot.assigned_model, 0) + 1

    print(f"\n    模型使用统计:")
    for model_id, count in sorted(model_usage.items(), key=lambda x: x[1], reverse=True):
        cost_per = scheduler.models[model_id]["cost_per_video"]
        print(f"      - {model_id}: {count}个 (¥{cost_per * count:.2f})")

    print(f"\n" + "="*70)
    print(f"🎉 完整工作流程演示完成！")
    print(f"="*70)


def main():
    """主演示程序"""
    print("\n" + "="*70)
    print("🚀 羽翼Pro V2 - 颠覆性AI视频生成系统")
    print("="*70)
    print("   10大创新 | 3-10分钟长视频 | 智能模型调度 | 爆款预测")
    print("="*70)

    demos = [
        ("超长视频导演系统", demo_director),
        ("智能模型调度引擎", demo_model_scheduler),
        ("爆款预测引擎", demo_viral_predictor),
        ("完整工作流程", demo_complete_workflow),
    ]

    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ {name} 演示出错: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print("🎉 所有演示完成！系统已就绪，可以开始真实生成！")
    print("="*70)
    print("\n💡 下一步：")
    print("   1. 配置API密钥: 编辑 config.py")
    print("   2. 运行真实生成: python yuyi_pro.py")
    print("   3. 查看文档: README.md")
    print("="*70 + "\n")


if __name__ == "__main__":
    # 配置简洁的日志输出
    logger.remove()
    logger.add(sys.stdout, format="<level>{message}</level>", level="INFO", colorize=True)

    main()
