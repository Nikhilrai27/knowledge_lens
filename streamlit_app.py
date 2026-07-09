import time
import queue
import threading
import uuid

import streamlit as st
from knowledge_lens.cli import run_task

st.set_page_config(page_title="Knowledge Lens", page_icon="🧠",
                   layout="wide", initial_sidebar_state="collapsed")

for k, v in {
    "generating": False, "current_task": "", "error": None,
    "provider": "groq",
    "current_pipeline_node": None, "execution_time": 0,
    "agent_statuses": {a: "idle" for a in
        ["Supervisor","Researcher","Analyst","Writer","Reviewer"]},
    "conversations": {}, "current_conv_id": None,
    "uploaded_files": [], "last_result": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def _cid():
    c = st.session_state.current_conv_id
    if c is None or c not in st.session_state.conversations:
        c = str(uuid.uuid4())
        st.session_state.conversations[c] = {"title": "New Chat", "messages": [], "created": time.time()}
        st.session_state.current_conv_id = c
    return c

def _msgs():
    return st.session_state.conversations[_cid()]["messages"]

# ═══════════════════════ CSS ═══════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; box-sizing: border-box; }
.stApp { background: #fff; color: #1a1a2e; }

/* top bar */
.bar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 999;
    background: #fff; border-bottom: 1px solid #f0f0f0;
    display: flex; align-items: center;
    justify-content: space-between; height: 48px;
    padding: 0 24px 0 18%;
}
.bar-l { display: flex; align-items: center; gap: 10px; }
.bar-logo { width: 26px; height: 26px; border-radius: 6px; background: #2563eb; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.bar-name { font-size: 14px; font-weight: 600; color: #111; }
.bar-sub { font-size: 11px; color: #888; display: none; }
.bar-r { display: flex; align-items: center; gap: 12px; font-size: 12px; color: #888; }
.bar-st { display: flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 500; color: #16a34a; }
.bar-st .d { width: 5px; height: 5px; border-radius: 50%; background: #22c55e; }

/* left sidebar */
.sb { padding: 56px 8px 16px; }
.sb-lbl { font-size: 10px; font-weight: 600; color: #bbb; text-transform: uppercase; letter-spacing: 0.4px; margin: 16px 0 6px; }
.sb-ch { display: flex; flex-direction: column; gap: 1px; }
.sb-ch .stButton > button {
    background: transparent !important; border: none !important; outline: none !important;
    justify-content: flex-start !important; padding: 6px 10px !important;
    font-size: 13px !important; color: #555 !important; font-weight: 400 !important;
    width: 100% !important; box-shadow: none !important;
}
.sb-ch .stButton > button:hover { background: #f5f5f5 !important; color: #111 !important; }
.sb-ch .stButton > button:focus { box-shadow: none !important; }
.sb-ch .stButton > button:active { background: #eff6ff !important; color: #2563eb !important; }
.sb-file { display: flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 6px; font-size: 12px; margin-bottom: 2px; color: #555; }
.sb-file .s { font-size: 10px; color: #bbb; margin-left: auto; }

/* right panel */
.rp { padding: 56px 8px 16px; }
.rp-h { font-size: 9px; font-weight: 600; color: #bbb; text-transform: uppercase; letter-spacing: 0.4px; margin: 16px 0 6px; }
.rp-ag .r { display: flex; align-items: center; justify-content: space-between; padding: 4px 0; font-size: 12px; color: #555; }
.rp-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.rp-dot.idle { background: #ddd; }
.rp-dot.run { background: #f59e0b; }
.rp-dot.done { background: #22c55e; }
.rp-pl .s { display: flex; align-items: center; gap: 6px; padding: 3px 6px; border-radius: 4px; font-size: 11px; color: #999; }
.rp-pl .s .i { width: 14px; text-align: center; font-size: 10px; }
.rp-pl .s.act { background: #eff6ff; color: #2563eb; font-weight: 600; }
.rp-pl .s.done { color: #16a34a; }
.rp-pl .a { text-align: center; font-size: 7px; color: #eee; line-height: 1; }
.rp-mg { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 4px; }
.rp-mc { text-align: center; padding: 6px 4px; }
.rp-mv { font-size: 16px; font-weight: 700; color: #2563eb; }
.rp-ml { font-size: 8px; font-weight: 500; color: #bbb; text-transform: uppercase; letter-spacing: 0.3px; }

/* chat */
.cht { padding: 56px 8px 0; min-height: calc(100vh - 140px); }
.cr { display: flex; margin-bottom: 24px; gap: 10px; }
.cr.u { flex-direction: row-reverse; }
.ca { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
.ca.u { background: #eff6ff; }
.cb { max-width: 80%; padding: 12px 16px; border-radius: 10px; font-size: 14px; line-height: 1.7; }
.cb.u { background: #2563eb; color: #fff; }
.cb.a { background: #f5f5f5; color: #1a1a2e; }
.cb .ts { font-size: 10px; color: #bbb; margin-top: 8px; }
.cb .sc { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: 500; margin-top: 6px; }

/* input form */
div[data-testid="stForm"] {
    border: 1px solid #e5e5e5 !important;
    border-radius: 10px !important;
    padding: 6px 8px !important;
    background: #fff !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
div[data-testid="stForm"]:focus-within {
    border-color: #2563eb !important;
}
div[data-testid="stForm"] [data-testid="stForm"] { border: none !important; padding: 0 !important; }
.in-btn { background: transparent !important; border: none !important; font-size: 16px !important; color: #999 !important; padding: 0 !important; min-width: 32px !important; height: 32px !important; border-radius: 8px !important; display: flex !important; align-items: center !important; justify-content: center !important; }
.in-btn:hover { background: #f5f5f5 !important; }
div[data-testid="stForm"] .stButton > button[kind="primary"] { background: #2563eb !important; color: #fff !important; width: 32px !important; height: 32px !important; min-width: 32px !important; border-radius: 8px !important; padding: 0 !important; font-size: 15px !important; }
div[data-testid="stForm"] .stButton > button[kind="primary"]:hover { background: #1d4ed8 !important; }
div[data-testid="stForm"] .stButton > button[kind="primary"]:disabled { background: #ddd !important; }
div[data-testid="stForm"] .stTextInput > div > div { border: none !important; background: transparent !important; box-shadow: none !important; padding: 0 !important; }
div[data-testid="stForm"] .stTextInput input { font-size: 14px !important; }
div[data-testid="stForm"] .st-emotion-cache-1inwz65 { display: none !important; }

/* empty state */
.em { text-align: center; padding: 120px 20px 40px; }
.em .i { font-size: 36px; }
.em .t1 { font-size: 18px; font-weight: 600; color: #111; margin: 12px 0 4px; }
.em .t2 { font-size: 14px; color: #888; }
.pc { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 20px; }
.pc span { padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 500; background: #f5f5f5; color: #555; cursor: pointer; }
.pc span:hover { background: #eee; color: #2563eb; }

/* pipeline animation */
.an { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: #eff6ff; border-radius: 8px; margin: 6px 0; }
.an .i { font-size: 14px; }
.an .nm { font-size: 11px; font-weight: 600; color: #2563eb; }
.an .ds { font-size: 10px; color: #6b7280; }
.stProgress > div > div > div { background: #2563eb !important; height: 3px !important; }
.stProgress > div > div { background: #e5e7eb !important; }

/* overrides */
.block-container { padding: 0 !important; max-width: 100% !important; }
div[data-testid="stDecoration"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stAppHeader { display: none !important; }
section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════ COMPONENTS ═══════════════════════

def top_bar():
    st.markdown("""
    <div class="bar">
        <div class="bar-l">
            <div class="bar-logo">🧠</div>
            <span class="bar-name">Knowledge Lens</span>
            <span class="bar-sub">AI Research Assistant</span>
        </div>
        <div class="bar-r">
            <div class="bar-st"><span class="d"></span> Connected</div>
            <span>⚙️</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def left_sidebar():
    conv = st.session_state.conversations
    cur = st.session_state.current_conv_id
    st.markdown('<div class="sb">', unsafe_allow_html=True)

    if st.button("+ New Chat", use_container_width=True, key="nc"):
        cid = str(uuid.uuid4())
        conv[cid] = {"title": "New Chat", "messages": [], "created": time.time()}
        st.session_state.current_conv_id = cid
        st.session_state.generating = False
        st.rerun()

    st.markdown('<div class="sb-lbl">Upload</div>', unsafe_allow_html=True)
    with st.popover("📎 Upload PDF", use_container_width=True):
        up = st.file_uploader("", type=["pdf"], label_visibility="collapsed", key="sb_pdf")
        if up and not any(f["name"] == up.name for f in st.session_state.uploaded_files):
            st.session_state.uploaded_files.append(
                {"name": up.name, "size": f"{len(up.getvalue())/1024:.0f}KB",
                 "id": str(uuid.uuid4())[:8]})
            st.rerun()
    for f in st.session_state.uploaded_files:
        st.markdown(f'<div class="sb-file">📄<span>{f["name"]}</span><span class="s">{f["size"]}</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-lbl">Conversations</div><div class="sb-ch">', unsafe_allow_html=True)
    for cid, c in sorted(conv.items(), key=lambda x: x[1].get("created", 0), reverse=True)[:15]:
        lbl = c["title"][:35]
        if st.button(f"💬 {lbl}", key=f"c_{cid[:8]}", use_container_width=True):
            st.session_state.current_conv_id = cid
            st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

def right_panel():
    st.markdown('<div class="rp">', unsafe_allow_html=True)

    st.markdown('<div class="rp-h">Agents</div><div class="rp-ag">', unsafe_allow_html=True)
    icons = {"idle":"○","running":"●","completed":"✓","error":"✗"}
    classes = {"idle":"idle","running":"run","completed":"done","error":"err"}
    for agent in ["Supervisor","Researcher","Analyst","Writer","Reviewer"]:
        s = st.session_state.agent_statuses.get(agent, "idle")
        ic = icons.get(s, "○")
        cls = classes.get(s, "idle")
        st.markdown(f'<div class="r"><span>{ic} {agent}</span><span class="rp-dot {cls}"></span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="rp-h">Pipeline</div><div class="rp-pl">', unsafe_allow_html=True)
    steps = [("📄","Upload"),("📝","Extract"),("🔪","Chunk"),("🧮","Embed"),
             ("💾","Store"),("🔍","Retrieve"),("🧠","Supervisor"),("🔬","Research"),
             ("📊","Analyze"),("✍️","Write"),("⭐","Review"),("✅","Answer")]
    am = {"Supervisor":"Supervisor","Research":"Research","Analyze":"Analyze",
          "Write":"Write","Review":"Review"}
    hl = am.get(st.session_state.current_pipeline_node) if st.session_state.current_pipeline_node else None
    hi = None
    for i, (_, l) in enumerate(steps):
        if l == hl: hi = i; break
    for i, (ic, l) in enumerate(steps):
        cls = ""
        if l == hl: cls = "act"
        elif hi is not None and i < hi: cls = "done"
        st.markdown(f'<div class="s {cls}"><span class="i">{ic}</span><span>{l}</span></div>', unsafe_allow_html=True)
        if i < len(steps)-1:
            st.markdown('<div class="a">▾</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="rp-h">Metrics</div><div class="rp-mg">', unsafe_allow_html=True)
    r = getattr(st.session_state, "last_result", None)
    et = f"{st.session_state.execution_time:.1f}s" if st.session_state.execution_time else "--"
    nc = str(r.get("retrieved_chunks","--")) if r and isinstance(r, dict) and "error" not in r else "--"
    tc = str(r.get("tool_calls","--")) if r and isinstance(r, dict) and "error" not in r else "--"
    nd = str(len(st.session_state.uploaded_files))
    for v, l in [(et,"Response"),(nc,"Chunks"),(nd,"Docs"),(tc,"Tools")]:
        st.markdown(f'<div class="rp-mc"><div class="rp-mv">{v}</div><div class="rp-ml">{l}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def chat():
    msgs = _msgs()
    has = bool(msgs) or st.session_state.generating

    # empty state
    if not has:
        st.markdown('<div class="em"><div class="i">🧠</div><div class="t1">Knowledge Lens</div><div class="t2">Ask questions about your documents.</div><div class="pc"><span>Explain transformers</span><span>Compare LSTMs vs GRUs</span><span>Summarize attention</span></div></div>', unsafe_allow_html=True)
    else:
        # messages
        st.markdown('<div class="cht">', unsafe_allow_html=True)
        for m in msgs:
            r, u = m["role"], "u" if m["role"] == "user" else "a"
            em = "👤" if r == "user" else "🧠"
            ts = time.strftime("%I:%M %p", time.localtime(m.get("ts", 0))) if m.get("ts") else ""
            st.markdown(f'<div class="cr {u}"><div class="ca {u}">{em}</div><div class="cb {u}">', unsafe_allow_html=True)
            st.markdown(m["content"])
            st.markdown(f'<div class="ts">{ts}</div>', unsafe_allow_html=True)
            sc = m.get("score")
            if r == "assistant" and sc is not None:
                c = "#16a34a" if sc >= 7 else "#d97706"
                bg = "#f0fdf4" if sc >= 7 else "#fffbeb"
                st.markdown(f'<span class="sc" style="background:{bg};color:{c}">Score: {sc}/10</span>', unsafe_allow_html=True)
                fb = m.get("feedback")
                if fb:
                    st.markdown(f'<div style="font-size:10px;color:#888;margin-top:4px;padding:6px 8px;border-radius:6px;background:#fafafa;">{fb}</div>', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

        # generation
        if st.session_state.generating:
            st.markdown('<div class="cr a"><div class="ca a">🧠</div><div class="cb a">', unsafe_allow_html=True)
            result = _execute(st.session_state.current_task)
            if result:
                if "error" in result:
                    st.markdown(f"❌ {result['error']}")
                    msgs.append({"role":"assistant","content":f"❌ {result['error']}","ts":time.time(),"score":0,"feedback":""})
                else:
                    doc = result.get("document","")
                    score = result.get("review_score",0)
                    fb = result.get("review_feedback","")
                    st.markdown(doc)
                    msgs.append({"role":"assistant","content":doc,"ts":time.time(),"score":score,"feedback":fb})
            st.markdown('</div></div>', unsafe_allow_html=True)
            st.session_state.generating = False
            st.rerun()
            st.stop()
        st.markdown('</div>', unsafe_allow_html=True)

    # input form
    if not st.session_state.generating:
        with st.form("chat_form", border=False):
            ci, cii, cs = st.columns([0.06, 0.86, 0.08], gap="small")
            with ci:
                with st.popover("📎", use_container_width=False):
                    up = st.file_uploader("", type=["pdf"], label_visibility="collapsed", key="in_pdf")
                    if up and not any(f["name"] == up.name for f in st.session_state.uploaded_files):
                        st.session_state.uploaded_files.append(
                            {"name": up.name, "size": f"{len(up.getvalue())/1024:.0f}KB",
                             "id": str(uuid.uuid4())[:8]})
                        st.rerun()
            with cii:
                prompt = st.text_input("", placeholder="Ask anything…", label_visibility="collapsed", key="ci")
            with cs:
                sp = bool(prompt and prompt.strip())
                send = st.form_submit_button("➤", type="primary", use_container_width=False, disabled=not sp)
        if send:
            t = prompt.strip()
            msgs.append({"role": "user", "content": t, "ts": time.time()})
            st.session_state.current_task = t
            st.session_state.conversations[st.session_state.current_conv_id]["title"] = t[:45]
            st.session_state.generating = True
            if "ci" in st.session_state: del st.session_state["ci"]
            st.rerun()

# ═══════════════════════ EXECUTION ═══════════════════════

def _execute(task: str) -> dict:
    st.session_state.error = None
    ps = st.empty()
    ss = st.empty()
    stages = [
        ("Supervisor","🧠","Decomposing task…"),
        ("Researcher","🔍","Searching web…"),
        ("Analyst","📊","Extracting insights…"),
        ("Writer","✍️","Generating document…"),
        ("Reviewer","⭐","Evaluating quality…"),
    ]
    q: queue.Queue = queue.Queue()
    def _w():
        try:
            q.put(run_task(task, provider=st.session_state.provider, human_gate=False))
        except Exception as e:
            q.put({"error": str(e)})
    t = threading.Thread(target=_w, daemon=True)
    start = time.time()
    t.start()
    for i, (agent, ic, desc) in enumerate(stages):
        for a in st.session_state.agent_statuses:
            st.session_state.agent_statuses[a] = "idle"
        st.session_state.agent_statuses[agent] = "running"
        st.session_state.current_pipeline_node = agent
        pct = (i + 1) / len(stages)
        with ps.container(): st.progress(pct)
        with ss.container():
            st.markdown(f'<div class="an"><span class="i">{ic}</span><div><div class="nm">{agent}</div><div class="ds">{desc}</div></div></div>', unsafe_allow_html=True)
        if i < len(stages)-1: time.sleep(0.4)
    t.join(timeout=180)
    st.session_state.execution_time = time.time() - start
    with ps.container(): st.progress(1.0)
    if t.is_alive(): return {"error":"Timed out after 3 minutes."}
    try: result = q.get_nowait()
    except: return {"error":"Failed to retrieve result."}
    if isinstance(result, dict) and "error" in result: return result
    for a in st.session_state.agent_statuses: st.session_state.agent_statuses[a] = "done"
    st.session_state.last_result = result
    return result

# ═══════════════════════ MAIN ═══════════════════════

top_bar()
l, c, r = st.columns([0.18, 0.62, 0.20], gap="small")
with l: left_sidebar()
with c: chat()
with r: right_panel()
