# -*- coding: utf-8 -*-
"""
阿里云百炼(DashScope) ASR客户端 - Paraformer录音文件识别

使用DashScope的异步录音文件识别API（Paraformer模型）
文档: https://help.aliyun.com/zh/model-studio/developer-reference/paraformer
"""
import time
import asyncio
import tempfile
from pathlib import Path
from typing import Optional
import httpx
from loguru import logger

from ..config import DASHSCOPE_API_KEY


class AliyunASRClient:
    """DashScope语音识别客户端 - Paraformer录音文件识别"""

    # DashScope录音文件识别API
    SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
    QUERY_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or DASHSCOPE_API_KEY

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def transcribe_from_url(self, audio_url: str) -> str:
        """
        通过URL进行语音转文字（支持音频和视频URL）

        Args:
            audio_url: 音频/视频文件的公网URL

        Returns:
            完整的口播文字
        """
        if not self._is_configured():
            logger.warning("DashScope ASR未配置API Key")
            return "[ASR未配置 - 请设置DASHSCOPE_API_KEY]"

        try:
            task_id = await self._submit_task(audio_url)
            if not task_id:
                return ""

            result = await self._poll_result(task_id)
            return result

        except Exception as e:
            logger.error(f"DashScope ASR转写失败: {e}")
            return ""

    async def transcribe_from_file(self, file_path: str) -> str:
        """
        从本地文件进行语音转文字
        注意: DashScope需要公网URL，本地文件需先上传
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"文件不存在: {file_path}")
            return ""

        logger.warning("DashScope ASR需要公网URL，本地文件暂不支持直接转写")
        return "[本地文件转写暂不支持，请使用URL方式]"

    async def _submit_task(self, file_url: str) -> Optional[str]:
        """提交异步录音文件识别任务"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",  # 异步模式
        }

        payload = {
            "model": "paraformer-v2",
            "input": {
                "file_urls": [file_url]
            },
            "parameters": {
                "language_hints": ["zh"],
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self.SUBMIT_URL,
                    json=payload,
                    headers=headers,
                )

                data = resp.json()

                if resp.status_code not in (200, 201):
                    logger.error(f"ASR提交任务失败: status={resp.status_code}, body={str(data)[:300]}")
                    return None

                # DashScope异步任务返回格式
                task_id = data.get("output", {}).get("task_id", "")
                if task_id:
                    logger.info(f"ASR任务提交成功: task_id={task_id}")
                    return task_id

                logger.error(f"ASR返回无task_id: {data}")
                return None

        except Exception as e:
            logger.error(f"ASR提交任务异常: {e}")
            return None

    async def _poll_result(self, task_id: str, max_wait: int = 90) -> str:
        """轮询获取转写结果"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        url = self.QUERY_URL.format(task_id=task_id)
        start = time.time()

        while time.time() - start < max_wait:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(url, headers=headers)

                    if resp.status_code != 200:
                        logger.warning(f"ASR查询失败: status={resp.status_code}, body={resp.text[:200]}")
                        await asyncio.sleep(3)
                        continue

                    data = resp.json()
                    output = data.get("output", {})
                    status = output.get("task_status", "")

                    if status == "SUCCEEDED":
                        return self._extract_text(output)

                    elif status == "FAILED":
                        error_msg = output.get("message", "未知错误")
                        error_code = output.get("code", "")
                        logger.error(f"ASR转写失败: code={error_code}, msg={error_msg}")
                        return ""

                    elif status in ("PENDING", "RUNNING"):
                        logger.debug(f"ASR任务进行中: {status}")
                        await asyncio.sleep(3)
                        continue

                    else:
                        logger.warning(f"ASR未知状态: {status}, data={str(data)[:200]}")
                        await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"ASR轮询异常: {e}")
                await asyncio.sleep(3)

        logger.error(f"ASR转写超时 ({max_wait}s)")
        return ""

    def _extract_text(self, output: dict) -> str:
        """从DashScope转写结果中提取文字"""
        texts = []

        # DashScope Paraformer返回格式:
        # output.results[].transcription_url -> 需要再请求获取内容
        # 或 output.results[].transcription.paragraphs[].words[].text
        results = output.get("results", [])

        for r in results:
            # 方式1: 直接内嵌转写结果
            transcription = r.get("transcription", {})
            if isinstance(transcription, dict):
                paragraphs = transcription.get("paragraphs", [])
                for para in paragraphs:
                    words = para.get("words", [])
                    para_text = "".join(w.get("text", "") for w in words)
                    if para_text:
                        texts.append(para_text)

                # 也可能直接有text字段
                if not paragraphs and transcription.get("text"):
                    texts.append(transcription["text"])

            # 方式2: transcription_url需要额外请求 (同步方式暂不处理)
            if r.get("transcription_url") and not texts:
                logger.info(f"ASR结果在transcription_url中，需要额外请求")
                # 这种情况会在后面通过_fetch_transcription_url处理

            # 方式3: 直接有text
            if r.get("text") and not texts:
                texts.append(r["text"])

        # 如果results里有transcription_url但没有直接文本
        if not texts:
            for r in results:
                url = r.get("transcription_url", "")
                if url:
                    texts.append(f"[转写结果URL: {url}]")
                    # TODO: 异步请求这个URL获取完整文本

        full_text = "".join(texts)
        logger.info(f"ASR转写成功: {len(full_text)}字")
        return full_text

    async def fetch_transcription_url(self, url: str) -> str:
        """获取transcription_url中的完整文本"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    # 提取文本
                    transcripts = data.get("transcripts", [])
                    texts = []
                    for t in transcripts:
                        sentences = t.get("sentences", [])
                        for s in sentences:
                            text = s.get("text", "")
                            if text:
                                texts.append(text)
                    return "".join(texts)
                else:
                    logger.error(f"获取转写URL失败: status={resp.status_code}")
                    return ""
        except Exception as e:
            logger.error(f"获取转写URL异常: {e}")
            return ""
