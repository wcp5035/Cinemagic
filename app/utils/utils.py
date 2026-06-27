import json
import locale
import os
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path
import threading
from typing import Any
from uuid import uuid4

from loguru import logger

from app.models import const


def get_response(status: int, data: Any = None, message: str = ""):
    obj = {
        "status": status,
    }
    if data:
        obj["data"] = data
    if message:
        obj["message"] = message
    return obj


def to_json(obj):
    try:
        # Define a helper function to handle different types of objects
        def serialize(o):
            # If the object is a serializable type, return it directly
            if isinstance(o, (int, float, bool, str)) or o is None:
                return o
            # If the object is binary data, convert it to a base64-encoded string
            elif isinstance(o, bytes):
                return "*** binary data ***"
            # If the object is a dictionary, recursively process each key-value pair
            elif isinstance(o, dict):
                return {k: serialize(v) for k, v in o.items()}
            # If the object is a list or tuple, recursively process each element
            elif isinstance(o, (list, tuple)):
                return [serialize(item) for item in o]
            # If the object is a custom type, attempt to return its __dict__ attribute
            elif hasattr(o, "__dict__"):
                return serialize(o.__dict__)
            # Return None for other cases (or choose to raise an exception)
            else:
                return None

        # Use the serialize function to process the input object
        serialized_obj = serialize(obj)

        # Serialize the processed object into a JSON string
        return json.dumps(serialized_obj, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"failed to serialize object to json: {str(e)}")
        return None


def get_uuid(remove_hyphen: bool = False):
    u = str(uuid4())
    if remove_hyphen:
        u = u.replace("-", "")
    return u


def root_dir():
    from app.utils.paths import app_root

    return app_root()


def storage_dir(sub_dir: str = "", create: bool = False):
    d = os.path.join(root_dir(), "storage")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if create and not os.path.exists(d):
        os.makedirs(d)

    return d


def resource_dir(sub_dir: str = ""):
    from app.utils.paths import bundle_root

    d = os.path.join(bundle_root(), "resource")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    return d


def task_dir(sub_dir: str = ""):
    d = os.path.join(storage_dir(), "tasks")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str, max_length: int = 80) -> str:
    cleaned = _INVALID_FILENAME_CHARS.sub("_", (name or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        cleaned = "video"
    return cleaned[:max_length]


def refresh_video_output_directory() -> str:
    from app.config import config
    from app.config.config import load_config

    value = (load_config().get("app", {}).get("video_output_directory") or "").strip()
    config.app["video_output_directory"] = value
    return value


def get_video_output_directory(create: bool = False) -> str:
    from app.config import config

    raw = (config.app.get("video_output_directory") or "").strip()
    if not raw:
        return ""

    path = raw if os.path.isabs(raw) else os.path.join(root_dir(), raw)
    path = os.path.realpath(os.path.normpath(path))
    if create:
        os.makedirs(path, exist_ok=True)
    return path


def build_final_video_path(
    task_id: str,
    index: int,
    *,
    video_subject: str = "",
    total_count: int = 1,
) -> str:
    output_dir = get_video_output_directory(create=True)
    if output_dir:
        safe_subject = sanitize_filename(video_subject)
        ext = ".mp4"
        filename = (
            f"{safe_subject}{ext}"
            if total_count == 1
            else f"{safe_subject}_{index}{ext}"
        )
        dest = os.path.join(output_dir, filename)
        if os.path.exists(dest):
            suffix = (task_id or get_uuid())[:8]
            stem = os.path.splitext(filename)[0]
            dest = os.path.join(output_dir, f"{stem}_{suffix}{ext}")
        return dest

    return os.path.join(task_dir(task_id), f"final-{index}.mp4")


def export_final_videos(
    video_paths: list[str],
    *,
    video_subject: str = "",
    task_id: str = "",
) -> list[str]:
    output_dir = get_video_output_directory(create=True)
    if not output_dir:
        return []

    safe_subject = sanitize_filename(video_subject)
    exported: list[str] = []
    for index, src in enumerate(video_paths, start=1):
        src_abs = os.path.abspath(os.path.normpath(src or ""))
        if not src_abs or not os.path.isfile(src_abs):
            logger.warning(f"export skipped, video not found: {src}")
            continue

        try:
            if os.path.commonpath([output_dir, src_abs]) == output_dir:
                exported.append(src_abs)
                continue
        except ValueError:
            pass

        ext = os.path.splitext(src_abs)[1] or ".mp4"
        filename = (
            f"{safe_subject}{ext}"
            if len(video_paths) == 1
            else f"{safe_subject}_{index}{ext}"
        )
        dest = os.path.join(output_dir, filename)
        if os.path.exists(dest):
            suffix = (task_id or get_uuid())[:8]
            stem = os.path.splitext(filename)[0]
            dest = os.path.join(output_dir, f"{stem}_{suffix}{ext}")

        try:
            shutil.copy2(src_abs, dest)
        except OSError as exc:
            logger.error(f"failed to export video to {dest}: {exc}")
            continue

        exported.append(dest)
        logger.info(f"exported video to: {dest}")

    return exported


def open_folder(path: str) -> bool:
    folder = (path or "").strip()
    if not folder or not os.path.isdir(folder):
        return False

    import webbrowser

    webbrowser.open(Path(folder).resolve().as_uri())
    return True


def _pick_directory_windows(initial_dir: str, title: str) -> str:
    import ctypes
    from ctypes import wintypes

    shell32 = ctypes.windll.shell32
    ole32 = ctypes.windll.ole32
    user32 = ctypes.windll.user32

    BIF_RETURNONLYFSDIRS = 0x0001
    BIF_NEWDIALOGSTYLE = 0x0040
    BFFM_INITIALIZED = 1
    BFFM_SETSELECTIONW = 0x467

    start_dir = (initial_dir or "").strip()
    if not start_dir or not os.path.isdir(start_dir):
        start_dir = os.path.expanduser("~")

    dir_buffer = ctypes.create_unicode_buffer(start_dir)

    class BROWSEINFO(ctypes.Structure):
        _fields_ = [
            ("hwndOwner", wintypes.HWND),
            ("pidlRoot", ctypes.c_void_p),
            ("pszDisplayName", wintypes.LPWSTR),
            ("lpszTitle", wintypes.LPCWSTR),
            ("ulFlags", wintypes.UINT),
            ("lpfn", ctypes.c_void_p),
            ("lParam", wintypes.LPARAM),
            ("iImage", ctypes.c_int),
        ]

    @ctypes.WINFUNCTYPE(wintypes.LPARAM, wintypes.HWND, wintypes.UINT, wintypes.LPARAM, wintypes.LPARAM)
    def browse_callback(hwnd, msg, _lparam, data):
        if msg == BFFM_INITIALIZED:
            user32.SendMessageW(hwnd, BFFM_SETSELECTIONW, 1, data)
        return 0

    callback = browse_callback
    browse_info = BROWSEINFO()
    browse_info.lpszTitle = title or "Select folder"
    browse_info.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE
    browse_info.lpfn = ctypes.cast(callback, ctypes.c_void_p).value
    browse_info.lParam = ctypes.cast(dir_buffer, wintypes.LPARAM)

    pidl = shell32.SHBrowseForFolderW(ctypes.byref(browse_info))
    if not pidl:
        return ""

    path_buffer = ctypes.create_unicode_buffer(260)
    if not shell32.SHGetPathFromIDListW(pidl, path_buffer):
        ole32.CoTaskMemFree(pidl)
        return ""

    ole32.CoTaskMemFree(pidl)
    return path_buffer.value.strip()


def _pick_directory_tkinter(initial_dir: str, title: str) -> str:
    import tkinter as tk
    from tkinter import filedialog

    start_dir = (initial_dir or "").strip()
    if not start_dir or not os.path.isdir(start_dir):
        start_dir = os.path.expanduser("~")

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askdirectory(
            title=title or "Select folder",
            initialdir=start_dir,
            mustexist=False,
        )
    finally:
        root.destroy()

    return (selected or "").strip()


def pick_directory(initial_dir: str = "", title: str = "") -> str:
    if sys.platform == "win32":
        try:
            return _pick_directory_windows(initial_dir, title)
        except Exception as exc:
            logger.warning(f"native folder picker failed, fallback to tkinter: {exc}")

    try:
        return _pick_directory_tkinter(initial_dir, title)
    except Exception as exc:
        logger.error(f"folder picker unavailable: {exc}")
        return ""


def font_dir(sub_dir: str = ""):
    d = resource_dir("fonts")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def song_dir(sub_dir: str = ""):
    d = resource_dir("songs")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def public_dir(sub_dir: str = ""):
    d = resource_dir("public")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def get_ffmpeg_binary() -> str:
    """
    解析当前进程应该使用的 FFmpeg 可执行文件。

    增加原因：
    1. 视频编码、静音音频生成、pydub 音频转码都依赖 FFmpeg；
    2. Windows 便携包、Docker 和用户自定义安装目录经常出现 PATH 不一致；
    3. 集中解析可以让所有调用方使用同一套优先级，减少某条链路能跑、
       另一条链路找不到 FFmpeg 的现场问题。

    优先级：
    1. IMAGEIO_FFMPEG_EXE：MoviePy/imageio 约定的显式配置；
    2. 系统 PATH 中的 ffmpeg；
    3. imageio-ffmpeg 依赖提供的内置二进制；
    4. 字符串 "ffmpeg" 兜底，交给 subprocess 在运行时暴露更具体错误。
    """
    configured_ffmpeg = os.environ.get("IMAGEIO_FFMPEG_EXE")
    if configured_ffmpeg:
        return configured_ffmpeg

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg

        bundled_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled_ffmpeg:
            return bundled_ffmpeg
    except Exception as exc:
        logger.warning(f"failed to resolve bundled ffmpeg binary: {str(exc)}")

    return "ffmpeg"


def run_in_background(func, *args, **kwargs):
    def run():
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error(f"run_in_background error: {e}", exc_info=True)

    thread = threading.Thread(target=run, daemon=False)
    thread.start()
    return thread


def time_convert_seconds_to_hmsm(seconds) -> str:
    hours = int(seconds // 3600)
    seconds = seconds % 3600
    minutes = int(seconds // 60)
    milliseconds = int(seconds * 1000) % 1000
    seconds = int(seconds % 60)
    return "{:02d}:{:02d}:{:02d},{:03d}".format(hours, minutes, seconds, milliseconds)


def text_to_srt(idx: int, msg: str, start_time: float, end_time: float) -> str:
    start_time = time_convert_seconds_to_hmsm(start_time)
    end_time = time_convert_seconds_to_hmsm(end_time)
    srt = """%d
%s --> %s
%s
        """ % (
        idx,
        start_time,
        end_time,
        msg,
    )
    return srt


def str_contains_punctuation(word):
    for p in const.PUNCTUATIONS:
        if p in word:
            return True
    return False


def split_string_by_punctuations(s):
    result = []
    txt = ""

    previous_char = ""
    next_char = ""
    for i in range(len(s)):
        char = s[i]
        if char == "\n":
            result.append(txt.strip())
            txt = ""
            continue

        if i > 0:
            previous_char = s[i - 1]
        if i < len(s) - 1:
            next_char = s[i + 1]

        if char == "." and previous_char.isdigit() and next_char.isdigit():
            # # In the case of "withdraw 10,000, charged at 2.5% fee", the dot in "2.5" should not be treated as a line break marker
            txt += char
            continue

        if char == "," and previous_char.isdigit() and next_char.isdigit():
            # 英文数字里的千分位逗号不是断句符，例如 "1,000 years"。
            # Edge TTS 的 word boundary 通常会把这种数字整体作为连续内容返回；
            # 如果这里拆成 "1" 和 "000 years"，后续字幕聚合会无法匹配脚本原文，
            # 进而错误回退到 Whisper。
            txt += char
            continue

        if char not in const.PUNCTUATIONS:
            txt += char
        else:
            result.append(txt.strip())
            txt = ""
    result.append(txt.strip())
    # filter empty string
    result = list(filter(None, result))
    return result


def normalize_script_for_subtitle_matching(video_script: str) -> str:
    """
    清理字幕匹配前的脚本文本。

    用户可能手动输入 Markdown 分隔符、标题强调或 `_` 这类格式符号。
    这些字符通常不会出现在 TTS/Whisper 的识别结果里；如果继续参与
    字幕逐行匹配，脚本行数量会大于真实字幕行数量，最终可能补出
    `00:00:00,000 --> 00:00:00,000`，导致剪辑软件无法导入 SRT。
    """
    video_script = video_script or ""
    underscore_count = video_script.count("_")
    video_script = video_script.replace("_", "")
    cleaned_lines = []
    removed_separator_lines = 0
    for line in video_script.splitlines():
        line = line.strip()
        # Markdown 分隔符或强调符号单独成行时不会被 TTS 朗读，必须从
        # 脚本行里移除，避免字幕聚合卡在这类“不可发声”的目标行上。
        if re.fullmatch(r"[-*_]{3,}", line):
            removed_separator_lines += 1
            continue
        cleaned_lines.append(line)

    normalized_script = "\n".join(cleaned_lines).strip()
    if underscore_count or removed_separator_lines:
        logger.debug(
            "normalized script for subtitle matching, "
            f"removed underscores: {underscore_count}, "
            f"removed markdown separator lines: {removed_separator_lines}"
        )
    return normalized_script


def md5(text):
    import hashlib

    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_system_locale():
    try:
        loc = locale.getdefaultlocale()
        # zh_CN, zh_TW return zh
        # en_US, en_GB return en
        language_code = loc[0].split("_")[0]
        return language_code
    except Exception:
        return "en"


@lru_cache(maxsize=None)
def load_locales(i18n_dir):
    # WebUI 每次交互都会触发 Streamlit 重新执行脚本，语言文件运行期不会变化，
    # 因此缓存解析结果，避免反复读取和解析所有 i18n JSON 文件。
    _locales = {}
    for root, dirs, files in os.walk(i18n_dir):
        for file in files:
            if file.endswith(".json"):
                lang = file.split(".")[0]
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    _locales[lang] = json.loads(f.read())
    return _locales


def parse_extension(filename):
    return Path(filename).suffix.lower().lstrip(".")


def run_subprocess(cmd, **kwargs):
    import subprocess

    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("errors", "replace")
    return subprocess.run(cmd, **kwargs)


def patch_windows_subprocess_encoding() -> None:
    """Avoid UnicodeDecodeError when decoding ffmpeg/moviepy output on GBK Windows."""
    if os.name != "nt":
        return
    if getattr(patch_windows_subprocess_encoding, "_patched", False):
        return

    import subprocess

    original_popen_init = subprocess.Popen.__init__

    def _popen_init(self, *args, **kwargs):
        if kwargs.get("text"):
            kwargs.setdefault("encoding", "utf-8")
            kwargs.setdefault("errors", "replace")
        return original_popen_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = _popen_init
    patch_windows_subprocess_encoding._patched = True


patch_windows_subprocess_encoding()
