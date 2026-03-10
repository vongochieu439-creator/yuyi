# -*- coding: utf-8 -*-
"""
分镜审核 API路由
"""
import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger

from ..services.storyboard_service import StoryboardService
from ..models.schemas import (
    StoryboardGenerateRequest,
    StoryboardReviewRequest,
)

router = APIRouter(prefix="/api/storyboard", tags=["分镜审核"])

# 服务实例
_service = StoryboardService()


# ==================== 生成分镜 ====================

@router.post("/generate")
async def generate_storyboard(req: StoryboardGenerateRequest):
    """
    SSE流式生成分镜脚本

    事件类型:
    - started: 生成开始 {project_id}
    - phase_complete: 阶段完成 {phase}
    - storyboard_ready: 分镜就绪 {完整数据}
    - error: 出错
    """
    logger.info(f"分镜生成请求: input={req.user_input[:30]}, style={req.style}")

    async def event_stream():
        try:
            async for event in _service.generate_storyboard(
                user_input=req.user_input,
                style=req.style,
                hook_type=req.hook_type,
                total_duration=req.total_duration,
                character_description=req.character_description or "",
                product_detail=req.product_detail or "",
            ):
                event_type = event.get("event", "progress")
                event_data = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: {event_type}\ndata: {event_data}\n\n"
                await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"SSE流错误: {e}")
            error_data = json.dumps({"message": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ==================== 获取分镜 ====================

@router.get("/{project_id}")
async def get_storyboard(project_id: str):
    """获取分镜状态"""
    result = _service.get_storyboard(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="项目不存在")
    return result


# ==================== 生成分镜图 ====================

@router.post("/{project_id}/generate-images")
async def generate_images(project_id: str):
    """
    SSE流式为所有帧生成分镜图

    事件类型:
    - image_generating: 开始生成 {frame_id}
    - image_generated: 生成完成 {frame_id, image_url}
    - image_failed: 生成失败 {frame_id, error}
    - images_complete: 全部完成 {total, success, failed}
    """
    storyboard = _service.get_storyboard(project_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="项目不存在")

    async def event_stream():
        try:
            async for event in _service.generate_images(project_id):
                event_type = event.get("event", "progress")
                event_data = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: {event_type}\ndata: {event_data}\n\n"
                await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"图片生成SSE错误: {e}")
            error_data = json.dumps({"message": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ==================== 批量审核 ====================

@router.post("/{project_id}/review")
async def review_frames(project_id: str, req: StoryboardReviewRequest):
    """批量审核帧（通过/驳回+反馈）"""
    try:
        result = _service.review_frames(
            project_id,
            [a.model_dump() for a in req.actions],
        )
        return {"success": True, **result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="项目不存在")


# ==================== 单帧重新生成 ====================

class RegenerateFrameRequest(BaseModel):
    feedback: Optional[str] = Field(None, description="用户反馈")

@router.post("/{project_id}/regenerate-frame/{frame_id}")
async def regenerate_frame(
    project_id: str,
    frame_id: int,
    req: Optional[RegenerateFrameRequest] = None,
):
    """用反馈重新生成单帧"""
    try:
        feedback = req.feedback if req else None
        result = await _service.regenerate_frame(project_id, frame_id, feedback)
        return {"success": True, **result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="项目不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 视频制作 ====================

@router.post("/{project_id}/produce")
async def produce_video(project_id: str):
    """
    SSE流式制作最终视频

    事件类型:
    - producing_started: 开始制作
    - video_generating: 帧视频生成中 {frame_id}
    - video_generated: 帧视频完成 {frame_id}
    - composing: 合成中 {message}
    - produce_complete: 完成 {video_url, elapsed}
    - error: 出错
    """
    storyboard = _service.get_storyboard(project_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="项目不存在")

    async def event_stream():
        try:
            async for event in _service.produce_video(project_id):
                event_type = event.get("event", "progress")
                event_data = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: {event_type}\ndata: {event_data}\n\n"
                await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"视频制作SSE错误: {e}")
            error_data = json.dumps({"message": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ==================== 成本估算 ====================

@router.get("/{project_id}/cost-estimate")
async def cost_estimate(project_id: str):
    """获取成本估算"""
    result = _service.get_cost_estimate(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
