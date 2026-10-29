"""
app.py
======
PulseGrid AI - Autonomous Competitive Intelligence Agent & Threat Scanner
Nebius x NVIDIA Global AI Hackathon
Streamlit Web Application featuring Multi-Stream Live Search, Adversarial Verification,
Source Provenance Classification, and Executive Threat Dossier.
"""

import html
import re
import streamlit as st

from config import simulation_enabled, NEBIUS_MODEL, redact
from search_engine import (
    run_pulsegrid_search,
    PulseGridError,
    supabase_client,
    tavily_client,
)
from ai_engine import (
    synthesize_threat_dossier,
    dossier_to_markdown,
    nebius_client,
)

# ==============================================================================
# 1. Page Configuration & Executive Dark Theme
# ==============================================================================
st.set_page_config(
    page_title="PulseGrid AI — Competitive Threat Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Tech Cyber Intelligence Dark Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }

    /* Main Container */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }

    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 2rem 2.2rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .main-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        line-height: 1.5;
    }

    /* Glass Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    /* Provenance Badges */
    .badge-primary {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    .badge-secondary {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    .badge-community {
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.3);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Delta Signal Item */
    .delta-item {
        background: rgba(15, 23, 42, 0.85);
        border-left: 4px solid #38bdf8;
        border-radius: 4px 8px 8px 4px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.75rem;
        color: #f1f5f9;
        font-size: 0.95rem;
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.05rem;
        padding: 0.65rem 1.5rem;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        transition: all 0.2s ease-in-out;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        transform: translateY(-1px);
    }

    .sim-banner {
        background: #dc2626; color: #fff; font-weight: 800; font-size: 1.6rem;
        text-align: center; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;
        letter-spacing: 0.05em;
    }
    .live-box {
        background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.35);
        border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 1rem; font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

SIMULATED = simulation_enabled()
if SIMULATED:
    st.markdown('<div class="sim-banner">SIMULATED DATA — NOT LIVE</div>', unsafe_allow_html=True)


# ==============================================================================
# 2. Sidebar: System Health & Integrations
# ==============================================================================
with st.sidebar:
    st.markdown("## ⚡ PulseGrid AI")
    st.caption("Autonomous Competitive Intelligence Engine")
    st.markdown("---")

    st.markdown("### 🔌 System Health & Integrations")

    if SIMULATED:
        st.error("DEMO_SIMULATION=true — all data is simulated.")
    if tavily_client is not None:
        st.markdown("🟢 **Tavily Search API**: `Configured`")
    else:
        st.markdown("🔴 **Tavily Search API**: `Not configured`")
    if nebius_client is not None:
        st.markdown(f"🟢 **Nebius Token Factory**: `Configured`  \nModel: `{NEBIUS_MODEL}`")
    else:
        st.markdown("🔴 **Nebius Token Factory**: `Not configured`")
    if supabase_client is not None:
        st.markdown("🟢 **Supabase**: `Configured` (snapshot diffing)")
    else:
        st.markdown("⚪ **Supabase**: `Not configured` (local JSON snapshot)")

    st.markdown("---")
    st.markdown("### 🛠️ Architecture Specs")
    st.markdown("""
    - **Reasoning Model**: NVIDIA Nemotron (via Nebius)
    - **Inference Gateway**: Nebius Token Factory
    - **Data Streams**: Tavily Multi-Stream Parallel RAG
    - **State**: Supabase / local snapshot diffing
    - **Verification**: Adversarial "Prove Me Wrong" search
    """)

    st.markdown("---")
    st.caption("PulseGrid AI • Nebius x NVIDIA Hackathon 2026")


# ==============================================================================
# 3. Main Search Interface
# ==============================================================================
st.markdown("""
<div class="main-header">
    <div class="main-title">⚡ PulseGrid AI: Autonomous Threat Scanner</div>
    <div class="main-subtitle">
        Scan live web streams across <b>Talent & Hiring</b>, <b>Product & Pricing</b>, <b>Customer Friction</b>, 
        and <b>Market News</b>, then challenge its own hypothesis with an <b>adversarial &quot;prove me wrong&quot; search</b>.
    </div>
</div>
""", unsafe_allow_html=True)

# Target Competitor Input
col1, col2 = st.columns([3, 1])

with col1:
    company_input = st.text_input(
        "Target Company / Competitor",
        value="",
        placeholder="e.g. OpenAI, Anthropic, Databricks, Mistral AI, Cohere, Scale AI",
        help="Enter the company name to scan multi-stream market baselines."
    )

with col2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    launch_btn = st.button("🚀 Launch Investigation", use_container_width=True)

# Session State Persistence
if "search_data" not in st.session_state:
    st.session_state.search_data = None
if "dossier_content" not in st.session_state:
    st.session_state.dossier_content = None
if "run_error" not in st.session_state:
    st.session_state.run_error = None
if "active_company" not in st.session_state:
    st.session_state.active_company = ""


# ==============================================================================
# 4. Investigation run (real calls; failures are shown, never faked)
# ==============================================================================
def esc(x) -> str:
    return html.escape(str(x or ""), quote=True)


def safe_href(url: str) -> str:
    return esc(url) if str(url).startswith(("http://", "https://")) else "#"


MAX_RUNS_PER_SESSION = 5
COMPANY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&'\-]{0,59}$")
if "run_count" not in st.session_state:
    st.session_state.run_count = 0

if launch_btn and company_input.strip():
    target_company = company_input.strip()
    if not COMPANY_RE.match(target_company):
        st.error("Company name: 1-60 characters; letters, numbers, spaces and . , & ' - only.")
        st.stop()
    if st.session_state.run_count >= MAX_RUNS_PER_SESSION and not SIMULATED:
        st.error(f"Limit reached: {MAX_RUNS_PER_SESSION} investigations per session. Reload the page to start a new session.")
        st.stop()
    st.session_state.run_count += 1
    st.session_state.active_company = target_company
    st.session_state.search_data = None
    st.session_state.dossier_content = None
    st.session_state.run_error = None

    with st.status(f"⚡ Investigating '{target_company}'...", expanded=True) as status:
        try:
            st.write("📡 **Step 1/3**: Scanning 4 parallel Tavily streams (talent, product, friction, market)...")
            search_data = run_pulsegrid_search(target_company)
            st.session_state.search_data = search_data

            st.write("🔍 **Step 2/3**: Comparing with previous snapshot...")
            for h in search_data["delta_highlights"][:1]:
                st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;↳ {h}")

            st.write("🧠 **Step 3/3**: Nemotron hypothesis → adversarial Tavily search → evidence classification → scoring...")
            analysis = synthesize_threat_dossier(target_company, search_data)
            st.session_state.dossier_content = analysis
            status.update(label=f"✅ Investigation complete for {target_company}", state="complete", expanded=False)
        except PulseGridError as e:
            st.session_state.run_error = redact(e)
            status.update(label="❌ Investigation failed", state="error", expanded=True)
        except Exception as e:  # unexpected - still show the real message
            st.session_state.run_error = f"{type(e).__name__}: {redact(e)}"
            status.update(label="❌ Investigation failed", state="error", expanded=True)

if st.session_state.get("run_error"):
    st.error(f"Live API call failed — no data was faked.\n\n{st.session_state.run_error}")


# ==============================================================================
# 5. Results
# ==============================================================================
def render_evidence(items):
    if not items:
        st.caption("None found.")
    for e in items:
        st.markdown(
            f"- **{esc(e['source_type'])}** · {esc(e['claim'])} — "
            f"[{esc(e['title'])}]({e['url']})  \n  <sub>{esc(e['domain'])}</sub>",
            unsafe_allow_html=True,
        )


if st.session_state.dossier_content and st.session_state.search_data:
    company_name = st.session_state.active_company
    search_data = st.session_state.search_data
    d = st.session_state.dossier_content
    conf = d["confidence"]
    meta = d["meta"]

    # Live mode indicator
    if d.get("simulated"):
        st.markdown('<div class="sim-banner">SIMULATED DATA — NOT LIVE</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='live-box'>🟢 <b>LIVE MODE</b> · Model: <code>{esc(meta['model'])}</code> via Nebius Token Factory · "
            f"Tavily: ✅ {search_data['tavily_calls_ok']}/4 streams + ✅ {meta['tavily_adversarial_ok']} adversarial queries · "
            f"Nebius: ✅ {meta['nebius_calls_ok']} calls succeeded · Snapshot store: {esc(search_data['storage_backend'])}</div>",
            unsafe_allow_html=True,
        )
    for w in search_data.get("storage_warnings", []):
        st.warning(w)

    tab1, tab2, tab3 = st.tabs(["⚡ Threat Dossier", "🔍 Changes Since Last Scan", "🌐 Evidence Ledger (Raw Streams)"])

    with tab1:
        col_header, col_download = st.columns([3, 1])
        with col_header:
            st.markdown(f"### 🛡️ Threat Intelligence Dossier: `{company_name}`")
        with col_download:
            st.download_button(
                "📥 Download (.md)", data=dossier_to_markdown(d, search_data["delta_highlights"]),
                file_name=f"{company_name.lower().replace(' ', '_')}_pulsegrid_dossier.md",
                mime="text/markdown", use_container_width=True,
            )
        st.markdown("---")
        st.markdown("#### Executive summary")
        st.write(d["executive_summary"])

        st.markdown("#### 🧠 HYPOTHESIS — NOT FACT")
        st.info(d["hypothesis"])

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### 🟢 Supporting evidence ({len(d['supporting'])})")
            render_evidence(d["supporting"])
        with c2:
            st.markdown(f"#### 🔴 Contradicting evidence ({len(d['contradicting'])})")
            if d["adversarial_queries"]:
                st.caption("Queries run to disprove it: " + " | ".join(d["adversarial_queries"]))
            render_evidence(d["contradicting"])
            if d.get("alternative_explanation"):
                st.markdown(f"**Alternative explanation:** {d['alternative_explanation']}")

        st.markdown(f"#### 📊 Confidence: {conf['score']}% ({conf['label']})")
        st.caption("Computed in Python from the evidence above — not generated by the model.")
        st.progress(min(int(conf["score"]), 100))
        st.table([
            {"Factor": b["label"], "Weight": f"{int(b['weight'] * 100)}%", "Value (0-1)": b["value"],
             "Points": b["points"], "Basis": b["note"]}
            for b in conf["breakdown"]
        ])
        for cap in conf["caps"]:
            st.warning(cap)
        st.markdown("**Why not higher?** (model-written explanation)")
        st.write(d["why_not_higher"])

        st.markdown("#### 🚀 Recommendations")
        for i, r in enumerate(d["recommendations"], 1):
            st.markdown(f"{i}. {r}")

    with tab2:
        st.markdown("### 🔍 Changes Since Last Scan")
        diff = search_data["diff"]
        if diff["first_scan"]:
            st.info("First scan — baseline saved. Rescan later to see what changed. (No changes are claimed.)")
        else:
            st.caption("Sources that appeared since the previous saved snapshot (matched by URL).")
            for n in diff["new_signals"]:
                st.markdown(
                    f"<div class='delta-item'>⚡ [{esc(n['category'])}] "
                    f"<a href='{safe_href(n['url'])}' target='_blank' style='color:#38bdf8'>{esc(n['title'])}</a> ({esc(n['provenance'])})</div>",
                    unsafe_allow_html=True,
                )
            if not diff["new_signals"]:
                st.info("No new sources since the previous scan.")
            st.caption(f"{diff['gone_count']} previously seen source(s) no longer appeared.")

    with tab3:
        st.markdown("### 🌐 Evidence Ledger across 4 Parallel Streams")
        st.caption("Raw results retrieved via Tavily with source provenance classification.")
        for stream in search_data["raw_streams"]:
            results = stream.get("results", [])
            with st.expander(f"📁 {stream.get('category', 'Stream')} ({len(results)} items)", expanded=False):
                if not results:
                    st.caption("No signals retrieved for this category.")
                for idx, item in enumerate(results, 1):
                    prov = item.get("provenance", "Secondary")
                    badge = {"Primary": "badge-primary", "Community": "badge-community"}.get(prov, "badge-secondary")
                    url = item.get("url", "")
                    st.markdown(f"""
                    <div class="glass-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                            <span style="font-weight:600;color:#f1f5f9;">{idx}. {esc(item.get('title'))}</span>
                            <span class="{badge}">{esc(prov)}</span>
                        </div>
                        <div style="color:#94a3b8;font-size:0.9rem;line-height:1.5;margin-bottom:8px;">{esc((item.get('snippet') or '')[:500])}</div>
                        <a href="{safe_href(url)}" target="_blank" style="color:#38bdf8;font-size:0.85rem;">🔗 {esc(url)}</a>
                    </div>
                    """, unsafe_allow_html=True)

elif not launch_btn and not st.session_state.get("run_error"):
    st.markdown("""
    <div style="text-align: center; padding: 4rem 1rem; color: #64748b;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
        <div style="font-size: 1.25rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.5rem;">Ready to Investigate</div>
        <div>Enter a target competitor above and click <b>Launch Investigation</b>.</div>
    </div>
    """, unsafe_allow_html=True)
