# -*- coding: utf-8 -*-
"""
导出相关API路由
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from loguru import logger

from ..services.video_merger import VideoMerger
from ..models.schemas import ExportConfig, ExportTask

router = APIRouter(prefix="/api", tags=["export"])

# 创建视频合并器实例
video_merger = VideoMerger()


@router.post("/projects/{project_id}/export", response_model=ExportTask)
async def export_video(
    project_id: str,
    config: ExportConfig,
    background_tasks: BackgroundTasks
):
    """
    创建导出任务（异步执行）

    Args:
        project_id: 项目ID
        config: 导出配置
        background_tasks: FastAPI后台任务

    Returns:
        导出任务信息
    """
    try:
        # 1. 创建任务
        task = await video_merger.create_export_task(
            project_id,
            config.model_dump()
        )

        # 2. 在后台执行视频合并
        background_tasks.add_task(
            video_merger.process_export,
            task["task_id"]
        )

        logger.info(f"导出任务已创建: {task['task_id']}")

        return task

    except Exception as e:
        logger.error(f"创建导出任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建导出任务失败: {str(e)}")


@router.get("/export/{task_id}/status")
async def get_export_status(task_id: str):
    """
    查询导出状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态
    """
    try:
        task = video_merger.get_task_status(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询导出状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询状态失败: {str(e)}")


@router.websocket("/ws/export/{task_id}")
async def export_progress_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket端点 - 推送导出进度

    Args:
        websocket: WebSocket连接
        task_id: 任务ID
    """
    await websocket.accept()
    logger.info(f"WebSocket连接已建立: {task_id}")

    try:
        # 推送进度流
        async for progress in video_merger.get_progress_stream(task_id):
            await websocket.send_json(progress)

        # 完成后关闭连接
        await websocket.close()
        logger.info(f"WebSocket连接已关闭: {task_id}")

    except WebSocketDisconnect:
        logger.info(f"客户端断开连接: {task_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        try:
            await websocket.close()
        except:
            pass
