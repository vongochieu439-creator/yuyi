# -*- coding: utf-8 -*-
"""羽翼Pro V2 端到端测试 - 模拟真人操作流程"""
import httpx
import json
import sys

BASE = "http://127.0.0.1:8082"
c = httpx.Client(trust_env=False, timeout=120)
errors = []
passed = []


def test(name, method, path, json_data=None, expect_status=200):
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = c.get(url)
        elif method == "POST":
            r = c.post(url, json=json_data)
        elif method == "DELETE":
            r = c.delete(url)
        else:
            raise ValueError(f"Unknown method: {method}")

        if r.status_code == expect_status:
            data = r.json() if "application/json" in r.headers.get("content-type", "") else {}
            passed.append(f"  PASS {name} [{r.status_code}]")
            return data
        else:
            errors.append(f"  FAIL {name} - expected {expect_status} got {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        errors.append(f"  FAIL {name} - exception: {e}")
        return None


print("=" * 60)
print("  YuyiPro V2 End-to-End Test")
print("=" * 60)

# ==================== 1. Health ====================
print("\n[1] Health Check")
test("health", "GET", "/health")

# ==================== 2. Product Profiles CRUD ====================
print("\n[2] Product Profiles CRUD")
test("list (empty)", "GET", "/api/product-profiles")

r = test("create", "POST", "/api/product-profiles", {
    "product_name": "TestCream",
    "category": "skincare",
    "price_range": "199-299",
    "core_features": ["whitening", "moisturizing"],
    "target_audience": "women 25-35",
})
prod_id = r.get("profile", {}).get("id", "") if r else ""
if prod_id:
    test("get detail", "GET", f"/api/product-profiles/{prod_id}")
    test("delete", "DELETE", f"/api/product-profiles/{prod_id}")
    test("confirm deleted", "GET", f"/api/product-profiles/{prod_id}", expect_status=404)

# ==================== 3. IP Studio - Profiles ====================
print("\n[3] IP Studio - Profile List")
r = test("list profiles", "GET", "/api/ip-studio/profiles")
if r:
    print(f"     Existing profiles: {r.get('total', 0)}")

# ==================== 4. IP Interview Flow ====================
print("\n[4] IP Interview - Background Phase")
chat = []
r = test("background Q1", "POST", "/api/ip-studio/interview/next-question", {
    "name": "TestUser", "industry": "tech", "chat_history": chat, "phase": "background"
})
if r:
    q = r.get("question", "")
    print(f"     AI: {q[:80]}")
    chat.append({"role": "ai", "content": q})
    chat.append({"role": "user", "content": "I've been in tech for 10 years, running a SaaS company with 50 employees."})

r = test("background Q2", "POST", "/api/ip-studio/interview/next-question", {
    "name": "TestUser", "industry": "tech", "chat_history": chat, "phase": "background"
})
if r:
    q = r.get("question", "")
    print(f"     AI: {q[:80]}")
    print(f"     is_done: {r.get('is_done', False)}")

# ==================== 5. Script Creator - Quick Mode ====================
print("\n[5] Script Creator - Quick Mode")
r = test("smart-create", "POST", "/api/script/smart-create", {
    "product_name": "smart watch",
    "industry": "electronics",
    "target_duration": 60,
    "mode": "quick",
})
session_id = r.get("session_id", "") if r else ""
directions = r.get("directions", []) if r else []
print(f"     Session: {session_id}, Directions: {len(directions)}")
if directions:
    for d in directions:
        print(f"       - {d.get('name')}: {d.get('description', '')[:50]}")

if session_id and directions:
    dir_id = directions[0].get("direction_id", 1)
    r = test("select direction", "POST", f"/api/script/{session_id}/select", {"direction_id": dir_id})
    hooks = r.get("data", {}).get("hooks", []) if r else []
    sp = r.get("data", {}).get("selling_points", []) if r else []
    print(f"     Hooks: {len(hooks)}, Selling points: {len(sp)}")
    if hooks:
        for h in hooks[:2]:
            print(f"       - [{h.get('style')}] {h.get('hook_text', '')[:50]}")

    if hooks:
        hook_id = hooks[0].get("hook_id", 1)
        r = test("select hook + generate", "POST", f"/api/script/{session_id}/select-hook", {"hook_id": hook_id})
        if r:
            data = r.get("data", {})
            project_id = data.get("project_id", "")
            shots = data.get("shots", [])
            print(f"     Project: {project_id}, Shots: {len(shots)}")
            if shots:
                for s in shots[:2]:
                    print(f"       - [{s.get('shot_type')}] {s.get('narration', '')[:50]}")

            if project_id:
                r = test("chat refine", "POST", f"/api/script/{project_id}/chat", {
                    "message": "make the opening more impactful",
                    "chat_history": [],
                })
                if r:
                    print(f"     AI reply: {r.get('ai_response', '')[:80]}")

                test("lock script", "POST", f"/api/script/{project_id}/lock")

# ==================== 6. Deep Mode ====================
print("\n[6] Script Creator - Deep Mode")
r = test("intake Q1", "POST", "/api/script/intake/next-question", {
    "session_id": "", "chat_history": []
})
if r:
    q = r.get("question", "")
    print(f"     AI: {q[:80]}")

    intake_chat = [
        {"role": "ai", "content": q},
        {"role": "user", "content": "Our product is TimeX Pro smartwatch, priced at $199, targeting fitness enthusiasts."},
    ]
    r2 = test("intake Q2", "POST", "/api/script/intake/next-question", {
        "session_id": "", "chat_history": intake_chat,
    })
    if r2:
        print(f"     AI: {r2.get('question', '')[:80]}")
        print(f"     complete: {r2.get('is_complete', False)}")

# ==================== 7. Product Extraction ====================
print("\n[7] Product Info Extraction")
r = test("extract from text", "POST", "/api/script/extract-product-info", {
    "source_type": "text",
    "content": "TimeX Pro smartwatch, $199. Blood oxygen, heart rate, sleep monitoring. IP68, 7-day battery. For fitness enthusiasts 25-45.",
})
if r:
    info = r.get("product_info", {})
    print(f"     Name: {info.get('product_name', '')}")
    print(f"     Category: {info.get('category', '')}")
    print(f"     Features: {info.get('core_features', [])}")

# ==================== 8. Templates ====================
print("\n[8] Template Library")
r = test("list templates", "GET", "/api/templates/list")
if r:
    print(f"     Templates: {len(r.get('templates', []))}")

# ==================== 9. Frontend Page ====================
print("\n[9] Frontend Accessibility")
r2 = c.get("http://127.0.0.1:5173/")
if r2.status_code == 200 and "app" in r2.text.lower():
    passed.append("  PASS frontend index.html loads")
    print("     Frontend loads OK")
else:
    errors.append(f"  FAIL frontend - status {r2.status_code}")

r3 = c.get("http://127.0.0.1:5173/api/ip-studio/profiles")
if r3.status_code == 200:
    passed.append("  PASS vite proxy works")
    print("     Vite API proxy works")
else:
    errors.append(f"  FAIL vite proxy - status {r3.status_code}")

# ==================== Summary ====================
print("\n" + "=" * 60)
print(f"  Results: {len(passed)} passed, {len(errors)} failed")
print("=" * 60)

if errors:
    print("\nFailed tests:")
    for e in errors:
        print(e)

print("\nPassed tests:")
for p in passed:
    print(p)

c.close()
sys.exit(1 if errors else 0)
