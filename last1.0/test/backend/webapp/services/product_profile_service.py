# -*- coding: utf-8 -*-
"""
产品档案管理服务 - CRUD操作
存储在 data/product_profiles.json
"""
import json
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

PRODUCT_PROFILES_FILE = Path(__file__).parent.parent / "data" / "product_profiles.json"

_product_profiles_lock = asyncio.Lock()


async def _load_product_profiles() -> Dict:
    async with _product_profiles_lock:
        if not PRODUCT_PROFILES_FILE.exists():
            return {}
        try:
            return json.loads(PRODUCT_PROFILES_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"产品档案JSON解析失败: {e}")
            return {}


async def _save_product_profiles(data: Dict):
    async with _product_profiles_lock:
        PRODUCT_PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
        PRODUCT_PROFILES_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


async def list_product_profiles() -> List[Dict]:
    """获取所有产品档案列表（摘要）"""
    profiles = await _load_product_profiles()
    summaries = []
    for p in profiles.values():
        summaries.append({
            "id": p.get("id", ""),
            "product_name": p.get("product_name", ""),
            "category": p.get("category", ""),
            "price_range": p.get("price_range", ""),
            "target_audience": p.get("target_audience", ""),
            "created_at": p.get("created_at", ""),
            "updated_at": p.get("updated_at", ""),
        })
    return summaries


async def get_product_profile(profile_id: str) -> Optional[Dict]:
    """获取单个产品档案详情"""
    profiles = await _load_product_profiles()
    return profiles.get(profile_id)


async def save_product_profile(profile_data: Dict) -> Dict:
    """创建或更新产品档案"""
    profiles = await _load_product_profiles()

    if "id" not in profile_data or not profile_data["id"]:
        profile_data["id"] = f"prod_{uuid.uuid4().hex[:8]}"
        profile_data["created_at"] = datetime.now().isoformat()

    profile_data["updated_at"] = datetime.now().isoformat()

    # Ensure required fields
    profile_data.setdefault("product_name", "")
    profile_data.setdefault("category", "")
    profile_data.setdefault("price_range", "")
    profile_data.setdefault("core_features", [])
    profile_data.setdefault("target_audience", "")
    profile_data.setdefault("use_cases", [])
    profile_data.setdefault("differentiators", [])
    profile_data.setdefault("brand_tone", "")
    profile_data.setdefault("raw_content", "")

    profiles[profile_data["id"]] = profile_data
    await _save_product_profiles(profiles)

    logger.info(f"产品档案保存: {profile_data['id']} - {profile_data.get('product_name', '')}")
    return profile_data


async def delete_product_profile(profile_id: str) -> bool:
    """删除产品档案"""
    profiles = await _load_product_profiles()
    if profile_id in profiles:
        del profiles[profile_id]
        await _save_product_profiles(profiles)
        logger.info(f"产品档案删除: {profile_id}")
        return True
    return False
