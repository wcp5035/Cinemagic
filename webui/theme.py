"""Streamlit UI theme helpers for Cinemagic dashboard layout."""

from __future__ import annotations

import html


def get_theme_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --mpt-primary: #6366f1;
    --mpt-primary-dark: #4f46e5;
    --mpt-primary-light: #eef2ff;
    --mpt-sidebar: #1a1d3f;
    --mpt-sidebar-top: #222654;
    --mpt-sidebar-hover: rgba(255, 255, 255, 0.12);
    --mpt-sidebar-active: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
    --mpt-sidebar-text: #f1f5f9;
    --mpt-sidebar-text-muted: #cbd5e1;
    --mpt-sidebar-text-dim: #94a3b8;
    --mpt-bg: #f4f6fb;
    --mpt-card: #ffffff;
    --mpt-text: #0f172a;
    --mpt-muted: #64748b;
    --mpt-border: #e2e8f0;
    --mpt-success: #10b981;
    --mpt-success-bg: #ecfdf5;
    --mpt-warning-bg: #fff7ed;
    --mpt-radius: 16px;
    --mpt-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

#MainMenu, footer {
    visibility: hidden;
    height: 0;
    display: none;
}

/* 保留顶栏，否则侧边栏收起后无法再次展开 */
header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--mpt-sidebar-top) 0%, var(--mpt-sidebar) 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 4px 0 24px rgba(15, 23, 42, 0.12);
    min-width: 280px !important;
    width: 280px !important;
    color: var(--mpt-sidebar-text);
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] p,
[data-testid="stSidebar"] [data-testid="stMarkdown"] li,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: var(--mpt-sidebar-text-muted) !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.18);
    margin: 1rem 0;
}

.mpt-sidebar-nav-label {
    color: var(--mpt-sidebar-text-dim) !important;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0 0 10px 2px;
}

[data-testid="stSidebar"] .stSelectbox label {
    color: var(--mpt-sidebar-text-dim) !important;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.96) !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    color: #0f172a !important;
    border-radius: 10px;
    min-height: 42px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div[data-baseweb="select"] {
    color: #0f172a !important;
}

[data-testid="stSidebar"] .stSelectbox svg {
    fill: #475569 !important;
}

/* 防止侧边栏被折叠后无法找回 */
[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 280px !important;
    margin-left: 0 !important;
    transform: translateX(0) !important;
    visibility: visible !important;
}

.stApp {
    background: var(--mpt-bg);
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2.5rem;
    max-width: 1360px;
}

[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] > div:first-child {
    background: transparent;
    padding-top: 0.5rem;
}

.mpt-sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 4px 20px;
    margin-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.mpt-sidebar-brand-icon {
    width: 44px;
    height: 44px;
    border-radius: 13px;
    background: linear-gradient(135deg, #818cf8 0%, var(--mpt-primary) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.45);
    flex-shrink: 0;
}

.mpt-sidebar-brand-title {
    color: #ffffff !important;
    font-size: 1.05rem;
    font-weight: 700;
    line-height: 1.25;
    letter-spacing: 0.01em;
}

.mpt-sidebar-social {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #f8fafc !important;
    text-decoration: none !important;
    transition: background 0.18s ease, border-color 0.18s ease, transform 0.15s ease;
}

.mpt-sidebar-social:hover {
    background: rgba(255, 255, 255, 0.16);
    border-color: rgba(255, 255, 255, 0.22);
    transform: translateY(-1px);
}

.mpt-sidebar-social svg {
    width: 18px;
    height: 18px;
    display: block;
}

.mpt-sidebar-footer {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
}

.mpt-sidebar-version {
    color: var(--mpt-sidebar-text-dim) !important;
    font-size: 0.82rem;
}

.mpt-sidebar-brand-sub {
    color: var(--mpt-sidebar-text-muted) !important;
    font-size: 0.78rem;
    margin-top: 4px;
}

div[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 6px;
    padding: 4px 0;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px;
    padding: 12px 16px !important;
    margin: 0 !important;
    transition: background 0.18s ease, border-color 0.18s ease, transform 0.15s ease;
    cursor: pointer;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: var(--mpt-sidebar-hover) !important;
    border-color: rgba(255, 255, 255, 0.22) !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
    background: var(--mpt-sidebar-active) !important;
    border-color: rgba(199, 210, 254, 0.6) !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

div[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
    display: none;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label p,
div[data-testid="stSidebar"] div[role="radiogroup"] label span,
div[data-testid="stSidebar"] div[role="radiogroup"] label div {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: var(--mpt-sidebar-text) !important;
    line-height: 1.4 !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p,
div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] span,
div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] div {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* 侧边栏导航按钮（替代 radio，避免主题色覆盖文字） */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] div.stButton {
    margin-bottom: 6px;
}

section[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    min-height: 44px;
    text-align: left;
    justify-content: flex-start;
    transition: background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

section[data-testid="stSidebar"] div.stButton > button[kind="secondary"],
section[data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-secondary"] {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
}

section[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover,
section[data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(255, 255, 255, 0.18) !important;
    border-color: rgba(255, 255, 255, 0.28) !important;
    color: #ffffff !important;
}

section[data-testid="stSidebar"] div.stButton > button[kind="primary"],
section[data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(199, 210, 254, 0.55) !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.42) !important;
}

section[data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover,
section[data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(90deg, #7577f5 0%, #5b52ee 100%) !important;
    color: #ffffff !important;
}

section[data-testid="stSidebar"] .mpt-sidebar-brand-title,
section[data-testid="stSidebar"] .mpt-sidebar-brand-title * {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] .mpt-sidebar-brand-sub {
    color: #cbd5e1 !important;
}

section[data-testid="stSidebar"] .mpt-sidebar-nav-label {
    color: #94a3b8 !important;
}

section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #94a3b8 !important;
}

.mpt-page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.mpt-page-title {
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--mpt-text);
    line-height: 1.15;
    margin: 0;
    letter-spacing: -0.02em;
}

.mpt-page-subtitle {
    font-size: 0.92rem;
    color: var(--mpt-muted);
    margin-top: 6px;
}

.mpt-card {
    background: var(--mpt-card);
    border: 1px solid var(--mpt-border);
    border-radius: var(--mpt-radius);
    padding: 20px 22px;
    box-shadow: var(--mpt-shadow);
    margin-bottom: 18px;
}

.mpt-card-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
}

.mpt-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
}

.mpt-badge-success {
    background: var(--mpt-success-bg);
    color: #047857;
}

.mpt-badge-warning {
    background: var(--mpt-warning-bg);
    color: #c2410c;
}

.mpt-badge-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
}

.mpt-meta {
    color: var(--mpt-muted);
    font-size: 0.84rem;
    margin-top: 10px;
    line-height: 1.5;
    word-break: break-all;
}

.mpt-meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 8px 20px;
    margin-top: 14px;
}

.mpt-meta-item {
    color: var(--mpt-muted);
    font-size: 0.84rem;
    line-height: 1.45;
}

.mpt-meta-item strong {
    color: var(--mpt-text);
    font-weight: 600;
}

.mpt-section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.02rem;
    font-weight: 700;
    color: var(--mpt-text);
    margin: 0 0 16px;
}

.mpt-section-title::before {
    content: "";
    width: 4px;
    height: 20px;
    border-radius: 999px;
    background: linear-gradient(180deg, #818cf8 0%, var(--mpt-primary) 100%);
    flex-shrink: 0;
}

.mpt-panel-title {
    font-size: 0.98rem;
    font-weight: 700;
    color: var(--mpt-text);
    margin: 0 0 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f1f5f9;
}

.mpt-steps {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 18px;
}

.mpt-step {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-radius: 999px;
    background: #fff;
    border: 1px solid var(--mpt-border);
    color: var(--mpt-muted);
    font-size: 0.82rem;
    font-weight: 600;
}

.mpt-step-num {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--mpt-primary-light);
    color: var(--mpt-primary-dark);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 700;
}

.mpt-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
}

.mpt-chip {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: 999px;
    background: #f8fafc;
    border: 1px solid var(--mpt-border);
    color: var(--mpt-text);
    font-size: 0.8rem;
}

.mpt-chip-accent {
    background: var(--mpt-primary-light);
    border-color: #c7d2fe;
    color: #4338ca;
}

.mpt-cta-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
    border: 1px solid #dbeafe;
    border-radius: var(--mpt-radius);
    padding: 22px 24px;
    box-shadow: 0 12px 32px rgba(99, 102, 241, 0.1);
    margin-top: 8px;
    margin-bottom: 12px;
}

.mpt-cta-hint {
    color: var(--mpt-muted);
    font-size: 0.88rem;
    margin: 0 0 16px;
    line-height: 1.55;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--mpt-card);
    border: 1px solid var(--mpt-border) !important;
    border-radius: var(--mpt-radius) !important;
    box-shadow: var(--mpt-shadow);
    padding: 0.35rem 0.15rem 0.15rem;
}

div[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
    border-bottom: 1px solid var(--mpt-border);
    padding-bottom: 2px;
}

div[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent;
    border-radius: 10px 10px 0 0;
    color: var(--mpt-muted);
    font-weight: 600;
    padding: 10px 18px;
    border: none;
}

div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    background: var(--mpt-primary-light);
    color: var(--mpt-primary-dark);
}

div[data-testid="stTabs"] [data-baseweb="tab-panel"] {
    padding-top: 18px;
}

.streamlit-expanderHeader {
    background: #f8fafc;
    border-radius: 10px;
    font-weight: 600;
    color: var(--mpt-text);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #818cf8 0%, var(--mpt-primary) 100%);
    border: none;
    border-radius: 12px;
    font-weight: 600;
    min-height: 48px;
    box-shadow: 0 10px 24px rgba(99, 102, 241, 0.28);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #6366f1 0%, var(--mpt-primary-dark) 100%);
    box-shadow: 0 12px 28px rgba(99, 102, 241, 0.34);
    transform: translateY(-1px);
}

.stButton > button[kind="secondary"] {
    border-radius: 10px;
    border-color: var(--mpt-border);
    font-weight: 500;
}

.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div,
.stNumberInput input, .stFileUploader section, .stMultiSelect [data-baseweb="select"] > div {
    border-radius: 10px !important;
    border-color: #dbe3ef !important;
}

.stTextInput label, .stTextArea label, .stSelectbox label, .stSlider label,
.stCheckbox label, .stFileUploader label {
    color: var(--mpt-text) !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
}

h1 { padding-top: 0 !important; }

.mpt-tutorial-card {
    background: var(--mpt-card);
    border: 1px solid var(--mpt-border);
    border-radius: var(--mpt-radius);
    padding: 22px 24px;
    box-shadow: var(--mpt-shadow);
}

.mpt-tutorial-card a {
    color: var(--mpt-primary);
    text-decoration: none;
    font-weight: 600;
}

.mpt-tutorial-card a:hover { text-decoration: underline; }

.mpt-link-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 12px;
    margin-top: 8px;
}

.mpt-link-item {
    display: block;
    padding: 14px 16px;
    border-radius: 12px;
    background: #f8fafc;
    border: 1px solid var(--mpt-border);
    color: var(--mpt-text);
    text-decoration: none;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.mpt-link-item:hover {
    border-color: #c7d2fe;
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.08);
    text-decoration: none;
}

.mpt-link-item-title {
    font-weight: 700;
    font-size: 0.92rem;
    color: var(--mpt-primary-dark);
}

.mpt-link-item-desc {
    font-size: 0.8rem;
    color: var(--mpt-muted);
    margin-top: 4px;
}

.mpt-tutorial-steps {
    background: var(--mpt-card);
    border: 1px solid var(--mpt-border);
    border-radius: var(--mpt-radius);
    padding: 8px 24px 18px;
    box-shadow: var(--mpt-shadow);
    margin-bottom: 20px;
}

.mpt-tutorial-steps ol {
    margin: 0;
    padding-left: 1.2rem;
}

.mpt-tutorial-step {
    padding: 14px 0;
    border-bottom: 1px solid #eef2f7;
}

.mpt-tutorial-step:last-child {
    border-bottom: none;
    padding-bottom: 4px;
}

.mpt-tutorial-step-title {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--mpt-text);
    margin-bottom: 6px;
}

.mpt-tutorial-step-body {
    font-size: 0.86rem;
    line-height: 1.65;
    color: var(--mpt-muted);
    white-space: pre-line;
}
</style>
"""


def render_sidebar_nav(
    options: dict[str, str],
    session_key: str = "current_page",
    default: str | None = None,
) -> str:
    """Render sidebar navigation as styled buttons (avoids radio theme contrast issues)."""
    import streamlit as st

    if default and session_key not in st.session_state:
        st.session_state[session_key] = default

    keys = list(options.keys())
    current = st.session_state.get(session_key, keys[0] if keys else "")

    for key, label in options.items():
        is_active = current == key
        if st.button(
            label,
            key=f"mpt_nav_{key}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state[session_key] = key
            st.rerun()

    return st.session_state.get(session_key, current)


def render_page_header(title: str, subtitle: str) -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="mpt-page-header">
            <div>
                <div class="mpt-page-title">{html.escape(title)}</div>
                <div class="mpt-page-subtitle">{html.escape(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_steps(*labels: str) -> None:
    import streamlit as st

    steps_html = "".join(
        f'<span class="mpt-step"><span class="mpt-step-num">{i + 1}</span>{html.escape(label)}</span>'
        for i, label in enumerate(labels)
    )
    st.markdown(f'<div class="mpt-steps">{steps_html}</div>', unsafe_allow_html=True)


def render_status_card(
    *,
    version: str,
    llm_provider: str,
    llm_configured: bool,
    ready_label: str,
    not_ready_label: str,
    version_label: str,
    llm_label: str,
    material_keys_configured: bool = False,
    material_label: str = "Material API",
    material_ready_label: str = "Configured",
    material_not_ready_label: str = "Not configured",
) -> None:
    import streamlit as st

    badge_class = "mpt-badge-success" if llm_configured else "mpt-badge-warning"
    badge_text = ready_label if llm_configured else not_ready_label
    material_badge_class = (
        "mpt-badge-success" if material_keys_configured else "mpt-badge-warning"
    )
    material_badge_text = (
        material_ready_label if material_keys_configured else material_not_ready_label
    )
    st.markdown(
        f"""
        <div class="mpt-card">
            <div class="mpt-card-row">
                <div>
                    <span class="mpt-badge {badge_class}">
                        <span class="mpt-badge-dot"></span>
                        {html.escape(llm_label)} {html.escape(badge_text)}
                    </span>
                    <span class="mpt-badge {material_badge_class}" style="margin-left:8px;">
                        <span class="mpt-badge-dot"></span>
                        {html.escape(material_label)} {html.escape(material_badge_text)}
                    </span>
                </div>
                <span style="color:#64748b;font-size:0.84rem;font-weight:600;">
                    {html.escape(version_label)} {html.escape(version)}
                </span>
            </div>
            <div class="mpt-meta-grid">
                <div class="mpt-meta-item"><strong>{html.escape(llm_label)}</strong><br>{html.escape(llm_provider)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer(version: str, x_url: str, *, x_title: str = "X") -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="mpt-sidebar-footer">
            <span class="mpt-sidebar-version">v{html.escape(version)}</span>
            <a class="mpt-sidebar-social" href="{html.escape(x_url)}" target="_blank"
               rel="noopener noreferrer" title="{html.escape(x_title)}" aria-label="{html.escape(x_title)}">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path fill="currentColor"
                        d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_header(title: str) -> None:
    import streamlit as st

    st.markdown(
        f'<div class="mpt-panel-title">{html.escape(title)}</div>',
        unsafe_allow_html=True,
    )


def render_generate_cta(title: str, hint: str) -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="mpt-cta-card">
            <div class="mpt-section-title">{html.escape(title)}</div>
            <div class="mpt-cta-hint">{html.escape(hint)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tutorial_steps(steps: list[tuple[str, str]]) -> None:
    import streamlit as st

    items = "".join(
        f"""
        <li class="mpt-tutorial-step">
            <div class="mpt-tutorial-step-title">{html.escape(title)}</div>
            <div class="mpt-tutorial-step-body">{html.escape(body)}</div>
        </li>
        """
        for title, body in steps
    )
    st.markdown(
        f'<div class="mpt-tutorial-steps"><ol>{items}</ol></div>',
        unsafe_allow_html=True,
    )


def render_tutorial_links(links: list[tuple[str, str, str]]) -> None:
    import streamlit as st

    items = "".join(
        f"""
        <a class="mpt-link-item" href="{html.escape(url)}" target="_blank">
            <div class="mpt-link-item-title">{html.escape(title)}</div>
            <div class="mpt-link-item-desc">{html.escape(desc)}</div>
        </a>
        """
        for title, desc, url in links
    )
    st.markdown(
        f'<div class="mpt-tutorial-card"><div class="mpt-link-grid">{items}</div></div>',
        unsafe_allow_html=True,
    )
