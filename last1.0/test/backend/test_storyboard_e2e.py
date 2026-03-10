# -*- coding: utf-8 -*-
"""
分镜工作台 端到端测试
完整流程: 生成分镜 → 生成图片 → 审核 → 制作视频
"""
import json
import time
import httpx

BASE = "http://localhost:8082"


def sse_collect(resp):
    """收集SSE事件"""
    events = []
    buffer = ""
    for chunk in resp.iter_text():
        buffer += chunk
        lines = buffer.split("\n")
        buffer = lines.pop()
        current_event = "message"
        for line in lines:
            if line.startswith("event: "):
                current_event = line[7:].strip()
            elif line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    events.append((current_event, data))
                    print(f"  [{current_event}] {json.dumps(data, ensure_ascii=False)[:120]}")
                except:
                    pass
    return events


def main():
    client = httpx.Client(timeout=600.0)

    # ===== Step 1: 生成分镜 =====
    print("\n" + "=" * 60)
    print("Step 1: 生成分镜脚本")
    print("=" * 60)

    with client.stream(
        "POST",
        f"{BASE}/api/storyboard/generate",
        json={
            "user_input": "一个程序员在深夜加班时，电脑屏幕突然显示出一行神秘代码",
            "style": "cinematic",
            "total_duration": 30,
        },
    ) as resp:
        events = sse_collect(resp)

    # 提取project_id
    project_id = None
    storyboard = None
    for evt, data in events:
        if evt == "started":
            project_id = data.get("project_id")
        if evt == "storyboard_ready":
            storyboard = data

    if not project_id:
        print("ERROR: 未获取到project_id")
        return

    print(f"\nproject_id: {project_id}")
    print(f"标题: {storyboard.get('title', '?')}")
    print(f"帧数: {len(storyboard.get('frames', []))}")
    for f in storyboard.get("frames", []):
        print(f"  帧{f['frame_id']}: {f['duration']}s | {f.get('narration', '')[:30]}")

    # ===== Step 2: 查看成本估算 =====
    print("\n" + "=" * 60)
    print("Step 2: 成本估算")
    print("=" * 60)

    cost = client.get(f"{BASE}/api/storyboard/{project_id}/cost-estimate").json()
    print(f"  图片: {cost.get('image_total', 0)}元")
    print(f"  视频: {cost.get('video_total', 0)}元")
    print(f"  总计: {cost.get('grand_total', 0)}元")

    # ===== Step 3: 生成分镜图 =====
    print("\n" + "=" * 60)
    print("Step 3: 生成分镜图")
    print("=" * 60)

    with client.stream(
        "POST",
        f"{BASE}/api/storyboard/{project_id}/generate-images",
        json={},
    ) as resp:
        events = sse_collect(resp)

    # 检查结果
    img_complete = None
    for evt, data in events:
        if evt == "images_complete":
            img_complete = data

    if img_complete:
        print(f"\n图片生成完成: {img_complete['success']}/{img_complete['total']} 成功")
    else:
        print("\n图片生成可能有问题，继续...")

    # ===== Step 4: 获取更新后的分镜 =====
    print("\n" + "=" * 60)
    print("Step 4: 获取分镜状态")
    print("=" * 60)

    sb = client.get(f"{BASE}/api/storyboard/{project_id}").json()
    for f in sb.get("frames", []):
        has_img = "有图" if f.get("image_url") else "无图"
        print(f"  帧{f['frame_id']}: status={f['status']} {has_img}")

    # ===== Step 5: 全部审核通过 =====
    print("\n" + "=" * 60)
    print("Step 5: 全部审核通过")
    print("=" * 60)

    actions = []
    for f in sb.get("frames", []):
        if f.get("image_url"):
            actions.append({"frame_id": f["frame_id"], "action": "approve"})

    if actions:
        review_result = client.post(
            f"{BASE}/api/storyboard/{project_id}/review",
            json={"actions": actions},
        ).json()
        print(f"  审核结果: approved={review_result.get('approved', [])}")
    else:
        print("  没有可审核的帧（图片生成可能失败了）")
        # 强制标记为generated/approved以继续测试
        print("  强制标记为approved继续测试...")
        force_actions = [
            {"frame_id": f["frame_id"], "action": "approve"}
            for f in sb.get("frames", [])
        ]
        review_result = client.post(
            f"{BASE}/api/storyboard/{project_id}/review",
            json={"actions": force_actions},
        ).json()
        print(f"  强制审核结果: {review_result}")

    # ===== Step 6: 制作视频 =====
    print("\n" + "=" * 60)
    print("Step 6: 制作最终视频")
    print("=" * 60)

    with client.stream(
        "POST",
        f"{BASE}/api/storyboard/{project_id}/produce",
        json={},
    ) as resp:
        events = sse_collect(resp)

    # 提取视频URL
    video_url = None
    elapsed = 0
    for evt, data in events:
        if evt == "produce_complete":
            video_url = data.get("video_url")
            elapsed = data.get("elapsed_seconds", 0)

    if video_url:
        full_url = f"{BASE}{video_url}"
        print(f"\n{'=' * 60}")
        print(f"视频制作完成!")
        print(f"  用时: {elapsed}s")
        print(f"  URL: {full_url}")
        print(f"{'=' * 60}")

        # 验证视频文件存在
        head = client.head(full_url)
        if head.status_code == 200:
            size_mb = int(head.headers.get("content-length", 0)) / 1024 / 1024
            print(f"  视频大小: {size_mb:.1f}MB")
            print(f"\n  在浏览器打开: {full_url}")
        else:
            print(f"  警告: 视频文件访问失败 status={head.status_code}")
    else:
        # 检查是否有错误
        for evt, data in events:
            if evt == "error":
                print(f"\n视频制作失败: {data.get('message', '未知错误')}")
                break
        else:
            print("\n视频制作未返回完成事件")

    print("\n测试完成!")


if __name__ == "__main__":
    main()
