# -*- coding: utf-8 -*-
"""
智能脚本创作 API 路由 (V2: 一体化脚本视频流水线)
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from loguru import logger

from ..services.script_creator import ScriptCreator
from ..services.script_preview_service import ScriptPreviewService
from ..services.product_extractor import ProductExtractor
from ..models.schemas import (
    SmartCreateRequest, SmartCreateResponse, SmartCreateResponseV2,
    SelectDirectionRequest, SelectHookRequest,
    SelectScriptRequest, RegenerateScriptsRequest,
    UpdateFrameRequest, RegenerateFrameImageRequest,
    SkipToPreviewRequest,
    ScriptChatRequest, ScriptChatResponse,
    SuccessResponse, CreativeDirection,
    SmartCreateV2Request, SmartCreateV2Response,
    ResearchStatusResponse, ResearchResultResponse,
)

router = APIRouter(prefix="/api/script", tags=["script-v2"])

# 全局服务实例
script_creator = ScriptCreator()
product_extractor = ProductExtractor()
preview_service = ScriptPreviewService()

from ..services.tts_service import TTSService
from ..services.material_service import MaterialService
tts_service = TTSService()
material_service = MaterialService()


# ==================== TTS配音 ====================


@router.get("/tts/voices")
async def get_tts_voices():
    """获取所有可用音色列表"""
    return {"success": True, "voices": tts_service.get_voice_catalog()}


@router.post("/tts/preview")
async def preview_tts_voice(request: dict):
    """试听音色"""
    from fastapi.responses import FileResponse
    voice_id = request.get("voice_id", "zh-CN-XiaoxiaoNeural")
    text = request.get("text")
    try:
        audio_path = await tts_service.preview_voice(voice_id, text)
        return FileResponse(audio_path, media_type="audio/mpeg", filename=f"preview_{voice_id}.mp3")
    except Exception as e:
        logger.error(f"TTS试听失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class GenerateNarrationRequest(BaseModel):
    voice: Optional[str] = Field(None, description="音色ID（不填则根据行业自动推荐）")
    rate: str = Field(default="-5%", description="语速（如 -10%, +5%）")


@router.post("/{project_id}/generate-narration")
async def generate_narration(project_id: str, request: GenerateNarrationRequest):
    """为项目所有镜头生成配音"""
    try:
        result = await tts_service.generate_project_narrations(
            project_id=project_id,
            voice=request.voice,
            rate=request.rate,
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"项目配音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 素材搜索 ====================


@router.get("/material/search")
async def search_materials(query: str, orientation: str = "portrait", per_page: int = 10):
    """搜索免费商用素材（Pexels视频+图片）"""
    try:
        videos = await material_service.search_pexels_videos(query, orientation, per_page)
        images = await material_service.search_pexels_images(query, orientation, min(per_page, 5))
        for v in videos:
            v["type"] = "video"
        for img in images:
            img["type"] = "image"
        return {"success": True, "materials": videos + images, "query": query}
    except Exception as e:
        logger.error(f"素材搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/search-materials")
async def search_project_materials(project_id: str):
    """为项目所有镜头自动搜索匹配素材"""
    try:
        result = await material_service.search_for_project(project_id)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"项目素材搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 产品信息提取 ====================

class ExtractProductRequest(BaseModel):
    source_type: str = Field(..., description="来源类型: url|image|text")
    content: str = Field(..., description="内容（URL/base64图片/文本）")


class IntakeQuestionRequest(BaseModel):
    session_id: str = Field(default="", description="会话ID")
    chat_history: List[Dict] = Field(default_factory=list, description="对话历史")


@router.post("/extract-product-info")
async def extract_product_info(request: ExtractProductRequest):
    """智能产品信息提取 - 支持URL/图片/文本"""
    try:
        if request.source_type == "url":
            result = await product_extractor.extract_from_url(request.content)
        elif request.source_type == "image":
            result = await product_extractor.extract_from_image(request.content)
        elif request.source_type == "text":
            result = await product_extractor.extract_from_text(request.content)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的来源类型: {request.source_type}")

        return {"success": True, "product_info": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"产品信息提取失败: {e}")
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")


@router.post("/intake/next-question")
async def intake_next_question(request: IntakeQuestionRequest):
    """深度模式: AI动态生成下一个产品信息采集问题"""
    try:
        result = await script_creator.intake_next_question(
            session_id=request.session_id,
            chat_history=request.chat_history
        )
        return {"success": True, **result}

    except Exception as e:
        logger.error(f"深度模式问题生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"问题生成失败: {str(e)}")


# ==================== 深度模式: 创意工作室 ====================
# 注意：这些固定路径路由必须在 /{xxx} 动态路由之前注册，否则 "deep" 会被当作路径参数


class DeepChatRequest(BaseModel):
    session_id: str = Field(default="", description="会话ID（首次对话可为空，自动创建）")
    message: str = Field(..., min_length=1, description="用户消息")
    chat_history: List[Dict] = Field(default_factory=list, description="对话历史")
    product_name: Optional[str] = Field(None, description="产品名称（首次对话时传）")
    industry: Optional[str] = Field(None, description="行业（首次对话时传）")


class DeepInspireRequest(BaseModel):
    session_id: str = Field(default="", description="会话ID")
    product_name: str = Field(..., min_length=1, description="产品名称")
    industry: Optional[str] = Field(None, description="行业")


@router.post("/deep/chat")
async def deep_chat(request: DeepChatRequest):
    """深度模式: 带工具调用的AI对话"""
    try:
        sid = request.session_id
        if not sid:
            import uuid
            sid = str(uuid.uuid4())[:8]
            if request.product_name:
                script_creator.sessions[sid] = {
                    "mode": "deep",
                    "product_name": request.product_name,
                    "industry": request.industry,
                    "target_duration": 60,
                    "deep_context": {"messages": [], "tool_results": [], "inspirations": []},
                }

        result = await script_creator.deep_chat_with_tools(
            session_id=sid,
            message=request.message,
            chat_history=request.chat_history,
        )
        return {"success": True, "session_id": sid, **result}

    except Exception as e:
        logger.error(f"深度对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


@router.post("/deep/inspire")
async def deep_inspire(request: DeepInspireRequest):
    """深度模式: 灵感获取（并行搜索多数据源）"""
    try:
        result = await script_creator.deep_get_inspiration(
            session_id=request.session_id,
            product_name=request.product_name,
            industry=request.industry,
        )
        return {"success": True, **result}

    except Exception as e:
        logger.error(f"灵感获取失败: {e}")
        raise HTTPException(status_code=500, detail=f"灵感获取失败: {str(e)}")


@router.post("/deep/generate/{session_id}")
async def deep_generate(session_id: str):
    """深度模式: 从完整对话上下文生成3个脚本"""
    try:
        result = await script_creator.deep_generate_from_conversation(session_id)
        scripts = result.get("scripts", [])
        return {
            "success": True,
            "session_id": session_id,
            "scripts": scripts,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"深度模式脚本生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/smart-create")
async def smart_create(request: SmartCreateRequest):
    """
    智能创作V2: 快速返回3个方向摘要（~10秒），选中后再生成完整脚本

    流程:
    1. 创建session (调研/快速模式) → 返回3个方向摘要
    2. 用户选择后，select-script 再调 StoryboardDirector 生成完整脚本
    """
    try:
        brand_profile = None
        if request.brand_profile_id:
            from .brand_profiles import _load_profile
            brand_profile = _load_profile(request.brand_profile_id)

        session_result = await script_creator.create_session(
            product_name=request.product_name,
            industry=request.industry,
            target_duration=request.target_duration,
            reference_text=request.reference_text,
            brand_profile=brand_profile,
            product_detail=request.product_detail,
            mode=request.mode,
            template_id=request.template_id
        )

        session_id = session_result["session_id"]

        # 快速模式：返回预生成的完整脚本（含shots）
        quick_scripts = session_result.get("scripts", [])
        if quick_scripts:
            scripts = []
            for s in quick_scripts:
                scripts.append({
                    "script_id": s.get("script_id", 0),
                    "name": s.get("name", ""),
                    "risk_level": s.get("risk_level", "moderate"),
                    "description": s.get("description", ""),
                    "shots": s.get("shots", []),
                    "total_duration": s.get("total_duration", request.target_duration),
                    "selling_points": s.get("selling_points", []),
                    "quality_report": {},
                    "hook": s.get("hook", ""),
                    "structure_preview": s.get("structure_preview", []),
                    "creative_techniques": s.get("creative_techniques", []),
                })
        else:
            # 详细模式：方向摘要（无shots）
            directions = session_result.get("directions", [])
            scripts = []
            for i, d in enumerate(directions):
                scripts.append({
                    "script_id": i,
                    "name": d.get("name", f"方案{i+1}"),
                    "risk_level": d.get("risk_level", "moderate"),
                    "description": d.get("description", ""),
                    "shots": [],  # 选中后才生成
                    "total_duration": request.target_duration,
                    "selling_points": [],
                    "quality_report": {},
                    "hook": d.get("hook", ""),
                    "structure_preview": d.get("structure_preview", []),
                    "creative_techniques": d.get("creative_techniques", []),
                })

        return {
            "success": True,
            "session_id": session_id,
            "competitor_summary": session_result.get("competitor_summary", {}),
            "market_summary": session_result.get("market_summary", {}),
            "scripts": scripts,
        }

    except Exception as e:
        logger.error(f"智能创作失败: {e}")
        raise HTTPException(status_code=500, detail=f"智能创作失败: {str(e)}")


@router.post("/{session_id}/select", response_model=SuccessResponse)
async def select_direction(session_id: str, request: SelectDirectionRequest):
    """
    选择创意方向 → 提取卖点 + 生成5个Hook候选

    返回: {session_id, direction, selling_points, hooks}
    """
    try:
        result = await script_creator.select_direction(session_id, request.direction_id)

        return SuccessResponse(
            success=True,
            message=f"已生成 {len(result['hooks'])} 个开场Hook候选",
            data=result
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"选择方向失败: {e}")
        raise HTTPException(status_code=500, detail=f"选择方向失败: {str(e)}")


@router.post("/{session_id}/select-hook", response_model=SuccessResponse)
async def select_hook(session_id: str, request: SelectHookRequest):
    """
    选择Hook并多步生成完整脚本

    流程:
    1. Director创建镜头骨架
    2. 用选中Hook填充开场
    3. Gemini生成主体内容(覆盖3个卖点)
    4. Gemini生成结尾(与Hook呼应)
    5. 质量自检 + 自动修复
    6. 创建项目目录 + metadata.json
    """
    try:
        result = await script_creator.select_hook(session_id, request.hook_id)

        return SuccessResponse(
            success=True,
            message=f"脚本生成成功，共 {result['shot_count']} 个镜头",
            data=result
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"选择Hook生成脚本失败: {e}")
        raise HTTPException(status_code=500, detail=f"脚本生成失败: {str(e)}")


@router.post("/{project_id}/chat", response_model=ScriptChatResponse)
async def chat_refine(project_id: str, request: ScriptChatRequest):
    """
    对话式脚本修改

    前端每次发送消息时带上chat_history，后端不持久化对话历史
    """
    try:
        result = await script_creator.chat_refine(
            project_id=project_id,
            message=request.message,
            chat_history=request.chat_history
        )

        return ScriptChatResponse(
            ai_response=result["ai_response"],
            changes_made=result["changes_made"],
            updated_shots=result["updated_shots"]
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"对话修改失败: {e}")
        raise HTTPException(status_code=500, detail=f"对话修改失败: {str(e)}")


@router.post("/{project_id}/lock", response_model=SuccessResponse)
async def lock_script(project_id: str):
    """锁定脚本，标记为可进入关键帧阶段"""
    try:
        result = await script_creator.lock_script(project_id)
        return SuccessResponse(success=True, message="脚本已锁定", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"锁定脚本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== V2: 一体化脚本视频流水线 ====================


@router.post("/{session_id}/select-script", response_model=SuccessResponse)
async def select_script(session_id: str, request: SelectScriptRequest):
    """选择方向 → 调StoryboardDirector生成完整脚本 → 创建项目"""
    try:
        # session 不存在但前端附带了完整脚本数据时，直接用该数据创建项目（防止后端reload后丢失session）
        if request.script_data and request.script_data.get("shots"):
            if not script_creator.sessions.get(session_id):
                script_creator.sessions[session_id] = {
                    "product_name": request.product_name or request.script_data.get("product_name", ""),
                    "product_detail": request.product_detail or "",
                    "industry": request.industry or "",
                    "target_duration": 60,
                    "quick_scripts": [request.script_data],
                }
                logger.info(f"Session {session_id} 不存在，已从前端脚本数据恢复")

        result = await script_creator.generate_single_script_and_create_project(
            session_id, request.script_id
        )
        return SuccessResponse(
            success=True,
            message=f"脚本生成完成，{result['shot_count']}个镜头",
            data=result,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"选择脚本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/regenerate-scripts")
async def regenerate_scripts(session_id: str, request: RegenerateScriptsRequest):
    """换一批脚本"""
    try:
        result = await script_creator.regenerate_scripts(session_id, request.feedback)
        return {
            "success": True,
            "session_id": session_id,
            "scripts": result.get("scripts", []),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"重新生成脚本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ChatRefineV2Request(BaseModel):
    """V2对话修改请求（支持多脚本上下文）"""
    message: str = Field(..., min_length=1)
    chat_history: List[Dict] = Field(default_factory=list)
    all_scripts_context: Optional[List[Dict]] = Field(None, description="全部脚本上下文，用于混搭")


@router.post("/{project_id}/chat-v2", response_model=ScriptChatResponse)
async def chat_refine_v2(project_id: str, request: ChatRefineV2Request):
    """对话式脚本修改V2（支持多脚本混搭）"""
    try:
        result = await script_creator.chat_refine(
            project_id=project_id,
            message=request.message,
            chat_history=request.chat_history,
            all_scripts_context=request.all_scripts_context,
        )
        return ScriptChatResponse(
            ai_response=result["ai_response"],
            changes_made=result["changes_made"],
            updated_shots=result["updated_shots"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"对话修改失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _sse_stream(generator):
    """将AsyncGenerator转为SSE格式的StreamingResponse"""
    async def event_stream():
        async for event in generator:
            evt_type = event.get("event", "message")
            data = json.dumps(event.get("data", {}), ensure_ascii=False)
            yield f"event: {evt_type}\ndata: {data}\n\n"
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class GeneratePreviewRequest(BaseModel):
    global_style: str = Field(default="", description="全局风格提示词（用户输入，中英文均可）")


@router.post("/{project_id}/generate-preview")
async def generate_preview(project_id: str, request: GeneratePreviewRequest = GeneratePreviewRequest()):
    """SSE: 生成分镜预览图（支持全局风格）"""
    return _sse_stream(preview_service.generate_preview_images(project_id, global_style=request.global_style))


@router.post("/{project_id}/update-frame", response_model=SuccessResponse)
async def update_frame(project_id: str, request: UpdateFrameRequest):
    """更新单帧文案/视觉描述"""
    try:
        result = await preview_service.update_frame(
            project_id, request.shot_id, request.narration, request.visual_description
        )
        return SuccessResponse(success=True, message="已更新", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新帧失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/regenerate-frame-image/{shot_id}")
async def regenerate_frame_image(
    project_id: str, shot_id: int, request: RegenerateFrameImageRequest
):
    """重新生成单帧分镜图"""
    try:
        result = await preview_service.regenerate_frame_image(
            project_id, shot_id, request.feedback, global_style=request.global_style
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"重新生成帧图片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/produce-video")
async def produce_video(project_id: str):
    """SSE: 视频生成（图生视频+TTS+FFmpeg合成）"""
    return _sse_stream(preview_service.produce_video(project_id))


# ==================== V3: 数据驱动脚本生成 ====================


@router.post("/smart-create-v2")
async def smart_create_v2(request: SmartCreateV2Request):
    """
    数据驱动智能创作V3: 触发异步三方向调研，立即返回session_id

    调研完成后通过 /status 轮询进度，通过 /result 获取结果
    """
    try:
        brand_profile = None
        if request.brand_profile_id:
            from .brand_profiles import _load_profile
            brand_profile = _load_profile(request.brand_profile_id)

        session_id = await script_creator.create_session_v2(
            product_name=request.product_name,
            industry=request.industry,
            target_duration=request.target_duration,
            reference_text=request.reference_text,
            brand_profile=brand_profile,
            product_detail=request.product_detail,
        )

        return {
            "success": True,
            "session_id": session_id,
            "phase": "researching",
            "message": "已启动三方向数据调研，请通过 /status 轮询进度",
        }

    except Exception as e:
        logger.error(f"数据驱动创作启动失败: {e}")
        raise HTTPException(status_code=500, detail=f"创作启动失败: {str(e)}")


@router.get("/{session_id}/status")
async def get_research_status(session_id: str):
    """
    轮询调研进度

    返回: {phase, progress, details}
    phase: searching|analyzing|generating|done|error
    """
    try:
        status = script_creator.get_research_status(session_id)
        return {"success": True, **status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取调研状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/result")
async def get_research_result(session_id: str):
    """
    获取调研结果+3个数据驱动脚本（调研完成后调用）

    返回: {scripts: [...], research_data: {...}}
    """
    try:
        result = script_creator.get_research_result(session_id)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取调研结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/select-data-script", response_model=SuccessResponse)
async def select_data_driven_script(session_id: str, request: SelectScriptRequest):
    """选择数据驱动脚本 → 创建项目"""
    try:
        result = await script_creator.select_data_driven_script(
            session_id, request.script_id
        )
        return SuccessResponse(
            success=True,
            message=f"脚本生成完成，{result['shot_count']}个镜头",
            data=result,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"选择数据驱动脚本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/skip-to-preview", response_model=SuccessResponse)
async def skip_to_preview(session_id: str, request: SkipToPreviewRequest):
    """深度模式: 用户自带脚本直接跳到预览"""
    try:
        result = await script_creator.parse_user_script(
            session_id, request.user_script, request.target_duration
        )
        return SuccessResponse(
            success=True,
            message=f"脚本解析完成，{len(result['shots'])}个镜头",
            data=result,
        )
    except Exception as e:
        logger.error(f"用户脚本解析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
