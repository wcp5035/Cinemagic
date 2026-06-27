import os
import sys
import webbrowser
from uuid import UUID, uuid4

import requests
import streamlit as st
from loguru import logger

# Add the root directory of the project to the system path to allow importing modules from the project
from app.utils.paths import app_root, bundle_root

root_dir = app_root()
webui_dir = os.path.join(bundle_root(), "webui")
if root_dir not in sys.path:
    sys.path.append(root_dir)
if webui_dir not in sys.path:
    sys.path.insert(0, webui_dir)

from app.config import config
from app.models.schema import (
    MaterialInfo,
    VideoAspect,
    VideoConcatMode,
    VideoParams,
    VideoTransitionMode,
)
from app.services import llm, voice
from app.services import task as tm
from app.utils import utils
from theme import (
    get_theme_css,
    render_page_header,
    render_panel_header,
    render_sidebar_footer,
    render_sidebar_nav,
    render_status_card,
    render_tutorial_links,
    render_tutorial_steps,
)

st.set_page_config(
    page_title=config.project_name,
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Report a bug": "https://github.com/harry0703/MoneyPrinterTurbo/issues",
        "About": (
            f"# {config.project_name} v{config.project_version}\n"
            "Simply provide a topic or keyword for a video, and it will "
            "automatically generate the video copy, video materials, video subtitles, "
            "and video background music before synthesizing a high-definition short "
            f"video.\n\nAuthor X: {config.author_x_url}"
        ),
    },
)

st.markdown(get_theme_css(), unsafe_allow_html=True)

# 定义资源目录（只读资源在打包目录 _internal 内）
font_dir = utils.resource_dir("fonts")
song_dir = utils.resource_dir("songs")
i18n_dir = os.path.join(webui_dir, "i18n")
config_file = os.path.join(webui_dir, ".streamlit", "webui.toml")
system_locale = utils.get_system_locale()


if "video_subject" not in st.session_state:
    st.session_state["video_subject"] = ""
if "video_script" not in st.session_state:
    st.session_state["video_script"] = ""
if "video_terms" not in st.session_state:
    st.session_state["video_terms"] = ""
if "video_script_prompt" not in st.session_state:
    st.session_state["video_script_prompt"] = ""
if "custom_system_prompt" not in st.session_state:
    st.session_state["custom_system_prompt"] = llm.DEFAULT_SCRIPT_SYSTEM_PROMPT
if "use_custom_system_prompt" not in st.session_state:
    st.session_state["use_custom_system_prompt"] = False
if "match_materials_to_script" not in st.session_state:
    st.session_state["match_materials_to_script"] = bool(
        config.app.get("match_materials_to_script", False)
    )
if "ui_language" not in st.session_state:
    st.session_state["ui_language"] = config.ui.get("language", system_locale)
if "local_video_materials" not in st.session_state:
    # 记住用户最近一次已经落盘的本地素材，避免仅修改文案后二次生成时丢失素材列表。
    st.session_state["local_video_materials"] = []

# 加载语言文件
locales = utils.load_locales(i18n_dir)

support_locales = [
    "zh-CN",
    "zh-HK",
    "zh-TW",
    "de-DE",
    "en-US",
    "fr-FR",
    "ru-RU",
    "vi-VN",
    "th-TH",
    "tr-TR",
]


def get_all_fonts():
    fonts = []
    for root, dirs, files in os.walk(font_dir):
        for file in files:
            if file.endswith(".ttf") or file.endswith(".ttc"):
                fonts.append(file)
    fonts.sort()
    return fonts


def get_all_songs():
    songs = []
    for root, dirs, files in os.walk(song_dir):
        for file in files:
            if file.endswith(".mp3"):
                songs.append(file)
    return songs


def open_task_folder(task_id):
    try:
        # task_id 应始终是服务端生成的 UUID。这里先做格式校验，避免异常值
        # 通过路径拼接访问任务目录之外的位置，也避免后续打开目录时触发
        # 平台 shell 对特殊字符的解释。
        normalized_task_id = str(UUID(str(task_id)))
        tasks_root = os.path.abspath(os.path.join(root_dir, "storage", "tasks"))
        path = os.path.abspath(os.path.join(tasks_root, normalized_task_id))

        # 即使 UUID 校验通过，也再次确认最终路径仍在任务根目录内，避免
        # 未来调用方调整 task_id 来源时引入路径穿越风险。
        if not path.startswith(tasks_root + os.sep):
            logger.warning(f"invalid task folder path: {path}")
            return

        if os.path.isdir(path):
            utils.open_folder(path)
    except Exception as e:
        logger.error(e)


def scroll_to_bottom():
    js = """
    <script>
        console.log("scroll_to_bottom");
        function scroll(dummy_var_to_force_repeat_execution){
            var sections = parent.document.querySelectorAll('section.main');
            console.log(sections);
            for(let index = 0; index<sections.length; index++) {
                sections[index].scrollTop = sections[index].scrollHeight;
            }
        }
        scroll(1);
    </script>
    """
    st.components.v1.html(js, height=0, width=0)


def init_log():
    logger.remove()
    _lvl = "DEBUG"

    def format_record(record):
        # 获取日志记录中的文件全路径
        file_path = record["file"].path
        # 将绝对路径转换为相对于项目根目录的路径
        relative_path = os.path.relpath(file_path, root_dir)
        # 更新记录中的文件路径
        record["file"].path = f"./{relative_path}"
        # 返回修改后的格式字符串
        # 您可以根据需要调整这里的格式
        record["message"] = record["message"].replace(root_dir, ".")

        _format = (
            "<green>{time:%Y-%m-%d %H:%M:%S}</> | "
            + "<level>{level}</> | "
            + '"{file.path}:{line}":<blue> {function}</> '
            + "- <level>{message}</>"
            + "\n"
        )
        return _format

    logger.add(
        sys.stdout,
        level=_lvl,
        format=format_record,
        colorize=True,
    )


init_log()

locales = utils.load_locales(i18n_dir)


def tr(key):
    ui_language = st.session_state.get("ui_language", "zh")
    loc = locales.get(ui_language)
    if loc is None and "-" in ui_language:
        loc = locales.get(ui_language.split("-", 1)[0])
    if loc is None:
        loc = locales.get("zh") or locales.get("en") or {}
    return loc.get("Translation", {}).get(key, key)


def tr_nav(key):
    """导航区域固定使用中文文案。"""
    _nav_zh = {
        "Tab Audio": "音频",
        "Tab Subtitle": "字幕",
        "Nav Home": "🏠 视频生成",
        "Nav Settings": "⚙️ 基础设置",
        "Nav Tutorial": "📖 使用教程",
        "Language": "语言",
        "Tutorial Author X": "作者 X",
        "Home Subtitle": "一键生成 · 短视频创作",
        "Settings Subtitle": "LLM 配置 · 素材密钥 · 运行选项",
        "Tutorial Subtitle": "快速上手 · 安装配置与生成流程",
    }
    zh = locales.get("zh", {}).get("Translation", {})
    return zh.get(key) or _nav_zh.get(key) or tr(key)


def tr_plain(key):
    return tr(key).replace("**", "")


def render_material_api_key_management() -> None:
    if "coverr_api_keys" not in config.app or config.app["coverr_api_keys"] is None:
        config.app["coverr_api_keys"] = []
    if "pexels_api_keys" not in config.app or config.app["pexels_api_keys"] is None:
        config.app["pexels_api_keys"] = []
    if "pixabay_api_keys" not in config.app or config.app["pixabay_api_keys"] is None:
        config.app["pixabay_api_keys"] = []

    st.caption(tr("Manage Pexels, Pixabay and Coverr API Keys"))

    col1, col2, col3 = st.tabs([
        tr("Pexels API Keys"),
        tr("Pixabay API Keys"),
        tr("Coverr API Keys"),
    ])

    with col1:
        st.subheader(tr("Pexels API Keys"))
        if config.app["pexels_api_keys"]:
            st.write(tr("Current Keys:"))
            for key in config.app["pexels_api_keys"]:
                st.code(key)
        else:
            st.info(tr("No Pexels API Keys currently"))

        new_key = st.text_input(tr("Add Pexels API Key"), key="pexels_new_key")
        if st.button(tr("Add Pexels API Key")):
            if new_key and new_key not in config.app["pexels_api_keys"]:
                config.app["pexels_api_keys"].append(new_key)
                config.save_config()
                st.success(tr("Pexels API Key added successfully"))
            elif new_key in config.app["pexels_api_keys"]:
                st.warning(tr("This API Key already exists"))
            else:
                st.error(tr("Please enter a valid API Key"))

        if config.app["pexels_api_keys"]:
            delete_key = st.selectbox(
                tr("Select Pexels API Key to delete"),
                config.app["pexels_api_keys"],
                key="pexels_delete_key",
            )
            if st.button(tr("Delete Selected Pexels API Key")):
                config.app["pexels_api_keys"].remove(delete_key)
                config.save_config()
                st.success(tr("Pexels API Key deleted successfully"))

    with col2:
        st.subheader(tr("Pixabay API Keys"))

        if config.app["pixabay_api_keys"]:
            st.write(tr("Current Keys:"))
            for key in config.app["pixabay_api_keys"]:
                st.code(key)
        else:
            st.info(tr("No Pixabay API Keys currently"))

        new_key = st.text_input(tr("Add Pixabay API Key"), key="pixabay_new_key")
        if st.button(tr("Add Pixabay API Key")):
            if new_key and new_key not in config.app["pixabay_api_keys"]:
                config.app["pixabay_api_keys"].append(new_key)
                config.save_config()
                st.success(tr("Pixabay API Key added successfully"))
            elif new_key in config.app["pixabay_api_keys"]:
                st.warning(tr("This API Key already exists"))
            else:
                st.error(tr("Please enter a valid API Key"))

        if config.app["pixabay_api_keys"]:
            delete_key = st.selectbox(
                tr("Select Pixabay API Key to delete"),
                config.app["pixabay_api_keys"],
                key="pixabay_delete_key",
            )
            if st.button(tr("Delete Selected Pixabay API Key")):
                config.app["pixabay_api_keys"].remove(delete_key)
                config.save_config()
                st.success(tr("Pixabay API Key deleted successfully"))

    with col3:
        st.subheader(tr("Coverr API Keys"))

        if config.app["coverr_api_keys"]:
            st.write(tr("Current Keys:"))
            for key in config.app["coverr_api_keys"]:
                st.code(key)
        else:
            st.info(tr("No Coverr API Keys currently"))

        new_key = st.text_input(tr("Add Coverr API Key"), key="coverr_new_key")
        if st.button(tr("Add Coverr API Key")):
            if new_key and new_key not in config.app["coverr_api_keys"]:
                config.app["coverr_api_keys"].append(new_key)
                config.save_config()
                st.success(tr("Coverr API Key added successfully"))
            elif new_key in config.app["coverr_api_keys"]:
                st.warning(tr("This API Key already exists"))
            else:
                st.error(tr("Please enter a valid API Key"))

        if config.app["coverr_api_keys"]:
            delete_key = st.selectbox(
                tr("Select Coverr API Key to delete"),
                config.app["coverr_api_keys"],
                key="coverr_delete_key",
            )
            if st.button(tr("Delete Selected Coverr API Key")):
                config.app["coverr_api_keys"].remove(delete_key)
                config.save_config()
                st.success(tr("Coverr API Key deleted successfully"))


def render_advanced_video_settings() -> None:
    st.checkbox(
        tr("Match Materials to Script Order"),
        help=tr("Match Materials to Script Order Help"),
        key="match_materials_to_script",
    )
    config.app["match_materials_to_script"] = bool(
        st.session_state.get("match_materials_to_script", False)
    )

    video_codec_options = [
        ("libx264 (CPU)", "libx264"),
        ("NVIDIA NVENC (h264_nvenc)", "h264_nvenc"),
        ("AMD AMF (h264_amf)", "h264_amf"),
        ("Intel QSV (h264_qsv)", "h264_qsv"),
        ("Windows MediaFoundation (h264_mf)", "h264_mf"),
        ("macOS VideoToolbox (h264_videotoolbox)", "h264_videotoolbox"),
    ]
    saved_video_codec = config.app.get("video_codec", "libx264")
    saved_video_codec_values = [item[1] for item in video_codec_options]
    if saved_video_codec not in saved_video_codec_values:
        saved_video_codec = "libx264"
    selected_codec_index = saved_video_codec_values.index(saved_video_codec)
    selected_codec_index = st.selectbox(
        tr("Video Encoder"),
        options=range(len(video_codec_options)),
        index=selected_codec_index,
        format_func=lambda x: video_codec_options[x][0],
        help=tr("Video Encoder Help"),
        key="settings_video_codec",
    )
    config.app["video_codec"] = video_codec_options[selected_codec_index][1]


NAV_HOME = "nav_home"
NAV_SETTINGS = "nav_settings"
NAV_TUTORIAL = "nav_tutorial"

with st.sidebar:
    st.markdown(
        f"""
        <div class="mpt-sidebar-brand">
            <div class="mpt-sidebar-brand-icon">🎬</div>
            <div>
                <div class="mpt-sidebar-brand-title">{config.project_name}</div>
                <div class="mpt-sidebar-brand-sub">AI 短视频创作平台</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="mpt-sidebar-nav-label">导航菜单</div>',
        unsafe_allow_html=True,
    )
    nav_options = {
        NAV_SETTINGS: tr_nav("Nav Settings"),
        NAV_HOME: tr_nav("Nav Home"),
        NAV_TUTORIAL: tr_nav("Nav Tutorial"),
    }
    default_page = st.session_state.get("current_page", NAV_HOME)
    if default_page not in nav_options:
        default_page = NAV_HOME
    current_page = render_sidebar_nav(
        nav_options,
        session_key="current_page",
        default=default_page,
    )
    st.session_state["current_page"] = current_page

    st.markdown("---")
    display_languages = []
    selected_index = 0
    for i, code in enumerate(locales.keys()):
        display_languages.append(f"{code} - {locales[code].get('Language')}")
        if code == st.session_state.get("ui_language", ""):
            selected_index = i

    selected_language = st.selectbox(
        tr_nav("Language"),
        options=display_languages,
        index=selected_index,
        key="sidebar_language_selector",
    )
    if selected_language:
        code = selected_language.split(" - ")[0].strip()
        st.session_state["ui_language"] = code
        config.ui["language"] = code

    render_sidebar_footer(
        config.project_version,
        config.author_x_url,
        x_title=tr_nav("Tutorial Author X"),
    )

@st.cache_data(ttl=300, show_spinner=False)
def get_groq_model_ids(api_key: str, base_url: str) -> list[str]:
    if not api_key:
        return []

    normalized_base_url = (base_url or "https://api.groq.com/openai/v1").strip().rstrip("/")
    models_url = f"{normalized_base_url}/models"

    try:
        response = requests.get(
            models_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", [])

        model_ids = []
        for item in data:
            if isinstance(item, dict):
                model_id = item.get("id")
                if isinstance(model_id, str) and model_id.strip():
                    model_ids.append(model_id.strip())

        return sorted(set(model_ids))
    except Exception as e:
        logger.warning(f"failed to fetch groq models: {e}")
        return []

# 系统设置页（独立页面始终显示完整配置，不受 hide_config 影响）
if current_page == NAV_SETTINGS:
    render_page_header(tr_nav("Nav Settings"), tr_nav("Settings Subtitle"))
    config_panels = st.columns(2)
    middle_config_panel = config_panels[0]
    right_config_panel = config_panels[1]

    with middle_config_panel:
        render_panel_header(tr_plain("LLM Settings"))
        # 下拉框需要展示“AIHubMix（推荐）”这类面向用户的文案，
        # 但配置文件和后端逻辑必须继续使用稳定的小写 provider id。
        # 因此这里显式维护 display label 和 provider id 的映射，避免
        # UI 文案变化污染 `config.app["llm_provider"]`。
        aihubmix_label = f"AIHubMix ({tr('Recommended')})"
        if config.ui.get("language") == "zh":
            aihubmix_label = "AIHubMix（推荐）"
        llm_provider_options = [
            ("OpenAI", "openai"),
            (aihubmix_label, "aihubmix"),
            ("AIML API", "aimlapi"),
            ("EvoLink", "evolink"),
            ("Moonshot", "moonshot"),
            ("Azure", "azure"),
            ("Qwen", "qwen"),
            ("DeepSeek", "deepseek"),
            ("ModelScope", "modelscope"),
            ("Gemini", "gemini"),
            ("Grok", "grok"),
            ("Groq", "groq"),
            ("Ollama", "ollama"),
            ("G4f", "g4f"),
            ("OneAPI", "oneapi"),
            ("Cloudflare", "cloudflare"),
            ("ERNIE", "ernie"),
            ("MiniMax", "minimax"),
            ("MiMo", "mimo"),
            ("Pollinations", "pollinations"),
            ("LiteLLM", "litellm"),
        ]
        llm_provider_ids = [provider_id for _, provider_id in llm_provider_options]
        llm_provider_labels = {
            provider_id: label for label, provider_id in llm_provider_options
        }
        saved_llm_provider = config.app.get("llm_provider", "openai").lower()
        if saved_llm_provider not in llm_provider_ids:
            saved_llm_provider = "openai"

        # Streamlit 会把没有 key 的 selectbox 视为一个由 label/options/index
        # 共同决定的临时控件。如果每次选择后都根据 config.app 重新计算 index，
        # 用户第一次切换 provider 后控件可能被重建，表现为“必须选择两次才生效”。
        # 这里用稳定的 provider id 作为真实选项，并给控件固定 key；展示文案只
        # 通过 format_func 转换，避免 UI 文案变化影响状态。
        if st.session_state.get("llm_provider_select") not in (
            None,
            *llm_provider_ids,
        ):
            del st.session_state["llm_provider_select"]

        llm_provider = st.selectbox(
            tr("LLM Provider"),
            options=llm_provider_ids,
            index=llm_provider_ids.index(saved_llm_provider),
            format_func=lambda provider_id: llm_provider_labels[provider_id],
            key="llm_provider_select",
        )
        llm_helper = st.container()
        config.app["llm_provider"] = llm_provider

        llm_api_key = config.app.get(f"{llm_provider}_api_key", "")
        llm_secret_key = config.app.get(
            f"{llm_provider}_secret_key", ""
        )  # only for baidu ernie
        llm_base_url = config.app.get(f"{llm_provider}_base_url", "")
        llm_model_name = config.app.get(f"{llm_provider}_model_name", "")
        llm_account_id = config.app.get(f"{llm_provider}_account_id", "")

        tips = ""
        if llm_provider == "ollama":
            if not llm_model_name:
                llm_model_name = "qwen:7b"
            if not llm_base_url:
                llm_base_url = config.get_default_ollama_base_url()

            with llm_helper:
                docker_hint = ""
                if config.is_running_in_container():
                    docker_hint = "\n                            > 检测到容器环境，未配置 Base Url 时会默认使用 `http://host.docker.internal:11434/v1`\n"
                tips = f"""
                        ##### Ollama配置说明
                        - **API Key**: 随便填写，比如 123
                        - **Base Url**: 一般为 http://localhost:11434/v1
                            - 如果 `{config.project_name}` 和 `Ollama` **不在同一台机器上**，需要填写 `Ollama` 机器的IP地址
                            - 如果 `{config.project_name}` 是 `Docker` 部署，建议填写 `http://host.docker.internal:11434/v1`{docker_hint}
                        - **Model Name**: 使用 `ollama list` 查看，比如 `qwen:7b`
                        """

        if llm_provider == "openai":
            if not llm_model_name:
                llm_model_name = "gpt-3.5-turbo"
            with llm_helper:
                tips = """
                        ##### OpenAI 配置说明
                        > 需要VPN开启全局流量模式
                        - **API Key**: [点击到官网申请](https://platform.openai.com/api-keys)
                        - **Base Url**: 官方 OpenAI 可留空；如果使用 OpenAI 兼容供应商（例如 OpenRouter），请填写对应的兼容接口地址
                        - **Model Name**: 填写**有权限**的模型；如果使用兼容供应商，请填写该平台支持的模型 ID
                        """

        if llm_provider == "aihubmix":
            if not llm_model_name:
                llm_model_name = "gpt-5.4-mini"
            if not llm_base_url:
                llm_base_url = "https://aihubmix.com/v1"
            with llm_helper:
                tips = """
                        ##### AIHubMix 配置说明
                        - **注册链接**: [点击注册 AIHubMix](https://aihubmix.com/?aff=CEve)
                        - **Base Url**: 预填 https://aihubmix.com/v1
                        - **推荐模型**: 默认 gpt-5.4-mini，也可以填写 AIHubMix 支持的免费模型或其它模型 ID

                        推荐理由：
                        - **模型全**: Claude、GPT、Gemini、Grok、DeepSeek、通义等 700+ 模型一站覆盖
                        - **稳定**: 无限并发，永远在线，集群部署于谷歌云，长期为众多知名应用提供高并发服务
                        - **能力完整**: 文本、图片生成、视频生成、TTS、STT、向量嵌入、Rerank，多模态场景全搞定
                        - **计费透明**: 按量付费，无会员无包月，免费模型可使用
                        """

        if llm_provider == "aimlapi":
            if not llm_model_name:
                llm_model_name = "openai/gpt-4o-mini"
            if not llm_base_url:
                llm_base_url = "https://api.aimlapi.com/v1"
            with llm_helper:
                tips = """
                        ##### AIML API Configuration
                        - **API Key**: create one at https://aimlapi.com/app/keys
                        - **Base Url**: https://api.aimlapi.com/v1
                        - **Model Name**: for example `openai/gpt-4o-mini`, `openai/gpt-4o`, `anthropic/claude-sonnet-4.5`, or `google/gemini-3-flash-preview`
                        """

        if llm_provider == "evolink":
            if not llm_model_name:
                llm_model_name = "gpt-5.5"
            if not llm_base_url:
                llm_base_url = "https://direct.evolink.ai/v1"
            with llm_helper:
                tips = """
                        ##### EvoLink 配置说明
                        - **API Key**: [点击到官网申请](https://evolink.ai/dashboard/keys)
                        - **Base Url**: 默认 https://direct.evolink.ai/v1
                        - **Model Name**: 默认 gpt-5.5，也可以填写 EvoLink 支持的其它模型 ID
                        """

        if llm_provider == "moonshot":
            if not llm_model_name:
                llm_model_name = "moonshot-v1-8k"
            with llm_helper:
                tips = """
                        ##### Moonshot 配置说明
                        - **API Key**: [点击到官网申请](https://platform.moonshot.cn/console/api-keys)
                        - **Base Url**: 固定为 https://api.moonshot.cn/v1
                        - **Model Name**: 比如 moonshot-v1-8k，[点击查看模型列表](https://platform.moonshot.cn/docs/intro#%E6%A8%A1%E5%9E%8B%E5%88%97%E8%A1%A8)
                        """
        if llm_provider == "oneapi":
            if not llm_model_name:
                llm_model_name = (
                    "claude-3-5-sonnet-20240620"  # 默认模型，可以根据需要调整
                )
            with llm_helper:
                tips = """
                    ##### OneAPI 配置说明
                    - **API Key**: 填写您的 OneAPI 密钥
                    - **Base Url**: 填写 OneAPI 的基础 URL
                    - **Model Name**: 填写您要使用的模型名称，例如 claude-3-5-sonnet-20240620
                    """

        if llm_provider == "qwen":
            if not llm_model_name:
                llm_model_name = "qwen-max"
            with llm_helper:
                tips = """
                        ##### 通义千问Qwen 配置说明
                        - **API Key**: [点击到官网申请](https://dashscope.console.aliyun.com/apiKey)
                        - **Base Url**: 留空
                        - **Model Name**: 比如 qwen-max，[点击查看模型列表](https://help.aliyun.com/zh/dashscope/developer-reference/model-introduction#3ef6d0bcf91wy)
                        """

        if llm_provider == "g4f":
            if not llm_model_name:
                llm_model_name = "gpt-3.5-turbo"
            with llm_helper:
                tips = """
                        ##### gpt4free 配置说明
                        > [GitHub开源项目](https://github.com/xtekky/gpt4free)，可以免费使用GPT模型，但是**稳定性较差**
                        - **API Key**: 随便填写，比如 123
                        - **Base Url**: 留空
                        - **Model Name**: 比如 gpt-3.5-turbo，[点击查看模型列表](https://github.com/xtekky/gpt4free/blob/main/g4f/models.py#L308)
                        """
        if llm_provider == "azure":
            with llm_helper:
                tips = """
                        ##### Azure 配置说明
                        > [点击查看如何部署模型](https://learn.microsoft.com/zh-cn/azure/ai-services/openai/how-to/create-resource)
                        - **API Key**: [点击到Azure后台创建](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/OpenAI)
                        - **Base Url**: 留空
                        - **Model Name**: 填写你实际的部署名
                        """

        if llm_provider == "gemini":
            if not llm_model_name:
                llm_model_name = "gemini-1.0-pro"

            with llm_helper:
                tips = """
                        ##### Gemini 配置说明
                        > 需要VPN开启全局流量模式
                        - **API Key**: [点击到官网申请](https://ai.google.dev/)
                        - **Base Url**: 留空
                        - **Model Name**: 比如 gemini-1.0-pro
                        """

        if llm_provider == "grok":
            if not llm_model_name:
                llm_model_name = "grok-4.3"
            if not llm_base_url:
                llm_base_url = "https://api.x.ai/v1"

            with llm_helper:
                tips = """
                        ##### Grok 配置说明
                        - **API Key**: 填写您的 GrokAPI 密钥
                        - **Base Url**: 填写 GrokAPI 的基础 URL
                        - **Model Name**: 比如 grok-4.3
                        """

        if llm_provider == "groq":
            if not llm_model_name:
                llm_model_name = "llama-3.3-70b-versatile"
            if not llm_base_url:
                llm_base_url = "https://api.groq.com/openai/v1"

            with llm_helper:
                tips = """
                        ##### Groq 配置说明
                        - **API Key**: [点击到官网申请](https://console.groq.com/keys)
                        - **Base Url**: 固定为 https://api.groq.com/openai/v1
                        - **Model Name**: 比如 llama-3.3-70b-versatile
                        """

        if llm_provider == "deepseek":
            if not llm_model_name:
                llm_model_name = "deepseek-chat"
            if not llm_base_url:
                llm_base_url = "https://api.deepseek.com"
            with llm_helper:
                tips = """
                        ##### DeepSeek 配置说明
                        - **API Key**: [点击到官网申请](https://platform.deepseek.com/api_keys)
                        - **Base Url**: 固定为 https://api.deepseek.com
                        - **Model Name**: 固定为 deepseek-chat
                        """

        if llm_provider == "mimo":
            if not llm_model_name:
                llm_model_name = "mimo-v2.5-pro"
            if not llm_base_url:
                llm_base_url = "https://api.xiaomimimo.com/v1"
            with llm_helper:
                tips = """
                        ##### Xiaomi MiMo 配置说明
                        - **API Key**: [点击到官网申请](https://platform.xiaomimimo.com/docs/zh-CN/quick-start/first-api-call)
                        - **Base Url**: 固定为 https://api.xiaomimimo.com/v1
                        - **Model Name**: 默认 mimo-v2.5-pro，也可以按官方文档填写其它可用模型
                        """

        if llm_provider == "modelscope":
            if not llm_model_name:
                llm_model_name = "Qwen/Qwen3-32B"
            if not llm_base_url:
                llm_base_url = "https://api-inference.modelscope.cn/v1/"
            with llm_helper:
                tips = """
                        ##### ModelScope 配置说明
                        - **API Key**: [点击到官网申请](https://modelscope.cn/docs/model-service/API-Inference/intro)
                        - **Base Url**: 固定为 https://api-inference.modelscope.cn/v1/
                        - **Model Name**: 比如 Qwen/Qwen3-32B，[点击查看模型列表](https://modelscope.cn/models?filter=inference_type&page=1)
                        """

        if llm_provider == "ernie":
            with llm_helper:
                tips = """
                        ##### 百度文心一言 配置说明
                        - **API Key**: [点击到官网申请](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
                        - **Secret Key**: [点击到官网申请](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
                        - **Base Url**: 填写 **请求地址** [点击查看文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/jlil56u11#%E8%AF%B7%E6%B1%82%E8%AF%B4%E6%98%8E)
                        """

        if llm_provider == "pollinations":
            if not llm_model_name:
                llm_model_name = "default"
            with llm_helper:
                tips = """
                        ##### Pollinations AI Configuration
                        - **API Key**: Optional - Leave empty for public access
                        - **Base Url**: Default is https://text.pollinations.ai/openai
                        - **Model Name**: Use 'openai-fast' or specify a model name
                        """

        if llm_provider == "litellm":
            if not llm_model_name:
                llm_model_name = "openai/gpt-4o-mini"
            with llm_helper:
                tips = """
                        ##### LiteLLM Configuration
                        > [LiteLLM](https://github.com/BerriAI/litellm) routes to 100+ LLM providers via a unified interface.
                        > Set your provider's API key as an env var: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `AWS_ACCESS_KEY_ID`, etc.
                        - **Model Name**: LiteLLM format — `openai/gpt-4o`, `anthropic/claude-sonnet-4-20250514`, `bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0`, `gemini/gemini-2.5-flash`. See [full provider list](https://docs.litellm.ai/docs/providers)
                        """

        if tips and config.ui["language"] == "zh":
            st.info(tips)

        st_llm_api_key = st.text_input(
            tr("API Key"), value=llm_api_key, type="password"
        )
        st_llm_base_url = st.text_input(tr("Base Url"), value=llm_base_url)
        st_llm_model_name = ""
        if llm_provider != "ernie":
            if llm_provider == "groq":
                effective_api_key = st_llm_api_key or llm_api_key
                effective_base_url = st_llm_base_url or llm_base_url
                groq_models = get_groq_model_ids(
                    api_key=effective_api_key,
                    base_url=effective_base_url,
                )

                if groq_models:
                    selected_index = 0
                    if llm_model_name in groq_models:
                        selected_index = groq_models.index(llm_model_name)

                    st_llm_model_name = st.selectbox(
                        tr("Model Name"),
                        options=groq_models,
                        index=selected_index,
                        key="groq_model_name_select",
                    )
                else:
                    st_llm_model_name = st.text_input(
                        tr("Model Name"),
                        value=llm_model_name,
                        key="groq_model_name_input",
                    )
                    if effective_api_key:
                        st.caption(
                            "Unable to load Groq model list right now. You can still enter a model name manually — note it won't be validated until generation."
                        )
                    else:
                        st.caption(
                            "Add a Groq API key to load available models automatically."
                        )
            else:
                st_llm_model_name = st.text_input(
                    tr("Model Name"),
                    value=llm_model_name,
                    key=f"{llm_provider}_model_name_input",
                )
            if st_llm_model_name:
                config.app[f"{llm_provider}_model_name"] = st_llm_model_name
        else:
            st_llm_model_name = None

        if st_llm_api_key:
            config.app[f"{llm_provider}_api_key"] = st_llm_api_key
        if st_llm_base_url:
            config.app[f"{llm_provider}_base_url"] = st_llm_base_url
        if st_llm_model_name:
            config.app[f"{llm_provider}_model_name"] = st_llm_model_name
        if llm_provider == "ernie":
            st_llm_secret_key = st.text_input(
                tr("Secret Key"), value=llm_secret_key, type="password"
            )
            config.app[f"{llm_provider}_secret_key"] = st_llm_secret_key

        if llm_provider == "cloudflare":
            st_llm_account_id = st.text_input(
                tr("Account ID"), value=llm_account_id
            )
            if st_llm_account_id:
                config.app[f"{llm_provider}_account_id"] = st_llm_account_id

    with right_config_panel:
        with st.container(border=True):
            render_panel_header(tr_plain("Video Source Settings"))
            render_material_api_key_management()

        with st.container(border=True):
            render_panel_header(tr_plain("Video Output Directory"))
            st.caption(tr("Video Output Directory Help"))

            saved_output_directory = config.app.get("video_output_directory", "")
            resolved_output_directory = utils.get_video_output_directory()
            if resolved_output_directory:
                st.text_input(
                    tr("Current Output Folder"),
                    value=resolved_output_directory,
                    disabled=True,
                    label_visibility="visible",
                )
            else:
                st.info(tr("Output Folder Not Set"))

            select_col, open_col, clear_col = st.columns([2, 1, 1])
            with select_col:
                if st.button(
                    tr("Select Output Folder"),
                    use_container_width=True,
                    key="select_video_output_folder",
                ):
                    picked_dir = utils.pick_directory(
                        initial_dir=resolved_output_directory or root_dir,
                        title=tr("Select Output Folder"),
                    )
                    if picked_dir:
                        config.app["video_output_directory"] = picked_dir
                        config.save_config()
                        st.toast(tr("Output Folder Selected"))
                        st.rerun()
            with open_col:
                if st.button(
                    tr("Open Output Folder"),
                    use_container_width=True,
                    key="open_video_output_folder",
                ):
                    output_dir = utils.get_video_output_directory(create=True)
                    if output_dir and utils.open_folder(output_dir):
                        st.toast(tr("Opening Output Folder"))
                    elif not saved_output_directory.strip():
                        st.warning(tr("Please Set Video Output Directory First"))
                    else:
                        st.warning(tr("Output Folder Does Not Exist"))
            with clear_col:
                if st.button(
                    tr("Clear Output Folder"),
                    use_container_width=True,
                    key="clear_video_output_folder",
                    disabled=not saved_output_directory.strip(),
                ):
                    config.app["video_output_directory"] = ""
                    config.save_config()
                    st.toast(tr("Output Folder Cleared"))
                    st.rerun()

        with st.container(border=True):
            render_panel_header(tr_plain("Advanced Video Settings"))
            render_advanced_video_settings()

elif current_page == NAV_TUTORIAL:
    render_page_header(tr_nav("Nav Tutorial"), tr_nav("Tutorial Subtitle"))
    st.caption(tr_nav("Tutorial Intro"))
    st.markdown(
        f'<div class="mpt-section-title">{tr_nav("Tutorial Steps Title")}</div>',
        unsafe_allow_html=True,
    )
    webui_port = os.environ.get("MPT_WEBUI_PORT", "8501")
    tutorial_format = {"webui_port": webui_port, "api_port": config.listen_port}
    render_tutorial_steps(
        [
            (tr_nav("Tutorial Step 1 Title"), tr_nav("Tutorial Step 1 Body")),
            (
                tr_nav("Tutorial Step 2 Title"),
                tr_nav("Tutorial Step 2 Body").format(**tutorial_format),
            ),
            (tr_nav("Tutorial Step 3 Title"), tr_nav("Tutorial Step 3 Body")),
            (tr_nav("Tutorial Step 4 Title"), tr_nav("Tutorial Step 4 Body")),
            (tr_nav("Tutorial Step 5 Title"), tr_nav("Tutorial Step 5 Body")),
        ]
    )
    st.markdown(
        f'<div class="mpt-section-title">{tr_nav("Tutorial Quick Links")}</div>',
        unsafe_allow_html=True,
    )
    api_docs_url = f"http://127.0.0.1:{config.listen_port}/docs"
    render_tutorial_links(
        [
            (
                tr_nav("Tutorial Author X"),
                tr_nav("Tutorial Author X Desc"),
                config.author_x_url,
            ),
            (
                tr_nav("Tutorial API Docs"),
                tr_nav("Tutorial API Desc"),
                api_docs_url,
            ),
        ]
    )

elif current_page == NAV_HOME:
    llm_provider = config.app.get("llm_provider", "").lower()
    llm_api_key = config.app.get(f"{llm_provider}_api_key", "")
    material_configured = bool(
        config.app.get("pexels_api_keys")
        or config.app.get("pixabay_api_keys")
        or config.app.get("coverr_api_keys")
    )
    render_page_header(tr_nav("Nav Home"), tr_nav("Home Subtitle"))
    render_status_card(
        version=config.project_version,
        llm_provider=llm_provider or "openai",
        llm_configured=bool(str(llm_api_key).strip()),
        ready_label=tr_nav("Status Ready"),
        not_ready_label=tr_nav("Status Not Ready"),
        version_label=tr_nav("Version Label"),
        llm_label=tr_nav("Current LLM"),
        material_keys_configured=material_configured,
        material_label=tr_nav("Material API"),
        material_ready_label=tr_nav("Status Ready"),
        material_not_ready_label=tr_nav("Status Not Ready"),
    )
    if not bool(str(llm_api_key).strip()):
        st.info(tr_nav("LLM Not Configured Hint"))
    st.markdown(
        f"""
        <div class="mpt-cta-card">
            <div class="mpt-section-title">{tr_nav("Generate Video")}</div>
            <div class="mpt-cta-hint">{tr_nav("Generate Video Hint")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    start_button = st.button(
        tr("Generate Video"), use_container_width=True, type="primary"
    )
    tab_script, tab_video, tab_audio, tab_subtitle = st.tabs(
        [
            tr_nav("Tab Script"),
            tr_nav("Tab Video"),
            "音频",
            "字幕",
        ]
    )
    params = VideoParams(video_subject="")
    params.match_materials_to_script = bool(
        st.session_state.get("match_materials_to_script", False)
    )
    uploaded_files = []
    uploaded_audio_file = None
    
    with tab_script:
        with st.container(border=True):
            render_panel_header(tr_plain("Video Script Settings"))
            params.video_subject = st.text_input(
                tr("Video Subject"),
                key="video_subject",
            ).strip()
    
            video_languages = [
                (tr("Auto Detect"), ""),
            ]
            for code in support_locales:
                video_languages.append((code, code))
    
            selected_index = st.selectbox(
                tr("Script Language"),
                index=0,
                options=range(
                    len(video_languages)
                ),  # Use the index as the internal option value
                format_func=lambda x: video_languages[x][
                    0
                ],  # The label is displayed to the user
            )
            params.video_language = video_languages[selected_index][1]
    
            with st.expander(tr("Advanced Script Settings"), expanded=False):
                params.paragraph_number = st.slider(
                    tr("Script Paragraph Number"),
                    min_value=llm.MIN_SCRIPT_PARAGRAPH_NUMBER,
                    max_value=llm.MAX_SCRIPT_PARAGRAPH_NUMBER,
                    value=st.session_state.get("paragraph_number_input", 1),
                    key="paragraph_number_input",
                )
                params.video_script_prompt = st.text_area(
                    tr("Custom Script Requirements"),
                    height=100,
                    max_chars=llm.MAX_SCRIPT_PROMPT_LENGTH,
                    placeholder=tr("Custom Script Requirements Placeholder"),
                    key="video_script_prompt",
                ).strip()
    
                use_custom_system_prompt = st.checkbox(
                    tr("Use Custom System Prompt"),
                    help=tr("Use Custom System Prompt Help"),
                    key="use_custom_system_prompt",
                )
    
                if use_custom_system_prompt:
                    custom_system_prompt = st.text_area(
                        tr("Custom System Prompt"),
                        height=240,
                        max_chars=llm.MAX_SCRIPT_SYSTEM_PROMPT_LENGTH,
                        key="custom_system_prompt",
                    ).strip()
                    params.custom_system_prompt = custom_system_prompt
                else:
                    params.custom_system_prompt = ""
    
            if st.button(
                tr("Generate Video Script and Keywords"), key="auto_generate_script"
            ):
                with st.spinner(tr("Generating Video Script and Keywords")):
                    script = llm.generate_script(
                        video_subject=params.video_subject,
                        language=params.video_language,
                        paragraph_number=params.paragraph_number,
                        video_script_prompt=params.video_script_prompt,
                        custom_system_prompt=params.custom_system_prompt,
                    )
                    terms = llm.generate_terms(
                        params.video_subject,
                        script,
                        amount=8 if params.match_materials_to_script else 5,
                        match_script_order=params.match_materials_to_script,
                    )
                    if "Error: " in script:
                        st.error(tr(script))
                    elif "Error: " in terms:
                        st.error(tr(terms))
                    else:
                        st.session_state["video_script"] = script
                        st.session_state["video_terms"] = ", ".join(terms)
            params.video_script = st.text_area(
                tr("Video Script"), value=st.session_state["video_script"], height=280
            )
            if st.button(tr("Generate Video Keywords"), key="auto_generate_terms"):
                if not params.video_script:
                    st.error(tr("Please Enter the Video Subject"))
                    st.stop()
    
                with st.spinner(tr("Generating Video Keywords")):
                    terms = llm.generate_terms(
                        params.video_subject,
                        params.video_script,
                        amount=8 if params.match_materials_to_script else 5,
                        match_script_order=params.match_materials_to_script,
                    )
                    if "Error: " in terms:
                        st.error(tr(terms))
                    else:
                        st.session_state["video_terms"] = ", ".join(terms)
    
            params.video_terms = st.text_area(
                tr("Video Keywords"), value=st.session_state["video_terms"]
            )
    
    with tab_video:
        with st.container(border=True):
            render_panel_header(tr_plain("Video Settings"))
            video_concat_modes = [
                (tr("Sequential"), "sequential"),
                (tr("Random"), "random"),
            ]
            video_sources = [
                (tr("Pexels"), "pexels"),
                (tr("Pixabay"), "pixabay"),
                (tr("Coverr"), "coverr"),
                (tr("Local file"), "local"),
                (tr("TikTok"), "douyin"),
                (tr("Bilibili"), "bilibili"),
                (tr("Xiaohongshu"), "xiaohongshu"),
            ]
    
            saved_video_source_name = config.app.get("video_source", "pexels")
            saved_video_source_index = [v[1] for v in video_sources].index(
                saved_video_source_name
            )
    
            selected_index = st.selectbox(
                tr("Video Source"),
                options=range(len(video_sources)),
                format_func=lambda x: video_sources[x][0],
                index=saved_video_source_index,
            )
            params.video_source = video_sources[selected_index][1]
            config.app["video_source"] = params.video_source
    
            if params.video_source == "local":
                # Streamlit 的文件类型校验对扩展名大小写敏感，这里同时放行大小写两种形式。
                local_file_types = ["mp4", "mov", "avi", "flv", "mkv", "jpg", "jpeg", "png"]
                uploaded_files = st.file_uploader(
                    tr("Upload Local Files"),
                    type=local_file_types + [file_type.upper() for file_type in local_file_types],
                    accept_multiple_files=True,
                )
    
            selected_index = st.selectbox(
                tr("Video Concat Mode"),
                index=1,
                options=range(
                    len(video_concat_modes)
                ),  # Use the index as the internal option value
                format_func=lambda x: video_concat_modes[x][
                    0
                ],  # The label is displayed to the user
            )
            params.video_concat_mode = VideoConcatMode(
                video_concat_modes[selected_index][1]
            )
    
            # 视频转场模式
            video_transition_modes = [
                (tr("None"), VideoTransitionMode.none.value),
                (tr("Shuffle"), VideoTransitionMode.shuffle.value),
                (tr("FadeIn"), VideoTransitionMode.fade_in.value),
                (tr("FadeOut"), VideoTransitionMode.fade_out.value),
                (tr("SlideIn"), VideoTransitionMode.slide_in.value),
                (tr("SlideOut"), VideoTransitionMode.slide_out.value),
            ]
            selected_index = st.selectbox(
                tr("Video Transition Mode"),
                options=range(len(video_transition_modes)),
                format_func=lambda x: video_transition_modes[x][0],
                index=0,
            )
            params.video_transition_mode = VideoTransitionMode(
                video_transition_modes[selected_index][1]
            )
    
            video_aspect_ratios = [
                (tr("Portrait"), VideoAspect.portrait.value),
                (tr("Landscape"), VideoAspect.landscape.value),
            ]
            # Coverr 库 99% 是 16:9 横屏,默认竖屏会让画面被大量黑边包围。
            # 用 source-specific widget key 让每个 source 各自记忆 aspect 选择:
            #   - 首次切到 coverr → 默认 Landscape(index=1)
            #   - 其他 source 沿用 Portrait(index=0)
            #   - 用户在某 source 下手动改过 aspect,session_state 会记住,
            #     下次回到同一 source 时尊重用户选择,不会再被强制覆盖。
            default_aspect_index = 1 if params.video_source == "coverr" else 0
            selected_index = st.selectbox(
                tr("Video Ratio"),
                options=range(
                    len(video_aspect_ratios)
                ),  # Use the index as the internal option value
                format_func=lambda x: video_aspect_ratios[x][
                    0
                ],  # The label is displayed to the user
                index=default_aspect_index,
                key=f"video_aspect_for_{params.video_source}",
            )
            params.video_aspect = VideoAspect(video_aspect_ratios[selected_index][1])
    
            params.video_clip_duration = st.selectbox(
                tr("Clip Duration"), options=[2, 3, 4, 5, 6, 7, 8, 9, 10], index=1
            )
            params.video_count = st.selectbox(
                tr("Number of Videos Generated Simultaneously"),
                options=[1, 2, 3, 4, 5],
                index=0,
            )

    with tab_audio:
        with st.container(border=True):
            render_panel_header(tr_plain("Audio Settings"))
    
            # 添加TTS服务器选择下拉框
            tts_servers = [
                (voice.NO_VOICE_NAME, tr("No Voice")),
                ("azure-tts-v1", "Azure TTS V1"),
                ("azure-tts-v2", "Azure TTS V2"),
                ("siliconflow", "SiliconFlow TTS"),
                ("gemini-tts", "Google Gemini TTS"),
                ("mimo-tts", "Xiaomi MiMo TTS"),
                ("elevenlabs", "ElevenLabs TTS"),
            ]
    
            # 获取保存的TTS服务器，默认为v1
            saved_tts_server = config.ui.get("tts_server", "azure-tts-v1")
            saved_tts_server_index = 0
            for i, (server_value, _) in enumerate(tts_servers):
                if server_value == saved_tts_server:
                    saved_tts_server_index = i
                    break
    
            selected_tts_server_index = st.selectbox(
                tr("TTS Servers"),
                options=range(len(tts_servers)),
                format_func=lambda x: tts_servers[x][1],
                index=saved_tts_server_index,
            )
    
            selected_tts_server = tts_servers[selected_tts_server_index][0]
            config.ui["tts_server"] = selected_tts_server
    
            # 根据选择的TTS服务器获取声音列表
            filtered_voices = []
    
            if selected_tts_server == voice.NO_VOICE_NAME:
                # 无配音是显式模式，只提供一个稳定 sentinel。这样普通 TTS 的空配置
                # 不会被误判为静音，后端也能继续通过同一条音频/字幕流程生成视频。
                filtered_voices = [voice.NO_VOICE_NAME]
            elif selected_tts_server == "siliconflow":
                # 获取硅基流动的声音列表
                filtered_voices = voice.get_siliconflow_voices()
            elif selected_tts_server == "gemini-tts":
                # 获取Gemini TTS的声音列表
                filtered_voices = voice.get_gemini_voices()
            elif selected_tts_server == "mimo-tts":
                # 获取 Xiaomi MiMo TTS 的预置音色列表
                filtered_voices = voice.get_mimo_voices()
            elif selected_tts_server == "elevenlabs":
                # Read from session_state first so the API key is available before
                # the Play Voice button runs (which is earlier in the script than
                # the API key text_input widget).
                saved_elevenlabs_api_key = st.session_state.get(
                    "elevenlabs_api_key_input",
                    config.elevenlabs.get("api_key", ""),
                )
                if saved_elevenlabs_api_key:
                    config.elevenlabs["api_key"] = saved_elevenlabs_api_key
                cache_key = f"elevenlabs_voices_{saved_elevenlabs_api_key}"
                if cache_key not in st.session_state:
                    st.session_state[cache_key] = voice.get_elevenlabs_voices(
                        saved_elevenlabs_api_key
                    )
                filtered_voices = st.session_state[cache_key]
            else:
                # 获取Azure的声音列表
                all_voices = voice.get_all_azure_voices(filter_locals=None)
    
                # 根据选择的TTS服务器筛选声音
                for v in all_voices:
                    if selected_tts_server == "azure-tts-v2":
                        # V2版本的声音名称中包含"v2"
                        if "V2" in v:
                            filtered_voices.append(v)
                    else:
                        # V1版本的声音名称中不包含"v2"
                        if "V2" not in v:
                            filtered_voices.append(v)
    
            if selected_tts_server == voice.NO_VOICE_NAME:
                friendly_names = {voice.NO_VOICE_NAME: tr("No Voice")}
            else:
                def _friendly(v):
                    if voice.is_elevenlabs_voice(v):
                        parts = v.split(":", 2)
                        return parts[2] if len(parts) >= 3 else v
                    return (
                        v.replace("Female", tr("Female"))
                        .replace("Male", tr("Male"))
                        .replace("Neural", "")
                    )
                friendly_names = {v: _friendly(v) for v in filtered_voices}
    
            saved_voice_name = config.ui.get("voice_name", "")
            saved_voice_name_index = 0
    
            # 检查保存的声音是否在当前筛选的声音列表中
            if saved_voice_name in friendly_names:
                saved_voice_name_index = list(friendly_names.keys()).index(saved_voice_name)
            else:
                # 如果不在，则根据当前UI语言选择一个默认声音
                for i, v in enumerate(filtered_voices):
                    if v.lower().startswith(st.session_state["ui_language"].lower()):
                        saved_voice_name_index = i
                        break
    
            # 如果没有找到匹配的声音，使用第一个声音
            if saved_voice_name_index >= len(friendly_names) and friendly_names:
                saved_voice_name_index = 0
    
            # 确保有声音可选
            if friendly_names:
                selected_friendly_name = st.selectbox(
                    tr("Speech Synthesis"),
                    options=list(friendly_names.values()),
                    index=min(saved_voice_name_index, len(friendly_names) - 1)
                    if friendly_names
                    else 0,
                )
    
                voice_name = list(friendly_names.keys())[
                    list(friendly_names.values()).index(selected_friendly_name)
                ]
                params.voice_name = voice_name
                config.ui["voice_name"] = voice_name
            else:
                # 如果没有声音可选，显示提示信息
                st.warning(
                    tr(
                        "No voices available for the selected TTS server. Please select another server."
                    )
                )
                voice_name = ""
                params.voice_name = ""
                config.ui["voice_name"] = ""
    
            # 无配音模式会生成静音占位音频，不展示试听按钮，避免用户误以为需要测试声音。
            if (
                friendly_names
                and selected_tts_server != voice.NO_VOICE_NAME
                and st.button(tr("Play Voice"))
            ):
                play_content = params.video_subject
                if not play_content:
                    play_content = params.video_script
                if not play_content:
                    # For ElevenLabs voices, detect language from the display name
                    # so the test text matches the voice's language.
                    if voice.is_elevenlabs_voice(voice_name):
                        parts = voice_name.split(":", 2)
                        display = parts[2] if len(parts) >= 3 else ""
                        _vi_chars = set("àáâãèéêìíòóôõùúýăđơưÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯ")
                        if any(c in _vi_chars for c in display):
                            play_content = "Xin chào, đây là đoạn âm thanh thử nghiệm giọng nói."
                        else:
                            play_content = tr("Voice Example")
                    else:
                        play_content = tr("Voice Example")
                with st.spinner(tr("Synthesizing Voice")):
                    temp_dir = utils.storage_dir("temp", create=True)
                    audio_file = os.path.join(temp_dir, f"tmp-voice-{str(uuid4())}.mp3")
                    sub_maker = voice.tts(
                        text=play_content,
                        voice_name=voice_name,
                        voice_rate=params.voice_rate,
                        voice_file=audio_file,
                        voice_volume=params.voice_volume,
                    )
                    # if the voice file generation failed, try again with a default content.
                    if not sub_maker:
                        play_content = "This is a example voice. if you hear this, the voice synthesis failed with the original content."
                        sub_maker = voice.tts(
                            text=play_content,
                            voice_name=voice_name,
                            voice_rate=params.voice_rate,
                            voice_file=audio_file,
                            voice_volume=params.voice_volume,
                        )
    
                    if sub_maker and os.path.exists(audio_file):
                        st.audio(audio_file, format="audio/mp3")
                        if os.path.exists(audio_file):
                            os.remove(audio_file)
    
            # 当选择V2版本或者声音是V2声音时，显示服务区域和API key输入框
            if selected_tts_server == "azure-tts-v2" or (
                voice_name and voice.is_azure_v2_voice(voice_name)
            ):
                saved_azure_speech_region = config.azure.get("speech_region", "")
                saved_azure_speech_key = config.azure.get("speech_key", "")
                azure_speech_region = st.text_input(
                    tr("Speech Region"),
                    value=saved_azure_speech_region,
                    key="azure_speech_region_input",
                )
                azure_speech_key = st.text_input(
                    tr("Speech Key"),
                    value=saved_azure_speech_key,
                    type="password",
                    key="azure_speech_key_input",
                )
                config.azure["speech_region"] = azure_speech_region
                config.azure["speech_key"] = azure_speech_key
    
            # 当选择硅基流动时，显示API key输入框和说明信息
            if selected_tts_server == "siliconflow" or (
                voice_name and voice.is_siliconflow_voice(voice_name)
            ):
                saved_siliconflow_api_key = config.siliconflow.get("api_key", "")
    
                siliconflow_api_key = st.text_input(
                    tr("SiliconFlow API Key"),
                    value=saved_siliconflow_api_key,
                    type="password",
                    key="siliconflow_api_key_input",
                )
    
                # 显示硅基流动的说明信息
                st.info(
                    tr("SiliconFlow TTS Settings")
                    + ":\n"
                    + "- "
                    + tr("Speed: Range [0.25, 4.0], default is 1.0")
                    + "\n"
                    + "- "
                    + tr("Volume: Uses Speech Volume setting, default 1.0 maps to gain 0")
                )
    
                config.siliconflow["api_key"] = siliconflow_api_key
    
            # 当选择 Xiaomi MiMo TTS 时，复用 MiMo LLM provider 的 API Key。
            # 这样用户如果同时使用 MiMo 生成文案和语音，只需要维护一份密钥。
            if selected_tts_server == "mimo-tts" or (
                voice_name and voice.is_mimo_voice(voice_name)
            ):
                saved_mimo_api_key = config.app.get("mimo_api_key", "")
    
                mimo_api_key = st.text_input(
                    tr("MiMo API Key"),
                    value=saved_mimo_api_key,
                    type="password",
                    key="mimo_tts_api_key_input",
                )
    
                st.info(
                    tr("MiMo TTS Settings")
                    + ":\n"
                    + "- "
                    + tr("Uses Xiaomi MiMo V2.5 TTS preset voices")
                    + "\n"
                    + "- "
                    + tr("Speed and volume are currently handled by the provider defaults")
                )
    
                config.app["mimo_api_key"] = mimo_api_key
    
            # ElevenLabs API key section
            if selected_tts_server == "elevenlabs" or (
                voice_name and voice.is_elevenlabs_voice(voice_name)
            ):
                saved_elevenlabs_api_key = config.elevenlabs.get("api_key", "")
    
                elevenlabs_api_key = st.text_input(
                    tr("ElevenLabs API Key"),
                    value=saved_elevenlabs_api_key,
                    type="password",
                    key="elevenlabs_api_key_input",
                )
    
                _elevenlabs_models = [
                    "eleven_multilingual_v2",
                    "eleven_flash_v2_5",
                    "eleven_v3",
                ]
                saved_elevenlabs_model = config.elevenlabs.get(
                    "model_id", "eleven_multilingual_v2"
                )
                if saved_elevenlabs_model not in _elevenlabs_models:
                    saved_elevenlabs_model = "eleven_multilingual_v2"
                elevenlabs_model = st.selectbox(
                    tr("ElevenLabs Model"),
                    options=_elevenlabs_models,
                    index=_elevenlabs_models.index(saved_elevenlabs_model),
                    key="elevenlabs_model_select",
                )
                config.elevenlabs["model_id"] = elevenlabs_model
    
                st.info(
                    "ElevenLabs TTS Settings:\n"
                    "- Get your API key at https://elevenlabs.io/app/settings/api-keys\n"
                    "- Mark voices as ★ Favorite in the ElevenLabs voice library to make them appear here"
                )
    
                if elevenlabs_api_key != saved_elevenlabs_api_key:
                    for k in list(st.session_state.keys()):
                        if k.startswith("elevenlabs_voices_"):
                            del st.session_state[k]
    
                config.elevenlabs["api_key"] = elevenlabs_api_key
    
            params.voice_volume = st.selectbox(
                tr("Speech Volume"),
                options=[0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0],
                index=2,
            )
    
            params.voice_rate = st.selectbox(
                tr("Speech Rate"),
                options=[0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.0],
                index=2,
            )
    
            custom_audio_file_types = ["mp3", "wav", "m4a", "aac", "flac", "ogg"]
            uploaded_audio_file = st.file_uploader(
                tr("Custom Audio File"),
                type=custom_audio_file_types
                + [file_type.upper() for file_type in custom_audio_file_types],
                accept_multiple_files=False,
                key="custom_audio_file_uploader",
            )
            if uploaded_audio_file:
                st.audio(uploaded_audio_file, format="audio/mp3")
                st.info(
                    tr(
                        "Custom audio will be used directly. TTS synthesis will be skipped for this task."
                    )
                )
    
            bgm_options = [
                (tr("No Background Music"), ""),
                (tr("Random Background Music"), "random"),
                (tr("Custom Background Music"), "custom"),
            ]
            selected_index = st.selectbox(
                tr("Background Music"),
                index=1,
                options=range(
                    len(bgm_options)
                ),  # Use the index as the internal option value
                format_func=lambda x: bgm_options[x][
                    0
                ],  # The label is displayed to the user
            )
            # Get the selected background music type
            params.bgm_type = bgm_options[selected_index][1]
    
            # Show or hide components based on the selection
            if params.bgm_type == "custom":
                custom_bgm_file = st.text_input(
                    tr("Custom Background Music File"), key="custom_bgm_file_input"
                )
                if custom_bgm_file:
                    # 这里不直接用 os.path.exists 判断，因为用户常见输入是
                    # output000.mp3，这个文件名需要由服务层映射到 resource/songs
                    # 目录后再校验。服务层会统一限制目录和文件类型，避免任意路径读取。
                    params.bgm_file = custom_bgm_file.strip()
                    # st.write(f":red[已选择自定义背景音乐]：**{custom_bgm_file}**")
            params.bgm_volume = st.selectbox(
                tr("Background Music Volume"),
                options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                index=2,
            )

    with tab_subtitle:
        with st.container(border=True):
            render_panel_header(tr_plain("Subtitle Settings"))
            params.subtitle_enabled = st.checkbox(tr("Enable Subtitles"), value=True)
            font_names = get_all_fonts()
            saved_font_name = config.ui.get("font_name", "MicrosoftYaHeiBold.ttc")
            saved_font_name_index = 0
            if saved_font_name in font_names:
                saved_font_name_index = font_names.index(saved_font_name)
            params.font_name = st.selectbox(
                tr("Font"), font_names, index=saved_font_name_index
            )
            config.ui["font_name"] = params.font_name
    
            subtitle_positions = [
                (tr("Top"), "top"),
                (tr("Center"), "center"),
                (tr("Bottom"), "bottom"),
                (tr("Custom"), "custom"),
            ]
            saved_subtitle_position = config.ui.get("subtitle_position", "bottom")
            saved_position_index = 2
            for i, (_, pos_value) in enumerate(subtitle_positions):
                if pos_value == saved_subtitle_position:
                    saved_position_index = i
                    break
            selected_index = st.selectbox(
                tr("Position"),
                index=saved_position_index,
                options=range(len(subtitle_positions)),
                format_func=lambda x: subtitle_positions[x][0],
            )
            params.subtitle_position = subtitle_positions[selected_index][1]
            config.ui["subtitle_position"] = params.subtitle_position
    
            if params.subtitle_position == "custom":
                saved_custom_position = config.ui.get("custom_position", 70.0)
                custom_position = st.text_input(
                    tr("Custom Position (% from top)"),
                    value=str(saved_custom_position),
                    key="custom_position_input",
                )
                try:
                    params.custom_position = float(custom_position)
                    if params.custom_position < 0 or params.custom_position > 100:
                        st.error(tr("Please enter a value between 0 and 100"))
                    else:
                        config.ui["custom_position"] = params.custom_position
                except ValueError:
                    st.error(tr("Please enter a valid number"))
    
            font_cols = st.columns([0.3, 0.7])
            with font_cols[0]:
                saved_text_fore_color = config.ui.get("text_fore_color", "#FFFFFF")
                params.text_fore_color = st.color_picker(
                    tr("Font Color"), saved_text_fore_color
                )
                config.ui["text_fore_color"] = params.text_fore_color
    
            with font_cols[1]:
                saved_font_size = config.ui.get("font_size", 60)
                params.font_size = st.slider(tr("Font Size"), 30, 100, saved_font_size)
                config.ui["font_size"] = params.font_size
    
            stroke_cols = st.columns([0.3, 0.7])
            with stroke_cols[0]:
                params.stroke_color = st.color_picker(tr("Stroke Color"), "#000000")
            with stroke_cols[1]:
                params.stroke_width = st.slider(tr("Stroke Width"), 0.0, 10.0, 1.5)
    
            subtitle_bg_cols = st.columns([0.4, 0.6])
            saved_subtitle_background_enabled = config.ui.get(
                "subtitle_background_enabled", True
            )
            with subtitle_bg_cols[0]:
                subtitle_background_enabled = st.checkbox(
                    tr("Enable Subtitle Background"),
                    value=saved_subtitle_background_enabled,
                )
            config.ui["subtitle_background_enabled"] = subtitle_background_enabled
            if subtitle_background_enabled:
                with subtitle_bg_cols[1]:
                    saved_subtitle_background_color = config.ui.get(
                        "subtitle_background_color", "#000000"
                    )
                    params.text_background_color = st.color_picker(
                        tr("Subtitle Background Color"),
                        saved_subtitle_background_color,
                    )
                    config.ui["subtitle_background_color"] = params.text_background_color
            else:
                params.text_background_color = False
    
            saved_rounded_subtitle_background = config.ui.get(
                "rounded_subtitle_background", False
            )
            # 背景关闭时，圆角背景没有可渲染的底色。这里禁用控件并保留原配置，
            # 用户下次重新开启字幕背景后，可以继续使用之前保存的圆角偏好。
            params.rounded_subtitle_background = st.checkbox(
                tr("Rounded Subtitle Background"),
                value=(
                    saved_rounded_subtitle_background
                    if subtitle_background_enabled
                    else False
                ),
                help=tr("Rounded Subtitle Background Help"),
                disabled=not subtitle_background_enabled,
            )
            if subtitle_background_enabled:
                config.ui["rounded_subtitle_background"] = (
                    params.rounded_subtitle_background
                )

    if start_button:
        config.save_config()
        task_id = str(uuid4())
        if not params.video_subject and not params.video_script:
            st.error(tr("Video Script and Subject Cannot Both Be Empty"))
            scroll_to_bottom()
            st.stop()
    
        if params.video_source not in ["pexels", "pixabay", "coverr", "local"]:
            st.error(tr("Please Select a Valid Video Source"))
            scroll_to_bottom()
            st.stop()
    
        if params.video_source == "pexels" and not config.app.get("pexels_api_keys", ""):
            st.error(tr("Please Enter the Pexels API Key"))
            scroll_to_bottom()
            st.stop()
    
        if params.video_source == "pixabay" and not config.app.get("pixabay_api_keys", ""):
            st.error(tr("Please Enter the Pixabay API Key"))
            scroll_to_bottom()
            st.stop()
    
        if params.video_source == "coverr" and not config.app.get("coverr_api_keys", ""):
            st.error(tr("Please Enter the Coverr API Key"))
            scroll_to_bottom()
            st.stop()
    
        if uploaded_audio_file:
            task_dir = utils.task_dir(task_id)
            # 上传文件名来自浏览器，不能直接拼到磁盘路径里；这里只保留扩展名，
            # 并使用固定文件名保存到当前任务目录，避免路径穿越或特殊字符问题。
            _, audio_ext = os.path.splitext(os.path.basename(uploaded_audio_file.name))
            audio_ext = audio_ext.lower() or ".mp3"
            custom_audio_path = os.path.join(task_dir, f"custom-audio{audio_ext}")
            with open(custom_audio_path, "wb") as f:
                f.write(uploaded_audio_file.getbuffer())
            params.custom_audio_file = custom_audio_path
    
        if uploaded_files:
            local_videos_dir = utils.storage_dir("local_videos", create=True)
            # 每次重新上传时都以本次选择的素材为准，避免旧素材不断重复追加。
            params.video_materials = []
            persisted_local_materials = []
            for file in uploaded_files:
                file_path = os.path.join(local_videos_dir, f"{file.file_id}_{file.name}")
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
                    m = MaterialInfo()
                    m.provider = "local"
                    m.url = file_path
                    params.video_materials.append(m)
                    persisted_local_materials.append(
                        {
                            "provider": m.provider,
                            "url": m.url,
                            "duration": m.duration,
                        }
                    )
            # 将已上传并保存到本地的视频素材写入会话，供后续只改文案时直接复用。
            st.session_state["local_video_materials"] = persisted_local_materials
        elif params.video_source == "local" and st.session_state["local_video_materials"]:
            # 当用户没有重新上传文件时，复用最近一次已经保存到磁盘的本地素材列表。
            params.video_materials = []
            for material in st.session_state["local_video_materials"]:
                m = MaterialInfo()
                m.provider = material.get("provider", "local")
                m.url = material.get("url", "")
                m.duration = material.get("duration", 0)
                if m.url:
                    params.video_materials.append(m)
    
        log_container = st.empty()
        log_records = []
    
        def log_received(msg):
            if config.ui["hide_log"]:
                return
            with log_container:
                log_records.append(msg)
                st.code("\n".join(log_records))
    
        logger.add(log_received)
    
        st.toast(tr("Generating Video"))
        logger.info(tr("Start Generating Video"))
        output_dir = utils.get_video_output_directory()
        if output_dir:
            logger.info(f"video output directory: {output_dir}")
        logger.info(utils.to_json(params))
        scroll_to_bottom()
    
        result = tm.start(task_id=task_id, params=params)
        if not result or "videos" not in result:
            st.error(tr("Video Generation Failed"))
            logger.error(tr("Video Generation Failed"))
            scroll_to_bottom()
            st.stop()
    
        video_files = result.get("exported_videos") or result.get("videos", [])
        st.success(tr("Video Generation Completed"))
        output_dir = utils.get_video_output_directory()
        if output_dir:
            st.info(f"{tr('Videos Saved To')}: `{output_dir}`")
        try:
            if video_files:
                player_cols = st.columns(len(video_files) * 2 + 1)
                for i, url in enumerate(video_files):
                    player_cols[i * 2 + 1].video(url)
        except Exception:
            pass

        if output_dir:
            utils.open_folder(output_dir)
        else:
            open_task_folder(task_id)
        logger.info(tr("Video Generation Completed"))
        scroll_to_bottom()

config.save_config()
