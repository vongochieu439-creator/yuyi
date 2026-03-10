# -*- coding: utf-8 -*-
"""
用户自建模板 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from loguru import logger

from ..services import user_template_service as svc
from ..data.templates import TEMPLATE_INDEX, TEMPLATE_LIBRARY

router = APIRouter(prefix="/api/user-templates", tags=["user-templates"])


class ExtractRequest(BaseModel):
    script_text: str = Field(..., description="脚本文本内容", min_length=30)
    template_name: str = Field(..., description="模板名称", min_length=1)


class CloneRequest(BaseModel):
    template_id: str = Field(..., description="要克隆的系统模板ID")
    new_name: str = Field(..., description="新模板名称", min_length=1)
    author_name: str = Field(default="自定义", description="来源/作者名称")
    description: str = Field(default="", description="模板说明")


class SaveExtractedRequest(BaseModel):
    name: str
    author_name: str = "自定义"
    description: str = ""
    core_strategy: str = ""
    hook_formula: str = ""
    narration_style: str = ""
    narration_examples: List[str] = []
    structure: Dict = {}
    suitable_categories: List[str] = []
    tags: List[str] = []
    best_duration: str = "60-90秒"


class UpdateRequest(BaseModel):
    name: Optional[str] = None
    core_strategy: Optional[str] = None
    hook_formula: Optional[str] = None
    narration_style: Optional[str] = None
    narration_examples: Optional[List[str]] = None
    structure: Optional[Dict] = None
    suitable_categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    best_duration: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
async def list_user_templates():
    """获取所有用户自建模板"""
    templates = svc.get_all()
    return {"templates": templates, "total": len(templates)}


@router.post("/extract")
async def extract_from_script(request: ExtractRequest):
    """用 AI 从脚本文本提炼模板结构，返回预览（不自动保存）"""
    try:
        preview = await svc.extract_from_script(request.script_text, request.template_name)
        return {"success": True, "preview": preview}
    except Exception as e:
        logger.error(f"提炼模板失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI提炼失败: {str(e)}")


@router.post("/save")
async def save_template(request: SaveExtractedRequest):
    """保存模板（提炼后确认保存，或直接新建）"""
    try:
        template = svc.create(request.model_dump())
        return {"success": True, "template": template}
    except Exception as e:
        logger.error(f"保存模板失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.post("/clone")
async def clone_system_template(request: CloneRequest):
    """克隆一个系统模板为用户模板，可进行编辑"""
    system_template = TEMPLATE_INDEX.get(request.template_id)
    if not system_template:
        raise HTTPException(status_code=404, detail="系统模板不存在")

    new_data = {
        "name": request.new_name,
        "author_name": request.author_name,
        "description": request.description or f"基于「{system_template['name']}」定制",
        "core_strategy": system_template.get("core_strategy", ""),
        "hook_formula": system_template.get("hook_formula", ""),
        "narration_style": system_template.get("narration_style", ""),
        "narration_examples": system_template.get("narration_examples", []),
        "structure": system_template.get("structure", {}),
        "suitable_categories": system_template.get("suitable_categories", []),
        "tags": system_template.get("tags", []),
        "unsuitable_for": system_template.get("unsuitable_for", []),
        "best_duration": system_template.get("best_duration", "60-90秒"),
        "cloned_from": request.template_id
    }

    template = svc.create(new_data)
    return {"success": True, "template": template}


@router.put("/{template_id}")
async def update_template(template_id: str, request: UpdateRequest):
    """更新用户模板字段"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="没有要更新的内容")

    result = svc.update(template_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="模板不存在或无权修改")
    return {"success": True, "template": result}


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """删除用户模板"""
    if not svc.delete(template_id):
        raise HTTPException(status_code=404, detail="模板不存在或无权删除")
    return {"success": True, "message": "已删除"}
