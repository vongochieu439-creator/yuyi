# -*- coding: utf-8 -*-
"""
分镜相关API路由
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..services.project_manager import ProjectManager
from ..models.schemas import ShotList, ReorderRequest, SuccessResponse

router = APIRouter(prefix="/api/projects", tags=["shots"])

# 创建项目管理器实例
project_manager = ProjectManager()


@router.get("/{project_id}/shots", response_model=ShotList)
async def get_project_shots(project_id: str):
    """
    获取项目的所有分镜

    Args:
        project_id: 项目ID

    Returns:
        分镜列表
    """
    try:
        project = await project_manager.get_project_detail(project_id)

        if not project:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")

        return {
            "project_id": project_id,
            "shots": project["shots"],
            "total_count": len(project["shots"])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分镜列表失败 {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取分镜列表失败: {str(e)}")


@router.put("/{project_id}/shots/reorder", response_model=SuccessResponse)
async def reorder_shots(project_id: str, request: ReorderRequest):
    """
    重新排序分镜

    Args:
        project_id: 项目ID
        request: 重排序请求（包含新的分镜顺序）

    Returns:
        成功响应
    """
    try:
        success = await project_manager.reorder_shots(project_id, request.shot_order)

        if not success:
            raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")

        return {
            "success": True,
            "message": "分镜顺序已保存",
            "data": {
                "project_id": project_id,
                "shot_order": request.shot_order
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存分镜顺序失败 {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"保存分镜顺序失败: {str(e)}")
