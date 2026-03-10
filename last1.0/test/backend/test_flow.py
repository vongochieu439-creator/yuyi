# -*- coding: utf-8 -*-
"""完整流程测试: smart-create → select direction → select hook → chat → lock"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import httpx
import json
import asyncio

BASE = "http://localhost:8082"

async def test_full_flow():
    print("=" * 60)
    print("  羽翼Pro V2 脚本生成质量升级 - 完整流程测试")
    print("=" * 60)

    # Step 1: smart-create
    print("\n=== Step 1: 智能创作 (smart-create) ===")
    async with httpx.AsyncClient(timeout=120.0, trust_env=False) as c:
        r = await c.post(f"{BASE}/api/script/smart-create", json={
            "product_name": "美白面霜",
            "industry": "美妆护肤",
            "target_duration": 60
        })
    assert r.status_code == 200, f"Step1 FAIL: {r.status_code} {r.text[:200]}"
    d = r.json()
    sid = d["session_id"]
    print(f"  session_id: {sid}")
    print(f"  方向数: {len(d['directions'])}")
    for x in d["directions"]:
        print(f"    {x['direction_id']}: {x['name']} ({x['risk_level']})")
    print("  PASS!")

    # Step 2: select direction → 返回hooks
    print("\n=== Step 2: 选择方向 → 返回Hook候选 ===")
    async with httpx.AsyncClient(timeout=120.0, trust_env=False) as c:
        r = await c.post(f"{BASE}/api/script/{sid}/select", json={"direction_id": 1})
    assert r.status_code == 200, f"Step2 FAIL: {r.status_code} {r.text[:200]}"
    d = r.json()
    hooks = d["data"]["hooks"]
    selling_points = d["data"]["selling_points"]
    print(f"  核心卖点: {selling_points}")
    print(f"  Hook数: {len(hooks)}")
    for h in hooks:
        print(f"    #{h['hook_id']} [{h['style']}] {h['hook_text']}")
        print(f"       依据: {h['rationale']}")
    print("  PASS!")

    # Step 3: select hook → 多步生成脚本
    print("\n=== Step 3: 选择Hook → 生成完整脚本 ===")
    async with httpx.AsyncClient(timeout=120.0, trust_env=False) as c:
        r = await c.post(f"{BASE}/api/script/{sid}/select-hook", json={"hook_id": 2})
    assert r.status_code == 200, f"Step3 FAIL: {r.status_code} {r.text[:200]}"
    d = r.json()
    data = d["data"]
    pid = data["project_id"]
    print(f"  project_id: {pid}")
    print(f"  镜头数: {data['shot_count']}")
    print(f"  总时长: {data['total_duration']}秒")

    # 质量自检
    qc = data.get("quality_check", {})
    print(f"  质量自检:")
    print(f"    字数/时长匹配: {qc.get('word_duration_match')}")
    print(f"    卖点覆盖: {qc.get('selling_point_coverage', [])}")
    print(f"    缺失卖点: {qc.get('missing_selling_points', [])}")
    print(f"    节奏评分: {qc.get('rhythm_score')}")
    print(f"    问题: {qc.get('issues', [])}")
    print(f"    自动修复: {qc.get('auto_fixes', [])}")

    # 打印脚本
    print(f"\n  脚本内容:")
    for s in data["shots"]:
        print(f"    Shot#{s['id']} [{s['shot_type']}/{s['act_type']}] {s['duration']}s")
        print(f"      画面: {s['visual_description'][:60]}...")
        print(f"      口播: {s['narration']}")
        print(f"      依据: {s.get('rationale', '无')}")
    print("  PASS!")

    # Step 4: chat refine
    print("\n=== Step 4: 对话修改脚本 ===")
    async with httpx.AsyncClient(timeout=120.0, trust_env=False) as c:
        r = await c.post(f"{BASE}/api/script/{pid}/chat", json={
            "message": "结尾增加紧迫感",
            "chat_history": []
        })
    assert r.status_code == 200, f"Step4 FAIL: {r.status_code} {r.text[:200]}"
    d = r.json()
    print(f"  AI回复: {d['ai_response']}")
    print(f"  改动: {d['changes_made']}")
    print(f"  更新镜头数: {len(d['updated_shots'])}")
    # 检查rationale是否保留
    has_rationale = any(s.get("rationale") for s in d["updated_shots"])
    print(f"  rationale保留: {has_rationale}")
    print("  PASS!")

    # Step 5: lock
    print("\n=== Step 5: 锁定脚本 ===")
    async with httpx.AsyncClient(timeout=120.0, trust_env=False) as c:
        r = await c.post(f"{BASE}/api/script/{pid}/lock")
    assert r.status_code == 200, f"Step5 FAIL: {r.status_code} {r.text[:200]}"
    d = r.json()
    print(f"  locked: {d['data']['locked']}")
    print("  PASS!")

    print("\n" + "=" * 60)
    print("  ALL 5 STEPS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_full_flow())
