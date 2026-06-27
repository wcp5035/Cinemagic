# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Cinemagic."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

block_cipher = None
project_root = Path(SPECPATH)

datas = [
    (str(project_root / "webui"), "webui"),
    (str(project_root / "resource"), "resource"),
    (str(project_root / "app" / "services" / "data"), "app/services/data"),
    (str(project_root / "config.example.toml"), "."),
]
binaries = []
hiddenimports = [
    "app.asgi",
    "app.router",
    "app.config",
    "app.config.config",
    "app.controllers.v1.video",
    "app.controllers.v1.llm",
    "app.controllers.ping",
    "app.controllers.manager.redis_manager",
    "app.controllers.manager.memory_manager",
    "app.services.task",
    "app.services.video",
    "app.services.voice",
    "app.services.subtitle",
    "app.services.llm",
    "app.services.material",
    "app.services.state",
    "app.services.upload_post",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "streamlit.web.cli",
    "streamlit.runtime.scriptrunner.magic_funcs",
    "streamlit.runtime.scriptrunner.script_runner",
    "streamlit.web.server.server",
    "edge_tts",
    "faster_whisper",
    "ctranslate2",
    "onnxruntime",
    "av",
    "moviepy",
    "imageio_ffmpeg",
    "litellm",
    "google.generativeai",
    "dashscope",
    "azure.cognitiveservices.speech",
    "pydub",
    "toml",
    "multipart",
]

for package in (
    "streamlit",
    "altair",
    "pydeck",
    "plotly",
    "tornado",
    "validators",
    "click",
    "packaging",
    "imageio",
    "imageio_ffmpeg",
    "moviepy",
):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

for package in (
    "streamlit",
    "altair",
    "pydeck",
    "imageio",
    "imageio-ffmpeg",
    "moviepy",
    "faster-whisper",
    "onnxruntime",
    "ctranslate2",
    "av",
    "numpy",
    "pandas",
    "pillow",
    "decorator",
    "proglog",
):
    try:
        datas += copy_metadata(package)
    except Exception:
        pass

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[
        str(project_root / "hooks" / "pyi_rth_metadata.py"),
        str(project_root / "hooks" / "pyi_rth_cinemagic.py"),
    ],
    excludes=[
        "matplotlib",
        "tkinter",
        "PyQt5",
        "PySide6",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Cinemagic",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Cinemagic",
)
