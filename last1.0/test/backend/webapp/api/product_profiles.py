# -*- coding: utf-8 -*-
"""
产品档案 API 路由 - CRUD + 智能提取
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional
from loguru import logger

from ..services import product_profile_service as pps
from ..services.product_extractor import ProductExtractor

router = APIRouter(prefix="/api/product-profiles", tags=["product-profiles"])

product_extractor = ProductExtractor()


# ==================== 数据模型 ====================

class ProductProfileCreate(BaseModel):
    product_name: str = Field(default="", description="产品名称")
    category: str = Field(default="", description="产品类别")
    price_range: str = Field(default="", description="价格区间")
    core_features: list = Field(default_factory=list, description="核心功能/特点")
    target_audience: str = Field(default="", description="目标受众")
    use_cases: list = Field(default_factory=list, description="使用场景")
    differentiators: list = Field(default_factory=list, description="差异化卖点")
    brand_tone: str = Field(default="", description="品牌调性")
    raw_content: str = Field(default="", description="原始内容")
    id: Optional[str] = Field(default=None, description="档案ID（更新时传入）")


class ExtractProductRequest(BaseModel):
    source_type: str = Field(..., description="来源类型: url|image|text")
    content: str = Field(..., description="内容（URL/base64图片/文本）")


# ==================== CRUD 路由 ====================

@router.get("")
async def list_profiles():
    """获取所有产品档案列表"""
    profiles = await pps.list_product_profiles()
    return {"profiles": profiles, "total": len(profiles)}


@router.post("")
async def create_profile(request: ProductProfileCreate):
    """创建/保存产品档案"""
    try:
        profile = await pps.save_product_profile(request.model_dump())
        return {"success": True, "profile": profile}
    except Exception as e:
        logger.error(f"保存产品档案失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/{profile_id}")
async def get_profile(profile_id: str):
    """获取产品档案详情"""
    profile = await pps.get_product_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="产品档案不存在")
    return profile


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    """删除产品档案"""
    if not await pps.delete_product_profile(profile_id):
        raise HTTPException(status_code=404, detail="产品档案不存在")
    return {"success": True, "message": "已删除"}
