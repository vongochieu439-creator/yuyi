# -*- coding: utf-8 -*-
"""
测试多Agent分镜系统 — 卖货场景
只看Gemini出的脚本质量，不调图片/视频API
"""
import asyncio
import json
import sys
sys.path.insert(0, ".")

from webapp.services.storyboard_director import StoryboardDirector


async def main():
    director = StoryboardDirector()

    print("=" * 70)
    print("  多Agent分镜系统测试 — 卖货短视频")
    print("=" * 70)

    # 测试产品: 一个真实的卖货场景
    product_name = "戴森Airwrap多功能美发器"
    product_detail = "集吹风、卷发、顺滑于一体的多功能美发造型器，利用康达效应气流造型，不伤发质，30秒打造沙龙级造型"
    industry = "个护美容"
    selling_points = [
        "康达效应气流造型，告别传统卷发棒烫伤风险",
        "一机六合一，吹干+卷发+顺滑+蓬松全搞定",
        "30秒沙龙级造型，手残党也能轻松上手",
    ]

    phases = {}

    async def on_agent(agent_name, data):
        phases[agent_name] = data
        print(f"\n{'='*50}")
        print(f"  Agent [{agent_name}] 完成")
        print(f"{'='*50}")

        if agent_name == "director":
            strategy = data.get("content_strategy", {})
            print(f"  切入角度: {strategy.get('angle', '?')}")
            print(f"  Hook类型: {strategy.get('hook_type', '?')}")
            print(f"  叙事弧线: {strategy.get('narrative_arc', '?')}")
            print(f"  情绪序列: {strategy.get('key_emotion_sequence', [])}")
            print(f"  镜头数: {len(data.get('shot_plan', []))}")
            audience = data.get("target_audience", {})
            print(f"  目标人群: {audience.get('primary', '?')}")
            print(f"  停拇指触发: {audience.get('scroll_stop_trigger', '?')}")

        elif agent_name == "screenwriter":
            frames = data.get("frames", [])
            print(f"  帧数: {len(frames)}")
            for f in frames:
                d = f.get('duration', '?')
                n = f.get('narration', '')[:40]
                st = f.get('shot_type', '?')
                print(f"  #{f.get('frame_id', '?')} [{d}s] {st} | {n}")

        elif agent_name == "producer":
            qr = data.get("quality_report", {})
            print(f"  Hook评分: {qr.get('hook_score', '?')}/10")
            print(f"  信息密度: {qr.get('info_density_score', '?')}/10")
            print(f"  卖点覆盖: {qr.get('selling_point_coverage', [])}")
            print(f"  修正项: {qr.get('fixes_applied', [])}")

    result = await director.generate_storyboard(
        product_name=product_name,
        product_detail=product_detail,
        industry=industry,
        selling_points=selling_points,
        target_duration=45,
        style="cinematic",
        on_agent_complete=on_agent,
    )

    # 打印最终分镜
    print("\n")
    print("=" * 70)
    print("  最终分镜脚本")
    print("=" * 70)
    print(f"  标题: {result.get('title', '?')}")
    print(f"  总时长: {result.get('total_duration', '?')}s")
    print(f"  帧数: {len(result.get('frames', []))}")

    # 产品参考
    pr = result.get("product_reference", {})
    if pr:
        print(f"\n  [产品参考图描述]")
        print(f"  {pr.get('description', 'N/A')}")
        print(f"  出现在帧: {pr.get('showcase_frames', [])}")

    # 角色参考
    cr = result.get("character_reference", {})
    if cr and cr.get("needed"):
        print(f"\n  [角色参考图描述]")
        print(f"  {cr.get('description', 'N/A')}")

    # 逐帧详情
    print(f"\n{'─'*70}")
    for f in result.get("frames", []):
        fid = f.get("frame_id", "?")
        dur = f.get("duration", "?")
        st = f.get("shot_type", "?")
        cm = f.get("camera_movement", "?")
        mood = f.get("mood", "?")
        narr = f.get("narration", "")
        vis = f.get("visual_prompt", "")
        text_ov = f.get("text_overlay")
        audio = f.get("audio_cue")
        prod = f.get("product_in_frame", False)

        print(f"\n  帧 #{fid}  [{dur}s]  {st} / {cm}  mood={mood}  产品={'是' if prod else '否'}")
        print(f"  旁白: {narr}")
        print(f"  画面: {vis[:100]}{'...' if len(vis) > 100 else ''}")
        if text_ov:
            print(f"  文字: {text_ov}")
        if audio:
            print(f"  音效: {audio}")
        print(f"  {'─'*66}")

    # 保存完整JSON
    output_path = "test_storyboard_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  完整JSON已保存: {output_path}")


asyncio.run(main())
