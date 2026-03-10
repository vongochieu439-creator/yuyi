# -*- coding: utf-8 -*-
"""
模板库 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from loguru import logger

from ..services.template_matcher import TemplateMatcher
from ..data.templates import ALL_CATEGORIES

router = APIRouter(prefix="/api/templates", tags=["templates"])

matcher = TemplateMatcher()


@router.get("/list")
async def list_templates(
    category: Optional[str] = Query(None, description="按品类筛选，如'美妆'"),
    source_type: Optional[str] = Query(None, description="来源类型筛选: kol / mcn / methodology")
):
    """
    获取全部模板列表（用于展示模板库页面）
    """
    templates = matcher.get_all_templates()

    if category:
        templates = [t for t in templates if category in t.get("suitable_categories", [])]

    if source_type:
        templates = [t for t in templates if t["source"]["type"] == source_type]

    # 返回精简信息（不含详细prompt结构，减少传输量）
    result = []
    for t in templates:
        result.append({
            "template_id": t["template_id"],
            "name": t["name"],
            "source": t["source"],
            "suitable_categories": t["suitable_categories"],
            "tags": t["tags"],
            "core_strategy": t["core_strategy"],
            "best_duration": t.get("best_duration", "60-90秒"),
            "hook_formula": t["hook_formula"],
            "narration_examples": t.get("narration_examples", [])[:2]
        })

    return {
        "total": len(result),
        "categories": ALL_CATEGORIES,
        "templates": result
    }


@router.get("/{template_id}")
async def get_template_detail(template_id: str):
    """
    获取单个模板的完整详情
    """
    template = matcher.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")
    return template


@router.post("/match")
async def match_templates(
    product_name: str = Query(..., description="产品名称"),
    industry: Optional[str] = Query(None, description="行业/品类"),
    product_detail: Optional[str] = Query(None, description="产品详细描述"),
    top_k: int = Query(default=3, ge=1, le=5, description="返回匹配数量")
):
    """
    为产品自动匹配最合适的模板

    返回按匹配度排序的 top_k 个模板，含匹配理由和亮点说明
    """
    try:
        results = await matcher.match(
            product_name=product_name,
            industry=industry,
            product_detail=product_detail,
            top_k=top_k
        )

        output = []
        for r in results:
            t = r["template"]
            output.append({
                "template_id": t["template_id"],
                "name": t["name"],
                "source": t["source"],
                "score": r["score"],
                "match_reason": r["match_reason"],
                "match_highlights": r["match_highlights"],
                "suitable_categories": t["suitable_categories"],
                "tags": t["tags"],
                "core_strategy": t["core_strategy"],
                "hook_formula": t["hook_formula"],
                "narration_examples": t.get("narration_examples", []),
                "best_duration": t.get("best_duration", "60-90秒"),
                "structure_preview": {
                    act: {
                        "name": info["name"],
                        "description": info["description"],
                        "emotion": info["emotion"]
                    }
                    for act, info in t["structure"].items()
                }
            })

        return {
            "product_name": product_name,
            "matched_templates": output
        }

    except Exception as e:
        logger.error(f"模板匹配失败: {e}")
        raise HTTPException(status_code=500, detail=f"模板匹配失败: {str(e)}")
