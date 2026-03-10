# -*- coding: utf-8 -*-
"""
阶跃星辰 Step-audio-2 Realtime WebSocket 客户端
负责：管理与阶跃星辰的WebSocket连接，收发音频和事件
"""
import json
import asyncio
from typing import Optional, Callable, List
from loguru import logger

try:
    import websockets
except ImportError:
    websockets = None


class StepfunRealtimeClient:
    """阶跃星辰 Step-audio-2 Realtime API 客户端"""

    def __init__(self, api_key: str, model_url: str, voice: str = "qingchunshaonv"):
        self.api_key = api_key
        self.model_url = model_url
        self.voice = voice
        self.ws = None
        self._listen_task: Optional[asyncio.Task] = None

        # 回调函数
        self.on_audio_delta: Optional[Callable] = None       # (base64_chunk) -> None
        self.on_transcript: Optional[Callable] = None        # (role, text) -> None
        self.on_speech_started: Optional[Callable] = None    # () -> None
        self.on_speech_stopped: Optional[Callable] = None    # () -> None
        self.on_tool_call: Optional[Callable] = None         # (name, args) -> None
        self.on_response_done: Optional[Callable] = None     # () -> None

        # 累积转录文本
        self._ai_transcript_buffer = ""

    async def connect(self):
        """建立WebSocket连接"""
        if websockets is None:
            raise RuntimeError("需要安装 websockets 库: pip install websockets")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        logger.info(f"连接阶跃星辰 Realtime API: {self.model_url}")
        self.ws = await websockets.connect(
            self.model_url,
            extra_headers=headers,
            ping_interval=20,
            ping_timeout=10,
            max_size=10 * 1024 * 1024,  # 10MB
        )
        logger.info("阶跃星辰 Realtime API 连接成功")

    async def send_session_update(self, instructions: str, tools: Optional[List[dict]] = None):
        """发送 session.update 配置 system prompt + voice + tools"""
        session_config = {
            "modalities": ["text", "audio"],
            "instructions": instructions,
            "voice": self.voice,
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_transcription": {
                "model": "step-audio-2"
            },
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.8,
                "prefix_padding_ms": 400,
                "silence_duration_ms": 1500,
            },
            "temperature": 0.8,
        }
        if tools:
            session_config["tools"] = tools
            session_config["tool_choice"] = "auto"

        event = {
            "type": "session.update",
            "session": session_config
        }
        await self._send(event)
        logger.info("已发送 session.update")

    async def send_audio_chunk(self, audio_base64: str):
        """转发用户音频块: input_audio_buffer.append"""
        event = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }
        await self._send(event)

    async def send_text_message(self, text: str):
        """发送文本消息让AI说出来: conversation.item.create + response.create"""
        # 创建对话项
        item_event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": text
                    }
                ]
            }
        }
        await self._send(item_event)

        # 触发响应
        response_event = {
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"]
            }
        }
        await self._send(response_event)

    async def cancel_response(self):
        """取消当前AI回复（用于打断）"""
        event = {"type": "response.cancel"}
        await self._send(event)
        logger.debug("已发送 response.cancel")

    async def listen(self):
        """持续监听服务端事件，分发到回调"""
        if not self.ws:
            raise RuntimeError("WebSocket未连接")

        try:
            async for raw_msg in self.ws:
                try:
                    event = json.loads(raw_msg)
                    await self._dispatch_event(event)
                except json.JSONDecodeError:
                    logger.warning(f"收到非JSON消息: {raw_msg[:100]}")
                except Exception as e:
                    logger.error(f"事件处理异常: {e}")
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"阶跃星辰连接关闭: {e}")
        except Exception as e:
            logger.error(f"监听异常: {e}")

    async def start_listening(self):
        """启动后台监听任务"""
        self._listen_task = asyncio.create_task(self.listen())

    async def close(self):
        """关闭连接"""
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except (asyncio.CancelledError, Exception):
                pass
        if self.ws:
            try:
                await asyncio.wait_for(self.ws.close(), timeout=3.0)
            except Exception:
                pass
            self.ws = None
        logger.info("阶跃星辰连接已关闭")

    async def _send(self, event: dict):
        """发送事件到WebSocket"""
        if not self.ws:
            logger.warning("WebSocket未连接，无法发送事件")
            return
        await self.ws.send(json.dumps(event))

    async def _dispatch_event(self, event: dict):
        """分发服务端事件到回调"""
        event_type = event.get("type", "")

        if event_type == "response.audio.delta":
            # AI音频块
            delta = event.get("delta", "")
            if delta and self.on_audio_delta:
                await self._call(self.on_audio_delta, delta)

        elif event_type == "conversation.item.input_audio_transcription.completed":
            # 用户语音转录完成
            text = event.get("transcript", "").strip()
            if text and self.on_transcript:
                await self._call(self.on_transcript, "user", text)

        elif event_type == "response.audio_transcript.delta":
            # AI转录增量
            delta = event.get("delta", "")
            self._ai_transcript_buffer += delta

        elif event_type == "response.audio_transcript.done":
            # AI转录完成
            text = event.get("transcript", self._ai_transcript_buffer).strip()
            self._ai_transcript_buffer = ""
            if text and self.on_transcript:
                await self._call(self.on_transcript, "ai", text)

        elif event_type == "response.function_call_arguments.done":
            # AI触发tool call
            name = event.get("name", "")
            args_str = event.get("arguments", "{}")
            if self.on_tool_call:
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {}
                await self._call(self.on_tool_call, name, args)

        elif event_type == "input_audio_buffer.speech_started":
            if self.on_speech_started:
                await self._call(self.on_speech_started)

        elif event_type == "input_audio_buffer.speech_stopped":
            if self.on_speech_stopped:
                await self._call(self.on_speech_stopped)

        elif event_type == "response.done":
            if self.on_response_done:
                await self._call(self.on_response_done)

        elif event_type == "error":
            error = event.get("error", {})
            logger.error(f"阶跃星辰错误: {error}")

        elif event_type in ("session.created", "session.updated"):
            logger.info(f"阶跃星辰事件: {event_type}")

    @staticmethod
    async def _call(fn, *args):
        """调用回调（支持同步和异步）"""
        if asyncio.iscoroutinefunction(fn):
            await fn(*args)
        else:
            fn(*args)
