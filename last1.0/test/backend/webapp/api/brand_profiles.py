# -*- coding: utf-8 -*-
"""
品牌档案 CRUD API 路由
"""
import json
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import List
from loguru import logger

from ..config import BRAND_PROFILES_DIR
from ..models.schemas import (
    BrandProfile, CreateBrandProfileRequest, SuccessResponse
)

router = APIRouter(prefix="/api/brand-profiles", tags=["brand-profiles"])


def _ensure_dir():
    """确保品牌档案目录存在"""
    BRAND_PROFILES_DIR.mkdir(parents=True, exist_ok=True)


def _load_profile(profile_id: str) -> dict:
    """加载单个品牌档案"""
    _ensure_dir()
    profile_path = BRAND_PROFILES_DIR / f"{profile_id}.json"
    if not profile_path.exists():
        return None
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/", response_model=SuccessResponse)
async def create_brand_profile(request: CreateBrandProfileRequest):
    """创建品牌档案"""
    _ensure_dir()

    profile_id = str(uuid.uuid4())[:8]
    profile = {
        "profile_id": profile_id,
        "brand_name": request.brand_name,
        "brand_tone": request.brand_tone,
        "forbidden_words": request.forbidden_words,
        "preferred_expressions": request.preferred_expressions,
        "visual_style": request.visual_style,
        "target_audience": request.target_audience
    }

    profile_path = BRAND_PROFILES_DIR / f"{profile_id}.json"
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    logger.info(f"品牌档案已创建: {profile_id} - {request.brand_name}")
    return SuccessResponse(
        success=True,
        message=f"品牌档案「{request.brand_name}」创建成功",
        data=profile
    )


@router.get("/", response_model=List[BrandProfile])
async def list_brand_profiles():
    """获取所有品牌档案"""
    _ensure_dir()

    profiles = []
    for f in BRAND_PROFILES_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                profiles.append(BrandProfile(**data))
        except Exception as e:
            logger.warning(f"读取品牌档案失败 {f}: {e}")

    return profiles


@router.get("/{profile_id}", response_model=BrandProfile)
async def get_brand_profile(profile_id: str):
    """获取品牌档案详情"""
    data = _load_profile(profile_id)
    if not data:
        raise HTTPException(status_code=404, detail="品牌档案不存在")
    return BrandProfile(**data)


@router.delete("/{profile_id}", response_model=SuccessResponse)
async def delete_brand_profile(profile_id: str):
    """删除品牌档案"""
    _ensure_dir()
    profile_path = BRAND_PROFILES_DIR / f"{profile_id}.json"
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="品牌档案不存在")

    profile_path.unlink()
    logger.info(f"品牌档案已删除: {profile_id}")
    return SuccessResponse(
        success=True,
        message="品牌档案已删除",
        data={"profile_id": profile_id}
    )
