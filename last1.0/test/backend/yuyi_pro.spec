# -*- mode: python ; coding: utf-8 -*-
"""
羽翼Pro V2 - PyInstaller 构建配置
用法: pyinstaller yuyi_pro.spec
"""

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('webapp/static', 'webapp/static'),
    ],
    hiddenimports=[
        # FastAPI / Starlette
        'fastapi',
        'fastapi.staticfiles',
        'fastapi.responses',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'starlette',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.responses',
        'starlette.staticfiles',
        'starlette.formparsers',
        # Uvicorn
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # Pydantic
        'pydantic',
        'pydantic._internal',
        'pydantic._internal._core_utils',
        'pydantic._internal._validators',
        'pydantic._internal._generate_schema',
        'pydantic._internal._generics',
        # httpx
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
        'httpcore',
        'httpcore._async',
        'httpcore._sync',
        # Multipart
        'multipart',
        'python_multipart',
        # Loguru
        'loguru',
        # App modules
        'webapp',
        'webapp.main',
        'webapp.config',
        'webapp.runtime',
        'webapp.api',
        'webapp.api.projects',
        'webapp.api.shots',
        'webapp.api.export',
        'webapp.api.keyframes',
        'webapp.api.script',
        'webapp.api.brand_profiles',
        'webapp.models',
        'webapp.models.schemas',
        'webapp.services',
        'webapp.services.metadata_manager',
        'webapp.services.project_manager',
        'webapp.services.gemini_client',
        'webapp.services.nanobanana_client',
        'webapp.services.keyframe_generator',
        'webapp.services.image_to_video_client',
        'webapp.services.video_generator',
        'webapp.services.video_merger',
        'webapp.services.ai_scorer',
        'webapp.services.tikhub_client',
        'webapp.services.tavily_client',
        'webapp.services.script_creator',
        # Encodings (Windows CJK)
        'encodings',
        'encodings.utf_8',
        'encodings.gbk',
        'encodings.gb2312',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'cv2',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='YuyiPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='YuyiPro',
)
