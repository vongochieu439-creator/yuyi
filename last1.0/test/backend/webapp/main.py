# -*- coding: utf-8 -*-
"""
羽翼Pro V2 - FastAPI Web服务器主程序
"""
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from loguru import logger

from .config import (
    HOST, PORT, CORS_ORIGINS, STATIC_DIR, OUTPUTS_DIR,
    LOG_LEVEL, LOG_FILE
)

# 配置日志
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logger.add(
    LOG_FILE,
    rotation="1 day",
    retention="7 days",
    level=LOG_LEVEL,
    encoding="utf-8"
)

# 创建FastAPI应用
app = FastAPI(
    title="羽翼Pro V2 - Web管理界面",
    description="AI视频生成系统的可视化管理平台",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 静态文件服务 ====================

# 挂载静态文件目录（HTML/CSS/JS）
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

# 挂载视频文件目录（outputs/）
app.mount(
    "/videos",
    StaticFiles(directory=str(OUTPUTS_DIR)),
    name="videos"
)

# 挂载漫剧输出目录
from .config import COMIC_DRAMA_OUTPUT_DIR
COMIC_DRAMA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount(
    "/comic-drama/output",
    StaticFiles(directory=str(COMIC_DRAMA_OUTPUT_DIR)),
    name="comic_drama_output"
)

# 挂载BGM目录
_bgm_dir = STATIC_DIR / "bgm"
_bgm_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/bgm",
    StaticFiles(directory=str(_bgm_dir)),
    name="bgm"
)

# ==================== 路由 ====================

@app.get("/", include_in_schema=False)
async def root():
    """根路径 - 返回主页面"""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return {"message": "欢迎使用羽翼Pro V2 Web管理界面！页面正在开发中..."}
    return FileResponse(str(index_file))

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "outputs_dir": str(OUTPUTS_DIR),
        "outputs_exists": OUTPUTS_DIR.exists()
    }

# ==================== API路由 ====================

from .api import projects, shots, export, keyframes, script, brand_profiles, templates, user_templates, ip_studio, product_profiles, comic_drama, storyboard
app.include_router(projects.router)
app.include_router(shots.router)
app.include_router(export.router)
app.include_router(keyframes.router)
app.include_router(script.router)
app.include_router(brand_profiles.router)
app.include_router(templates.router)
app.include_router(user_templates.router)
app.include_router(ip_studio.router)
app.include_router(product_profiles.router)
app.include_router(comic_drama.router)
app.include_router(storyboard.router)

# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("羽翼Pro V2 Web服务器启动中...")
    logger.info(f"输出目录: {OUTPUTS_DIR}")
    logger.info(f"静态文件目录: {STATIC_DIR}")

    # 检查关键目录
    if not OUTPUTS_DIR.exists():
        logger.warning(f"输出目录不存在: {OUTPUTS_DIR}")
    else:
        video_count = len(list(OUTPUTS_DIR.glob("video_*")))
        logger.info(f"找到 {video_count} 个视频项目")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("羽翼Pro V2 Web服务器关闭")

# ==================== 主程序入口 ====================

if __name__ == "__main__":
    logger.info(f"启动Web服务器: http://{HOST}:{PORT}")
    uvicorn.run(
        "webapp.main:app",
        host=HOST,
        port=PORT,
        reload=False,  # 开发模式下可改为True
        log_level=LOG_LEVEL.lower()
    )
