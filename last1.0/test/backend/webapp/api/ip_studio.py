# -*- coding: utf-8 -*-
"""
个人IP工作室 API 路由 - 增强版（含语音访谈WebSocket）
"""
import json
import re
import asyncio
import time
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
from loguru import logger

from ..services import ip_service as svc
from ..services.stepfun_realtime import StepfunRealtimeClient
from ..services.interview_brain import InterviewBrain
from ..config import STEPFUN_API_KEY, STEPFUN_REALTIME_URL, STEPFUN_VOICE

router = APIRouter(prefix="/api/ip-studio", tags=["ip-studio"])

# H5: 并发WebSocket连接计数器
_active_ws_connections = 0
_MAX_WS_CONNECTIONS = 10


# ==================== 数据模型 ====================

# H7: 类型化聊天消息
class ChatMessage(BaseModel):
    role: str = Field(..., pattern=r'^(ai|user|system)$')
    content: str = Field(..., max_length=5000)


# M10: 类型化topic字段
class TopicDict(BaseModel):
    model_config = {"extra": "allow"}
    title: str = Field(default="", max_length=200)
    hook_opening: str = Field(default="", max_length=500)
    core_angle: str = Field(default="", max_length=500)


class InterviewRequest(BaseModel):
    name: str = Field(..., description="受访者姓名/称呼", max_length=50)
    industry: str = Field(..., description="行业", max_length=50)
    chat_history: List[ChatMessage] = Field(default_factory=list, description="完整对话历史 [{role, content}]")
    phase: str = Field(default="background", description="访谈阶段: background|hot_topics|cognitive|voice")
    hot_topics: str = Field(default="", description="热点话题列表文本（用于hot_topics阶段）", max_length=2000)


class FinalizeRequest(BaseModel):
    name: str = Field(..., max_length=50)
    industry: str = Field(..., max_length=50)
    role: str = Field(default="创始人", description="职位/角色", max_length=50)
    chat_history: List[ChatMessage]


class GenerateTopicsRequest(BaseModel):
    profile_id: str
    count: int = Field(default=15, ge=5, le=20)


class GenerateScriptRequest(BaseModel):
    profile_id: str
    topic: TopicDict = Field(..., description="选题对象")
    duration: int = Field(default=90, ge=30, le=300, description="目标时长（秒）")


class ScriptFeedbackRequest(BaseModel):
    profile_id: str = Field(..., description="IP档案ID")
    rejected_paragraphs: List[str] = Field(default_factory=list, description="被标记为'不像我'的段落列表")
    edits: List[Dict] = Field(default_factory=list, description="用户编辑记录 [{original_text, edited_text, paragraph_index, topic_title}]")
    notes: str = Field(default="", description="用户备注", max_length=1000)


class SupplementRequest(BaseModel):
    profile_id: str = Field(..., description="IP档案ID")
    chat_history: List[ChatMessage] = Field(..., description="补充访谈对话历史 [{role, content}]")


# H6: WebSocket输入清理
def _sanitize_ws_input(text: str, max_length: int = 50) -> str:
    """清理WebSocket输入：限长度+过滤控制字符"""
    if not text:
        return ""
    text = text[:max_length]
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()


# ==================== 档案管理 ====================

@router.get("/profiles")
async def list_profiles():
    """获取所有IP档案"""
    profiles = svc.get_all_profiles()
    # M5: 一次加载所有topics，避免N+1查询
    all_topics = svc._load_topics()
    summaries = []
    for p in profiles:
        summaries.append({
            "profile_id": p["profile_id"],
            "name": p["name"],
            "industry": p["industry"],
            "role": p.get("role", ""),
            "ip_positioning": p.get("ip_positioning", ""),
            "content_pillars": p.get("content_pillars", []),
            "created_at": p.get("created_at", ""),
            "topic_count": len(all_topics.get(p["profile_id"], []))
        })
    return {"profiles": summaries, "total": len(summaries)}


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """获取IP档案详情"""
    profile = svc.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="IP档案不存在")
    return profile


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """删除IP档案"""
    if not await svc.delete_profile(profile_id):
        raise HTTPException(status_code=404, detail="IP档案不存在")
    return {"success": True, "message": "已删除"}


# ==================== AI记者访谈 ====================

@router.post("/interview/next-question")
async def next_question(request: InterviewRequest):
    """
    AI记者动态访谈 - 根据对话历史和当前阶段返回下一个问题
    phase: background|cognitive|voice
    """
    try:
        # H7: 用model_dump()转换ChatMessage为dict
        result = await svc.conduct_interview(
            name=request.name,
            industry=request.industry,
            chat_history=[m.model_dump() for m in request.chat_history],
            phase=request.phase,
            hot_topics=request.hot_topics
        )
        return result
    except Exception as e:
        logger.error(f"访谈问题生成失败: {e}")
        # H8: 错误信息脱敏
        raise HTTPException(status_code=500, detail="AI访谈失败，请稍后重试")


@router.post("/interview/finalize")
async def finalize_interview(request: FinalizeRequest):
    """
    访谈结束后，AI提炼完整IP档案并保存（2步合成：事实+认知）
    """
    try:
        profile = await svc.finalize_profile(
            name=request.name,
            industry=request.industry,
            role=request.role,
            chat_history=[m.model_dump() for m in request.chat_history]
        )
        return {"success": True, "profile": profile}
    except Exception as e:
        logger.error(f"IP档案提炼失败: {e}")
        raise HTTPException(status_code=500, detail="档案提炼失败，请稍后重试")


# ==================== 补充访谈 ====================

@router.post("/interview/supplement")
async def supplement_interview(request: SupplementRequest):
    """
    补充访谈 - 只提取新观点和表达模式，追加到现有档案
    """
    try:
        profile = await svc.supplement_profile(
            profile_id=request.profile_id,
            chat_history=[m.model_dump() for m in request.chat_history]
        )
        return {"success": True, "profile": profile}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"补充访谈失败: {e}")
        raise HTTPException(status_code=500, detail="补充访谈失败，请稍后重试")


# ==================== 选题生成 ====================

@router.post("/topics/generate")
async def generate_topics(request: GenerateTopicsRequest):
    """基于IP档案批量生成选题库"""
    try:
        topics = await svc.generate_topics(
            profile_id=request.profile_id,
            count=request.count
        )
        return {"success": True, "topics": topics, "total": len(topics)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"选题生成失败: {e}")
        raise HTTPException(status_code=500, detail="选题生成失败，请稍后重试")


# M9: industry路径参数加 :path 允许含 /
@router.get("/topics/{profile_id}")
async def get_topics(profile_id: str):
    """获取某个IP的选题库"""
    topics = svc.get_topics_for_profile(profile_id)
    return {"topics": topics, "total": len(topics)}


# ==================== 脚本生成 ====================

@router.post("/script/generate")
async def generate_script(request: GenerateScriptRequest):
    """基于IP档案和选题生成脚本（3步：Think→Write→DeAI）"""
    try:
        result = await svc.generate_script(
            profile_id=request.profile_id,
            topic=request.topic.model_dump(),
            duration=request.duration
        )
        return {"success": True, "script": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"脚本生成失败: {e}")
        raise HTTPException(status_code=500, detail="脚本生成失败，请稍后重试")


# ==================== 脚本反馈 ====================

@router.post("/script/feedback")
async def script_feedback(request: ScriptFeedbackRequest):
    """
    脚本段落反馈 - 用户标记"不像我"的段落 + 直接编辑
    分析后更新档案中的声音指纹禁用词和表达模式
    """
    try:
        result = await svc.update_profile_from_feedback(
            profile_id=request.profile_id,
            rejected_paragraphs=request.rejected_paragraphs,
            edits=request.edits,
            notes=request.notes
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"反馈处理失败: {e}")
        raise HTTPException(status_code=500, detail="反馈处理失败，请稍后重试")


# ==================== 热点话题 ====================

# M9: industry路径参数加 :path
@router.get("/hot-topics/{industry:path}")
async def get_hot_topics(industry: str):
    """获取行业热点话题"""
    try:
        topics = await svc.fetch_hot_topics_for_industry(industry)
        return {"success": True, "topics": topics, "total": len(topics)}
    except Exception as e:
        logger.error(f"热点话题获取失败: {e}")
        raise HTTPException(status_code=500, detail="热点话题获取失败，请稍后重试")


# ==================== 实时语音访谈 WebSocket ====================

@router.websocket("/interview/live")
async def interview_live(ws: WebSocket, token: str = Query(default="")):
    """实时语音访谈WebSocket端点 - StepFun全权负责对话"""
    global _active_ws_connections

    # H4+H5: 必须先 accept 才能 close（FastAPI 要求）
    await ws.accept()

    # H4: WebSocket认证 - token参数校验（空token跳过，兼容无认证场景）
    if token and len(token) < 8:
        try:
            await ws.send_json({"type": "error", "message": "认证失败"})
            await ws.close(code=4001, reason="认证失败")
        except Exception:
            pass
        return

    # H5: 并发连接限制
    if _active_ws_connections >= _MAX_WS_CONNECTIONS:
        try:
            await ws.send_json({"type": "error", "message": "连接数已满，请稍后重试"})
            await ws.close(code=4002, reason="连接数已满")
        except Exception:
            pass
        return

    _active_ws_connections += 1
    logger.info("语音访谈 WebSocket 已连接")

    stepfun: Optional[StepfunRealtimeClient] = None
    brain: Optional[InterviewBrain] = None
    call_ended = False
    ai_speaking = False
    ai_speaking_since: Optional[float] = None  # C5: ai_speaking 时间戳
    watchdog_task: Optional[asyncio.Task] = None  # C5: 看门狗任务
    listener_task: Optional[asyncio.Task] = None  # C6: 监听任务

    # C7: send_to_browser 失败时设 call_ended
    async def send_to_browser(msg: dict):
        nonlocal call_ended
        try:
            if not call_ended:
                await ws.send_json(msg)
        except Exception as e:
            logger.warning(f"发送浏览器消息失败: {e}")
            call_ended = True

    # C5: ai_speaking看门狗 — 超过15秒自动重置
    async def _ai_speaking_watchdog():
        nonlocal ai_speaking, ai_speaking_since
        while not call_ended:
            await asyncio.sleep(2)
            if ai_speaking and ai_speaking_since is not None:
                elapsed = time.monotonic() - ai_speaking_since
                if elapsed > 15:
                    logger.warning(f"ai_speaking卡死 {elapsed:.1f}s，自动重置")
                    ai_speaking = False
                    ai_speaking_since = None
                    await send_to_browser({"type": "ai_speaking_done"})

    # ===== 阶跃星辰回调 =====

    async def on_audio_delta(base64_chunk: str):
        nonlocal ai_speaking, ai_speaking_since
        if not ai_speaking:
            ai_speaking_since = time.monotonic()
        ai_speaking = True
        await send_to_browser({"type": "ai_audio", "data": base64_chunk})

    async def on_transcript(role: str, text: str):
        nonlocal ai_speaking
        if not text or not text.strip():
            return

        if role == "ai":
            await send_to_browser({"type": "transcript", "role": "ai", "text": text})
            if brain:
                brain.add_transcript("ai", text)
                new_phase = brain.detect_phase_from_transcript()
                if new_phase:
                    await send_to_browser({
                        "type": "phase_change",
                        "phase": new_phase,
                        "message": f"进入{new_phase}阶段"
                    })
                if brain.is_interview_done():
                    chat_history = brain.get_chat_history()
                    try:
                        await ws.send_json({
                            "type": "interview_done",
                            "chat_history": chat_history
                        })
                    except Exception:
                        pass

        elif role == "user":
            if ai_speaking:
                logger.debug(f"忽略回声: {text[:40]}")
                return
            await send_to_browser({"type": "transcript", "role": "user", "text": text})
            if brain:
                brain.add_transcript("user", text)

    # M6: 打断AI说话(barge-in) — 不再在ai_speaking时直接return
    async def on_speech_started():
        nonlocal ai_speaking, ai_speaking_since
        if ai_speaking:
            # barge-in: 用户打断AI说话，重置标志并取消当前回复
            logger.info("用户打断AI说话(barge-in)")
            ai_speaking = False
            ai_speaking_since = None
            if stepfun:
                try:
                    await stepfun.cancel_response()
                except Exception:
                    pass
            await send_to_browser({"type": "ai_speaking_done"})
        await send_to_browser({"type": "user_speaking_start"})

    async def on_speech_stopped():
        nonlocal ai_speaking
        if ai_speaking:
            return
        await send_to_browser({"type": "user_speaking_done"})

    async def on_response_done():
        nonlocal ai_speaking, ai_speaking_since
        ai_speaking = False
        ai_speaking_since = None
        await send_to_browser({"type": "ai_speaking_done"})

    # C6: 后台监听包装函数
    async def _run_listener():
        nonlocal call_ended
        try:
            await stepfun.start_listening()
        except Exception as e:
            logger.error(f"StepFun监听异常: {e}")
            call_ended = True
            await send_to_browser({"type": "error", "message": "语音服务异常断开"})

    # ===== 主流程 =====
    try:
        # M7: 初始消息超时 10秒
        try:
            init_raw = await asyncio.wait_for(ws.receive_text(), timeout=10)
        except asyncio.TimeoutError:
            await send_to_browser({"type": "error", "message": "初始化超时"})
            return

        # M8: 畸形JSON处理
        try:
            init_data = json.loads(init_raw)
        except json.JSONDecodeError:
            await send_to_browser({"type": "error", "message": "无效的JSON格式"})
            return

        if init_data.get("type") != "init":
            await send_to_browser({"type": "error", "message": "首条消息必须是init"})
            return

        # H6: 输入清理
        name = _sanitize_ws_input(init_data.get("name", ""), max_length=50)
        industry = _sanitize_ws_input(init_data.get("industry", ""), max_length=50)
        role = _sanitize_ws_input(init_data.get("role", "创始人"), max_length=50)

        if not name or not industry:
            await send_to_browser({"type": "error", "message": "缺少name或industry"})
            return

        logger.info(f"语音访谈开始: {name}, {industry}, {role}")

        # 2. 创建brain（只做状态管理）和StepFun客户端
        brain = InterviewBrain(name, industry, role)

        # 2.1 后台获取热点话题并注入brain
        try:
            hot_topics = await svc.fetch_hot_topics_for_industry(industry)
            hot_topics_text = "\n".join(
                f"- {t.get('title', '')}: {t.get('angle', '你怎么看？')}"
                for t in hot_topics
            )
            brain.set_hot_topics(hot_topics_text)
            await send_to_browser({"type": "hot_topics_ready", "count": len(hot_topics)})
        except Exception as e:
            logger.warning(f"热点话题获取失败（不影响访谈）: {e}")

        stepfun = StepfunRealtimeClient(
            api_key=STEPFUN_API_KEY,
            model_url=STEPFUN_REALTIME_URL,
            voice=STEPFUN_VOICE
        )

        # 3. 设置回调
        stepfun.on_audio_delta = on_audio_delta
        stepfun.on_transcript = on_transcript
        stepfun.on_speech_started = on_speech_started
        stepfun.on_speech_stopped = on_speech_stopped
        stepfun.on_response_done = on_response_done

        # 4. 连接阶跃星辰
        try:
            await stepfun.connect()
        except Exception as e:
            logger.error(f"阶跃星辰连接失败: {e}")
            # H8: 错误信息脱敏
            await send_to_browser({"type": "error", "message": "语音服务连接失败，请稍后重试"})
            return

        # 5. 发送session配置（包含完整3阶段访谈策略）
        await stepfun.send_session_update(brain.get_system_prompt())

        # 6. 通知浏览器已连接
        await send_to_browser({"type": "connected"})

        # 7. 触发AI说第一句话（发一条指令让AI主动开口）
        await send_to_browser({"type": "ai_speaking_start"})
        await stepfun.send_text_message(
            f"请开始访谈，先跟{name}打个招呼，然后问第一个背景问题。"
        )

        # C5: 启动看门狗
        watchdog_task = asyncio.create_task(_ai_speaking_watchdog())

        # C6: 启动后台监听(create_task替代await)
        listener_task = asyncio.create_task(_run_listener())

        # 8. 接收浏览器消息循环
        while not call_ended:
            try:
                raw = await ws.receive_text()
                # M8: 畸形JSON处理
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await send_to_browser({"type": "error", "message": "无效的消息格式"})
                    continue
                msg_type = msg.get("type", "")

                if msg_type == "audio":
                    audio_data = msg.get("data", "")
                    if audio_data and stepfun and not ai_speaking:
                        await stepfun.send_audio_chunk(audio_data)

                elif msg_type == "end_call":
                    logger.info("用户结束通话")
                    chat_history = brain.get_chat_history() if brain else []
                    try:
                        await ws.send_json({
                            "type": "interview_done",
                            "chat_history": chat_history
                        })
                    except Exception:
                        pass
                    call_ended = True
                    break

            except WebSocketDisconnect:
                logger.info("浏览器WebSocket断开")
                break
            except Exception as e:
                logger.error(f"消息处理异常: {e}")
                break

    except WebSocketDisconnect:
        logger.info("语音访谈WebSocket断开")
    except Exception as e:
        logger.error(f"语音访谈异常: {e}")
        try:
            # H8: 错误信息脱敏
            await send_to_browser({"type": "error", "message": "语音访谈发生异常，请重试"})
        except Exception:
            pass
    finally:
        call_ended = True
        # C5: 取消看门狗
        if watchdog_task and not watchdog_task.done():
            watchdog_task.cancel()
            try:
                await watchdog_task
            except (asyncio.CancelledError, Exception):
                pass
        # C6: 取消监听任务
        if listener_task and not listener_task.done():
            listener_task.cancel()
            try:
                await listener_task
            except (asyncio.CancelledError, Exception):
                pass
        if stepfun:
            try:
                await stepfun.close()
            except Exception:
                pass
        _active_ws_connections -= 1
        logger.info("语音访谈结束")
