import multiprocessing
import os
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

STREAMLIT_FLAG = "--cinemagic-streamlit"


def _is_streamlit_child() -> bool:
    return len(sys.argv) > 1 and sys.argv[1] == STREAMLIT_FLAG


def _streamlit_argv() -> list[str]:
    from app.utils.paths import bundle_root

    webui_script = Path(bundle_root()) / "webui" / "Main.py"
    webui_host = os.environ.get("MPT_WEBUI_HOST", "127.0.0.1")
    webui_port = os.environ.get("MPT_WEBUI_PORT", "8501")
    return [
        "streamlit",
        "run",
        str(webui_script),
        "--global.developmentMode=false",
        f"--server.address={webui_host}",
        f"--server.port={webui_port}",
        f"--browser.serverAddress={webui_host}",
        "--browser.gatherUsageStats=False",
        "--server.showEmailPrompt=False",
        "--server.headless=true",
        "--server.enableCORS=True",
    ]


def _run_streamlit_child() -> None:
    from streamlit.web import cli as stcli

    sys.argv = _streamlit_argv()
    stcli.main()


def _write_startup_error(exc: BaseException) -> None:
    from app.utils.paths import app_root

    log_path = Path(app_root()) / "startup_error.log"
    log_path.write_text(traceback.format_exc(), encoding="utf-8")
    print(f"\nStartup failed. Details saved to:\n{log_path}\n", file=sys.stderr)


def _start_webui(root_dir: Path) -> None:
    from app.utils.paths import is_frozen

    try:
        if is_frozen():
            env = os.environ.copy()
            subprocess.Popen(
                [sys.executable, STREAMLIT_FLAG],
                cwd=str(root_dir),
                env=env,
            )
            return

        env = os.environ.copy()
        env["PYTHONPATH"] = str(root_dir)
        subprocess.Popen(
            [sys.executable, "-m", *_streamlit_argv()],
            cwd=str(root_dir),
            env=env,
        )
    except Exception:
        from loguru import logger

        logger.exception("failed to start webui")


def _open_webui_in_browser() -> None:
    webui_host = os.environ.get("MPT_WEBUI_HOST", "127.0.0.1")
    webui_port = os.environ.get("MPT_WEBUI_PORT", "8501")
    time.sleep(3)
    webui_url = f"http://{webui_host}:{webui_port}"
    from loguru import logger

    logger.info(f"opening browser: {webui_url}")
    webbrowser.open(webui_url)


def main() -> None:
    import uvicorn
    from loguru import logger

    from app.asgi import app as asgi_app
    from app.config import config
    from app.utils import utils
    from app.utils.paths import app_root

    root_dir = Path(app_root())
    utils.storage_dir("", create=True)
    utils.task_dir()

    webui_host = os.environ.get("MPT_WEBUI_HOST", "127.0.0.1")
    webui_port = os.environ.get("MPT_WEBUI_PORT", "8501")
    webui_url = f"http://{webui_host}:{webui_port}"
    api_docs_url = f"http://127.0.0.1:{config.listen_port}/docs"
    logger.info(f"start webui: {webui_url}")
    logger.info(f"start api server, docs: {api_docs_url}")

    threading.Thread(target=_start_webui, args=(root_dir,), daemon=True).start()
    threading.Thread(target=_open_webui_in_browser, daemon=True).start()
    uvicorn.run(
        asgi_app,
        host=config.listen_host,
        port=config.listen_port,
        log_level="warning",
    )


if __name__ == "__main__":
    multiprocessing.freeze_support()

    if _is_streamlit_child():
        try:
            _run_streamlit_child()
        except Exception as exc:
            _write_startup_error(exc)
            input("Press Enter to exit...")
            raise SystemExit(1) from exc
        raise SystemExit(0)

    try:
        main()
    except Exception as exc:
        _write_startup_error(exc)
        input("Press Enter to exit...")
        raise SystemExit(1) from exc
