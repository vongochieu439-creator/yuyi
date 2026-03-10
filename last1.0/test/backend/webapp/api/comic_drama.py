# -*- coding: utf-8 -*-
"""
漫剧一键生成 API路由
"""
import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from ..services.comic_drama_service import ComicDramaService

router = APIRouter(prefix="/api/comic-drama", tags=["漫剧生成"])

# 服务实例
_service = ComicDramaService()


class ComicDramaRequest(BaseModel):
    """漫剧生成请求"""
    user_input: str = Field(..., description="故事概念", min_length=2)
    style: str = Field(default="cinematic", description="视觉风格: cinematic|ink_wash|anime|comedy")


@router.post("/generate")
async def generate_comic_drama(req: ComicDramaRequest):
    """
    SSE流式生成漫剧

    事件类型:
    - started: 生成开始
    - storyboard_ready: 分镜脚本就绪
    - image_generated: 单张图片完成
    - progress: 进度更新
    - complete: 生成完成
    - error: 出错
    """
    logger.info(f"漫剧生成请求: input={req.user_input[:30]}, style={req.style}")

    async def event_stream():
        try:
            async for event in _service.generate(req.user_input, req.style):
                event_type = event.get("event", "progress")
                event_data = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: {event_type}\ndata: {event_data}\n\n"
                # 小延迟确保前端能逐条接收
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


@router.get("/history")
async def get_history():
    """获取生成历史"""
    return {"history": ComicDramaService.get_history()}


@router.get("/result/{task_id}")
async def get_result(task_id: str):
    """获取生成结果"""
    result = ComicDramaService.get_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="结果不存在")
    return result


@router.get("/styles")
async def get_styles():
    """获取可用风格列表"""
    from ..services.comic_drama_prompts import STYLE_MODIFIERS
    styles = []
    icons = {"cinematic": "🎬", "ink_wash": "🏯", "anime": "🌸", "comedy": "🤡"}
    for key, info in STYLE_MODIFIERS.items():
        styles.append({
            "id": key,
            "name": info["name"],
            "icon": icons.get(key, "🎨"),
            "description": info["suffix"][:60] + "...",
        })
    return {"styles": styles}
