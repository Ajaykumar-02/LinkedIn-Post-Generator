import os
import html
import streamlit as st
from dotenv import load_dotenv
from graph import build_graph, get_resources, run_generation

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LinkedIn Post Generator",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

/* ── Root Variables ── */
:root {
    --bg: #0c0a14;
    --surface: #14111f;
    --surface-2: #1c1829;
    --border: #2e2945;
    --accent: #8b5cf6;
    --accent-glow: #a78bfa;
    --accent-2: #34d399;
    --text: #ece9f5;
    --text-muted: #8b86a3;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp { background: var(--bg) !important; }
[data-testid="stHeader"] { background: transparent !important; }

/* Grid background */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        linear-gradient(rgba(139, 92, 246, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(139, 92, 246, 0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
}

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 800;
    line-height: 1.1;
    margin: 0;
    background: linear-gradient(135deg, #ffffff 0%, var(--accent-glow) 50%, var(--accent-2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.card:hover { border-color: var(--accent); }
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, var(--accent), var(--accent-2));
}

.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text);
}
.metric-sub { color: var(--text-muted); font-size: 0.72rem; margin-top: 0.2rem; }

.post-text {
    font-size: 0.92rem;
    line-height: 1.8;
    color: var(--text);
    white-space: pre-wrap;
    word-break: break-word;
}

.text-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-size: 0.82rem;
    line-height: 1.75;
    color: var(--text);
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0.5rem 0 0.8rem 0;
}

.src-list { font-size: 0.78rem; line-height: 1.9; }
.src-list a { color: var(--accent-glow) !important; text-decoration: none; }
.src-list a:hover { text-decoration: underline; }

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.badge-purple { background: rgba(139,92,246,0.2); color: var(--accent-glow); border: 1px solid rgba(139,92,246,0.3); }
.badge-cyan   { background: rgba(52,211,153,0.15); color: var(--accent-2);   border: 1px solid rgba(52,211,153,0.3); }
.badge-green  { background: rgba(16,185,129,0.15); color: var(--success);    border: 1px solid rgba(16,185,129,0.3); }
.badge-red    { background: rgba(239,68,68,0.15);  color: var(--danger);     border: 1px solid rgba(239,68,68,0.3); }

/* ── Inputs & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stTextArea textarea {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
    line-height: 1.6 !important;
    padding: 0.9rem 1rem !important;
}
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(139,92,246,0.2) !important;
}

.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, var(--accent), #6d28d9) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
    text-transform: uppercase !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(139,92,246,0.4) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    text-transform: none !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    text-align: left !important;
}

/* ── Status rows ── */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 1rem;
    background: var(--surface-2);
    border-radius: 8px;
    margin: 0.4rem 0;
    border: 1px solid var(--border);
    font-size: 0.78rem;
}
.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-done  { background: var(--success); box-shadow: 0 0 8px var(--success); }
.dot-error { background: var(--danger);  box-shadow: 0 0 8px var(--danger); }

/* ── Expanders / status ── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-bottom: 0.6rem;
}

hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

.stSpinner > div { border-top-color: var(--accent) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
label { color: var(--text-muted) !important; font-size: 0.8rem !important; }

/* Developer credit */
.dev-credit {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    text-align: center;
}
.dev-credit span { color: var(--accent-glow); font-weight: 600; }
.dev-footer {
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
}
.dev-footer span {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent-glow), var(--accent-2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Social / contact links */
.dev-links {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
    margin-top: 0.8rem;
}
.dev-links a {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.4rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--surface-2);
    color: var(--text-muted) !important;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    text-decoration: none !important;
    transition: all 0.2s;
}
.dev-links a svg { width: 15px; height: 15px; flex-shrink: 0; }
.dev-links a:hover {
    color: var(--accent-glow) !important;
    border-color: var(--accent);
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(139,92,246,0.25);
}
.dev-links.compact a { padding: 0.45rem; border-radius: 8px; }

/* scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
""", unsafe_allow_html=True)

# ─── Developer details ──────────────────────────────────────────────────────────
DEV_EMAIL    = "kumarajay3023ak3@gmail.com"
DEV_LINKEDIN = "https://www.linkedin.com/in/ajay-kumar-63a3b7326/"
DEV_GITHUB   = "https://github.com/Ajaykumar-02"

ICON_MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="22,6 12,13 2,6"/></svg>'
ICON_LINKEDIN = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 1 1 0-4.125 2.062 2.062 0 0 1 0 4.125zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0z"/></svg>'
ICON_GITHUB = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>'


def dev_links_html(compact: bool = False) -> str:
    """Email / LinkedIn / GitHub icon links. compact=True shows icons only."""
    def link(href, icon, label, title):
        text = "" if compact else f"<span>{label}</span>"
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer" title="{title}">{icon}{text}</a>'
    cls = "dev-links compact" if compact else "dev-links"
    return (
        f'<div class="{cls}">'
        + link(f"mailto:{DEV_EMAIL}", ICON_MAIL, "Email", "Email")
        + link(DEV_LINKEDIN, ICON_LINKEDIN, "LinkedIn", "LinkedIn")
        + link(DEV_GITHUB, ICON_GITHUB, "GitHub", "GitHub")
        + '</div>'
    )


# ─── Helpers ────────────────────────────────────────────────────────────────────
def esc(text: str) -> str:
    return html.escape(text or "")


def sources_html(sources: list) -> str:
    items = []
    for s in sources:
        url = s.get("url", "")
        if url.startswith(("http://", "https://")):
            items.append(f'<div>🔗 <a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(s.get("title") or url)}</a></div>')
    return '<div class="src-list">' + "".join(items) + "</div>" if items else ""


def metric_card(label: str, value: str, sub: str = "") -> str:
    return (
        f'<div class="card"><div class="card-title">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-sub">{sub}</div></div>'
    )


def set_topic(text: str):
    st.session_state.topic = text


def clear_all():
    """Clear button: empties the topic box and removes the generated post and its history."""
    st.session_state.topic = ""
    st.session_state.result = None


@st.cache_resource(show_spinner="Loading models and search tool...")
def load_resources():
    return get_resources()


# ─── Session state ──────────────────────────────────────────────────────────────
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "result" not in st.session_state:
    st.session_state.result = None

# ─── API keys ───────────────────────────────────────────────────────────────────
KEYS = {"GROQ_API_KEY": "Groq API key", "TAVILY_API_KEY": "Tavily API key"}
missing_keys = [k for k in KEYS if not os.getenv(k)]

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="hero-title" style="font-size:1.6rem">✍️ LinkedIn<br>Writer</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Write · Review · Refine</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-purple">Settings</span>', unsafe_allow_html=True)
    max_attempts = st.slider("Max review attempts", min_value=1, max_value=5, value=3,
                             help="The writer rewrites the post until the reviewer approves it, or until this limit is reached.")

    st.markdown("---")
    st.markdown('<span class="badge badge-cyan">Try an example</span>', unsafe_allow_html=True)
    examples = [
        "Why every student should build a RAG project",
        "How AI agents are changing software development",
        "Lessons I learned from my first internship",
    ]
    for i, ex in enumerate(examples):
        st.button(ex, key=f"ex_{i}", use_container_width=True, on_click=set_topic, args=(ex,), type="secondary")

    st.markdown("---")
    st.markdown('<span class="badge badge-green">API keys</span>', unsafe_allow_html=True)
    for key, label in KEYS.items():
        ok = bool(os.getenv(key))
        dot = "dot-done" if ok else "dot-error"
        st.markdown(
            f'<div class="status-bar"><div class="status-dot {dot}"></div><span>{label}: {"found" if ok else "missing"}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown('<div class="dev-credit">Developed by<br><span>Ajay Kumar</span></div>', unsafe_allow_html=True)
    st.markdown(dev_links_html(compact=True), unsafe_allow_html=True)

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">LinkedIn Post Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">An AI writer drafts it · an AI reviewer checks it · until it is publish-ready</div>', unsafe_allow_html=True)
st.markdown("---")

if missing_keys:
    st.error(
        "Missing: " + ", ".join(missing_keys) +
        ". Add them to your .env file (local) or to Secrets (Streamlit Cloud), then restart the app."
    )
    st.stop()

st.markdown('<span class="badge badge-purple">Your topic</span>', unsafe_allow_html=True)
topic = st.text_area(
    "Topic",
    key="topic",
    height=110,
    placeholder="What should the LinkedIn post be about? e.g. 'Why every student should learn RAG in 2026'",
    label_visibility="collapsed",
)
btn1, btn2 = st.columns([4, 1], gap="small")
with btn1:
    run_btn = st.button("⚡  Generate Post", use_container_width=True)
with btn2:
    st.button("🗑️ Clear", use_container_width=True, on_click=clear_all, type="secondary")

# ── Generate ────────────────────────────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a topic first.")
    else:
        attempts, log = [], []
        current = None

        with st.status("Generating your post...", expanded=True) as status:
            try:
                graph_app = build_graph(load_resources(), max_attempts=max_attempts)

                for ev in run_generation(graph_app, topic.strip()):
                    kind = ev["event"]

                    if kind == "writer":
                        current = {"attempt": ev["attempt"], "draft": "", "approved": None,
                                   "feedback": "", "query": ev["query"], "sources": []}
                        attempts.append(current)
                        line = f"✍️ Writer started attempt {ev['attempt']}"
                        if ev["query"]:
                            line += f" and is searching the web for: “{ev['query']}”"
                        log.append(line)
                        status.write(line)

                    elif kind == "sources":
                        current["sources"] = ev["sources"]
                        line = f"🔎 Found {len(ev['sources'])} web source(s). Writer is using them."
                        log.append(line)
                        status.write(line)

                    elif kind == "draft":
                        current["draft"] = ev["draft"]
                        words = len(ev["draft"].split())
                        line = f"📝 Draft {current['attempt']} ready ({words} words)"
                        log.append(line)
                        status.write(line)

                    elif kind == "review":
                        current["approved"] = ev["approved"]
                        current["feedback"] = ev["feedback"]
                        line = ("✅ Reviewer approved the post" if ev["approved"]
                                else f"🔁 Reviewer rejected draft {current['attempt']}: {ev['feedback']}")
                        log.append(line)
                        status.write(line)

                final = attempts[-1]
                st.session_state.result = {
                    "topic": topic.strip(),
                    "attempts": attempts,
                    "log": log,
                    "approved": bool(final["approved"]),
                    "max_attempts": max_attempts,
                }
                status.update(label="Done!", state="complete", expanded=False)

            except Exception as e:
                status.update(label="Something went wrong", state="error", expanded=True)
                st.session_state.result = None
                st.error(f"Error: {e}")
                st.stop()

        st.rerun()

# ── Results ─────────────────────────────────────────────────────────────────────
result = st.session_state.result

if result:
    attempts = result["attempts"]
    final = attempts[-1]
    final_text = final["draft"]
    words = len(final_text.split())
    chars = len(final_text)

    if not result["approved"]:
        st.warning(
            f"The reviewer did not approve the post within {result['max_attempts']} attempt(s). "
            "This is the latest draft. Read the reviewer's feedback below and edit it, or generate again."
        )

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(metric_card("Status", "✅ Approved" if result["approved"] else "⚠️ Not approved",
                                "by the AI reviewer"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Attempts", f"{len(attempts)} of {result['max_attempts']}",
                                "write → review rounds"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Length", f"{words} words", f"{chars} characters (LinkedIn limit: 3000)"),
                    unsafe_allow_html=True)

    st.markdown(
        f'<div class="card"><div class="card-title">📝 Final LinkedIn Post</div>'
        f'<div class="post-text">{esc(final_text)}</div></div>',
        unsafe_allow_html=True,
    )

    d1, d2 = st.columns([1, 3], gap="medium")
    with d1:
        st.download_button("⬇️ Download .txt", data=final_text, file_name="linkedin_post.txt",
                           mime="text/plain", use_container_width=True)

    with st.expander("📋 Copy-friendly text (use the copy icon on the top right)"):
        try:
            st.code(final_text, language=None, wrap_lines=True)
        except TypeError:
            st.code(final_text, language=None)

    st.markdown("---")
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.2rem;font-weight:700;margin-bottom:0.8rem">🔍 How it was made</div>', unsafe_allow_html=True)

    for a in attempts:
        if a["approved"] is True:
            verdict, badge = "Approved", "badge-green"
        elif a["approved"] is False:
            verdict, badge = "Rejected", "badge-red"
        else:
            verdict, badge = "Not reviewed", "badge-purple"

        with st.expander(f"Attempt {a['attempt']} · {verdict}"):
            st.markdown(f'<span class="badge {badge}">{verdict}</span>', unsafe_allow_html=True)
            if a["query"]:
                st.markdown(f"🔎 **Search query:** {esc(a['query'])}")
            if a["sources"]:
                st.markdown(sources_html(a["sources"]), unsafe_allow_html=True)
            st.markdown("**Draft**")
            st.markdown(f'<div class="text-box">{esc(a["draft"]) or "(empty draft)"}</div>', unsafe_allow_html=True)
            st.markdown("**Reviewer feedback**")
            st.markdown(f'<div class="text-box">{esc(a["feedback"])}</div>', unsafe_allow_html=True)

    with st.expander("🧾 Activity log"):
        for line in result["log"]:
            st.markdown(f"- {esc(line)}")

else:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:3.5rem 2rem;text-align:center">
        <div style="font-size:4rem;margin-bottom:1rem">✍️</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:var(--text);margin-bottom:0.5rem">
            Ready to Write
        </div>
        <div style="color:var(--text-muted);font-size:0.85rem;max-width:460px;line-height:1.7">
            Enter a topic above and press <strong>Generate Post</strong>. The writer can search the web for fresh
            information, and the reviewer sends the draft back until it meets the checklist.
        </div>
        <div style="margin-top:2rem;display:flex;gap:1rem;flex-wrap:wrap;justify-content:center">
            <span class="badge badge-purple">Writer</span>
            <span class="badge badge-cyan">Web Search</span>
            <span class="badge badge-green">Reviewer</span>
        </div>
    </div>""", unsafe_allow_html=True)

# ─── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="dev-footer">Designed &amp; Developed by <span>Ajay Kumar</span>'
    + dev_links_html(compact=False)
    + '</div>',
    unsafe_allow_html=True,
)