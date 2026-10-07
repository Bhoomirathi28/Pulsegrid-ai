"""
app.py
======
PulseGrid AI - Autonomous Competitive Intelligence Agent & Threat Scanner
Nebius x NVIDIA Global AI Hackathon
Streamlit Web Application featuring Multi-Stream Live Search, Adversarial Verification,
Trust Layer™ Confidence Matrix, and Executive Threat Dossier.
"""

import os
import time
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# Load engines
from search_engine import (
    run_pulsegrid_search,
    TAVILY_API_KEY,
    SUPABASE_URL,
    SUPABASE_KEY,
    _is_placeholder_key,
    supabase_client,
    tavily_client
)
from ai_engine import (
    synthesize_threat_dossier,
    NEBIUS_API_KEY,
    DEFAULT_MODEL,
    openai_client
)

load_dotenv()

# ==============================================================================
# Page Configuration & Modern Dark Cyber Theme
# ==============================================================================
st.set_page_config(
    page_title="PulseGrid AI — Autonomous Threat Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Tech Cyber Intelligence CSS styling
st.markdown("""
<style>
    /* Dark Obsidian & NVIDIA Green Theme */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* Top Header Aesthetics */
    .pulsegrid-hero {
        background: linear-gradient(135deg, rgba(16, 24, 40, 0.9) 0%, rgba(11, 15, 25, 0.95) 100%);
        border: 1px solid rgba(118, 185, 0, 0.3);
        box-shadow: 0 8px 32px 0 rgba(0, 255, 136, 0.08);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .pulsegrid-title {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #76b900 0%, #00ff88 50%, #00e5ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .pulsegrid-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 400;
        margin-bottom: 0px;
    }
    
    /* Highlight Cards */
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        border-color: #76b900;
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #76b900;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Hypothesis Callout Banner */
    .hypothesis-card {
        background: rgba(17, 24, 39, 0.85);
        border-left: 4px solid #76b900;
        border-radius: 8px;
        padding: 18px;
        margin: 16px 0;
        border-top: 1px solid #1f2937;
        border-right: 1px solid #1f2937;
        border-bottom: 1px solid #1f2937;
    }
    
    /* Status Pills */
    .pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .pill-green { background: rgba(118, 185, 0, 0.15); color: #76b900; border: 1px solid rgba(118, 185, 0, 0.4); }
    .pill-cyan { background: rgba(0, 229, 255, 0.15); color: #00e5ff; border: 1px solid rgba(0, 229, 255, 0.4); }
    .pill-amber { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); }
    .pill-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }
    
    /* Evidence Items */
    .evidence-item {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .evidence-item a {
        color: #00e5ff;
        text-decoration: none;
        font-weight: 600;
    }
    .evidence-item a:hover {
        text-decoration: underline;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #111827;
        border-radius: 6px 6px 0 0;
        color: #94a3b8;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #76b900 !important;
        border-bottom: 2px solid #76b900 !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# Session State Initialization
# ==============================================================================
if "active_scan_results" not in st.session_state:
    st.session_state["active_scan_results"] = None
if "active_dossier" not in st.session_state:
    st.session_state["active_dossier"] = None
if "watch_list" not in st.session_state:
    st.session_state["watch_list"] = ["Cursor", "Perplexity"]


# ==============================================================================
# Sidebar: System Health, Configuration & Model Settings
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚡ PULSEGRID AI")
    st.caption("Nebius x NVIDIA AI Hackathon Edition")
    st.markdown("---")

    # API Status Indicators
    st.markdown("#### 🔌 Integration Status")

    # 1. Tavily
    tavily_ok = not _is_placeholder_key(TAVILY_API_KEY)
    if tavily_ok:
        st.markdown("🟢 **Tavily Search API:** `Active`")
    else:
        st.markdown("🔴 **Tavily Search API:** `Missing Key (Mock Mode)`")

    # 2. Nebius Token Factory (NVIDIA Nemotron 3)
    nebius_ok = not _is_placeholder_key(NEBIUS_API_KEY)
    if nebius_ok:
        st.markdown("🟢 **Nebius Token Factory:** `Active`")
    else:
        st.markdown("🔴 **Nebius Token Factory:** `Missing Key (Local Sim)`")

    # 3. Supabase Cache
    supabase_ok = not _is_placeholder_key(SUPABASE_URL) and not _is_placeholder_key(SUPABASE_KEY) and (supabase_client is not None)
    if supabase_ok:
        st.markdown("🟢 **Supabase Cache:** `Connected`")
    else:
        st.markdown("🟡 **Supabase Cache:** `Local JSON Cache`")

    st.markdown("---")

    # Model Tier Selection
    st.markdown("#### 🧠 Model Selection")
    selected_model = st.selectbox(
        "Nemotron Model Tier",
        options=[
            "nvidia/nemotron-3-super-120b",
            "nvidia/nemotron-3-ultra-550b",
            "nvidia/nemotron-3.5-lightning",
            "nvidia/nemotron-3-nano-30b"
        ],
        index=0,
        help="Powered by NVIDIA Nemotron open models hosted on Nebius Token Factory."
    )

    # Scan Controls
    st.markdown("#### ⚙️ Scan Controls")
    force_refresh = st.checkbox(
        "🔄 Force Fresh Live Scan",
        value=False,
        help="Bypasses Supabase snapshot cache to trigger live crawl and change detection."
    )

    st.markdown("---")

    # Monitored Targets in Watch Mode
    st.markdown("#### 👁️ Active Watch Mode Targets")
    for company in st.session_state["watch_list"]:
        st.markdown(f"- 📡 **{company}** `(Monitoring 72h)`")

    st.markdown("---")
    st.caption("PulseGrid Trust Layer™ enforces adversarial verification before generating any strategic recommendation.")


# ==============================================================================
# Main UI Header
# ==============================================================================
st.markdown("""
<div class="pulsegrid-hero">
    <div class="pulsegrid-title">⚡ PULSEGRID AI</div>
    <div class="pulsegrid-subtitle">
        The Autonomous Competitive Intelligence Agent That Has to <strong>Prove Its Own Conclusions</strong>.
    </div>
    <p style="color: #64748b; font-size: 0.9rem; margin-top: 6px; margin-bottom: 0px;">
        Investigate ➔ Detect ➔ Correlate ➔ Hypothesize ➔ <strong>Attack ("Prove Me Wrong")</strong> ➔ Verify ➔ Decide ➔ Watch
    </p>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# Search & Investigation Input Bar
# ==============================================================================
st.markdown("##### 🎯 Enter Target Competitor to Investigate")
col_input, col_btn = st.columns([4, 1.2])

with col_input:
    target_company = st.text_input(
        "Target Company",
        placeholder="e.g. Cursor, Databricks, Perplexity, Cognition, Anthropic",
        label_visibility="collapsed"
    )

with col_btn:
    launch_btn = st.button("🚀 Launch Investigation", use_container_width=True, type="primary")

# Preset Quick Selector
st.markdown("<p style='font-size: 0.82rem; color: #64748b; margin-top: -6px;'>Quick presets: </p>", unsafe_allow_html=True)
preset_cols = st.columns([1, 1, 1, 1, 3])
if preset_cols[0].button("Cursor", use_container_width=True):
    target_company = "Cursor"
    launch_btn = True
if preset_cols[1].button("Databricks", use_container_width=True):
    target_company = "Databricks"
    launch_btn = True
if preset_cols[2].button("Perplexity", use_container_width=True):
    target_company = "Perplexity"
    launch_btn = True
if preset_cols[3].button("Cognition", use_container_width=True):
    target_company = "Cognition"
    launch_btn = True


# ==============================================================================
# Investigation Execution Pipeline
# ==============================================================================
if launch_btn:
    if not target_company.strip():
        st.warning("Please specify a target company name.")
    else:
        company_clean = target_company.strip()
        st.markdown("---")

        # Interactive Step-by-Step Status Box
        with st.status(f"🔎 Investigating {company_clean} across live web and adversarial audit...", expanded=True) as status_box:
            st.write("✓ Establishing baseline and querying snapshot cache...")
            time.sleep(0.3)

            st.write("✓ Scanning 4 parallel Tavily intelligence streams (Talent, Product, Friction, Market)...")
            scan_results = run_pulsegrid_search(company_clean, force_refresh=force_refresh)
            st.session_state["active_scan_results"] = scan_results

            cache_note = " (Retrieved from Supabase cache)" if scan_results.get("is_cached") else " (Fresh live crawl)"
            st.write(f"✓ Retrieved {len(scan_results.get('normalized_evidence', []))} intelligence signals{cache_note}.")
            time.sleep(0.2)

            st.write("✓ Normalizing source provenance and executing Change Engine diff...")
            time.sleep(0.2)

            st.write(f"✓ Correlating signals and synthesizing hypothesis via NVIDIA Nemotron 3 ({selected_model})...")
            
            # Synthesize Dossier with progress updates
            def update_status_cb(msg: str):
                st.write(f"→ {msg}")

            dossier_data = synthesize_threat_dossier(
                company_name=company_clean,
                raw_streams=scan_results.get("raw_streams", []),
                change_signals=scan_results.get("change_signals"),
                extracted_pages=scan_results.get("extracted_pages"),
                model=selected_model,
                status_callback=update_status_cb
            )
            st.session_state["active_dossier"] = dossier_data

            status_box.update(
                label=f"✅ Intelligence Investigation Complete: {company_clean} (Confidence: {dossier_data.get('confidence_score')}%)",
                state="complete",
                expanded=False
            )


# ==============================================================================
# Results Presentation View
# ==============================================================================
if st.session_state.get("active_dossier") and st.session_state.get("active_scan_results"):
    dossier = st.session_state["active_dossier"]
    scan = st.session_state["active_scan_results"]

    company_name = dossier.get("company_name", "Target")
    conf_score = dossier.get("confidence_score", 75)
    threat_level = dossier.get("threat_level", "HIGH")
    verdict = dossier.get("verdict", "PLAUSIBLE — REQUIRES MONITORING")
    hypothesis = dossier.get("hypothesis", "")
    matrix = dossier.get("confidence_matrix", {})
    why_not = dossier.get("why_not_higher", "")

    # Top Metric Highlight Grid
    st.markdown("### 📊 Verified Intelligence Summary")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{conf_score}%</div>
            <div class="metric-label">Calibrated Confidence</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col2:
        badge_class = "pill-red" if threat_level in ["CRITICAL", "HIGH"] else "pill-amber"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {'#ef4444' if threat_level in ['CRITICAL', 'HIGH'] else '#f59e0b'};">{threat_level}</div>
            <div class="metric-label">Competitive Threat Level</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #00e5ff;">{len(scan.get('normalized_evidence', []))}</div>
            <div class="metric-label">Live Signals Indexed</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #00ff88;">{len(dossier.get('supporting_summary', []))} / {len(dossier.get('contradicting_summary', []))}</div>
            <div class="metric-label">Support vs Counter Signals</div>
        </div>
        """, unsafe_allow_html=True)

    # Hypothesis Highlight Banner
    st.markdown(f"""
    <div class="hypothesis-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="pill pill-cyan">Strategic Hypothesis (Unproven)</span>
            <span class="pill pill-green">{verdict}</span>
        </div>
        <div style="font-size: 1.25rem; font-weight: 700; color: #f8fafc;">
            "{hypothesis}"
        </div>
        <div style="margin-top: 10px; font-size: 0.88rem; color: #cbd5e1;">
            <strong>Cross-Signal Correlation:</strong> {dossier.get('correlation_rationale', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Add to Watch List Action
    c_watch, c_space = st.columns([1.5, 4])
    with c_watch:
        if company_name not in st.session_state["watch_list"]:
            if st.button(f"👁️ Watch {company_name} (Enable Persistent Diffing)", use_container_width=True):
                st.session_state["watch_list"].append(company_name)
                st.success(f"Added {company_name} to active 72-hour Watch Mode!")

    # Tabs for In-Depth Analysis
    tab_dossier, tab_adversarial, tab_streams, tab_change = st.tabs([
        "⚡ Executive Threat Dossier",
        "🛡️ Adversarial Verification & Trust Layer™",
        "📡 4 Live Tavily Streams",
        "🔄 Baseline & Change Engine"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: EXECUTIVE THREAT DOSSIER
    # --------------------------------------------------------------------------
    with tab_dossier:
        st.markdown("### 📄 Full Threat Dossier")
        st.markdown(dossier.get("dossier_markdown", ""))

        st.markdown("---")
        # Download Markdown Report
        st.download_button(
            label="📥 Download Executive Threat Dossier (.md)",
            data=dossier.get("dossier_markdown", ""),
            file_name=f"{company_name.lower()}_pulsegrid_dossier.md",
            mime="text/markdown",
            use_container_width=False
        )

    # --------------------------------------------------------------------------
    # TAB 2: ADVERSARIAL VERIFICATION & TRUST LAYER
    # --------------------------------------------------------------------------
    with tab_adversarial:
        st.markdown("### 🛡️ Adversarial 'Prove Me Wrong' Audit")
        st.caption("PulseGrid does not trust its first answer. It executes targeted adversarial sweeps to challenge and attempt to falsify its own hypothesis.")

        adv_col1, adv_col2 = st.columns(2)

        with adv_col1:
            st.markdown("#### 🟢 Supporting Evidence")
            for item in dossier.get("supporting_summary", []):
                st.markdown(f"""
                <div class="evidence-item" style="border-left: 3px solid #76b900;">
                    <div style="color: #76b900; font-weight: 600; font-size: 0.9rem;">CONFIRMATORY SIGNAL</div>
                    <div style="color: #f1f5f9; margin-top: 4px;">{item}</div>
                </div>
                """, unsafe_allow_html=True)

        with adv_col2:
            st.markdown("#### 🔴 Contradicting Evidence ('Prove Me Wrong')")
            for item in dossier.get("contradicting_summary", []):
                st.markdown(f"""
                <div class="evidence-item" style="border-left: 3px solid #ef4444;">
                    <div style="color: #ef4444; font-weight: 600; font-size: 0.9rem;">DISCONFIRMING / COUNTER SIGNAL</div>
                    <div style="color: #f1f5f9; margin-top: 4px;">{item}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 📊 PulseGrid Trust Layer™ Confidence Matrix")
        
        # Display 6-factor Confidence Breakdown in structured progress bars
        dim_cols = st.columns(3)
        dims = [
            ("Evidence Strength", matrix.get("evidence_strength", 80), "Volume & depth of primary sources"),
            ("Source Independence", matrix.get("source_independence", 75), "Cross-platform uncached signals"),
            ("Signal Recency", matrix.get("signal_recency", 90), "Time-decay freshness score"),
            ("Cross-Signal Correlation", matrix.get("cross_signal_correlation", 85), "Inter-stream signal synergy"),
            ("Contradicting Evidence Weight", matrix.get("contradicting_weight", 60), "Impact of counter-theses"),
            ("Historical Consistency", matrix.get("historical_consistency", 70), "Trajectory coherence against baseline")
        ]

        for idx, (label, val, desc) in enumerate(dims):
            col = dim_cols[idx % 3]
            with col:
                st.markdown(f"**{label}** (`{val}/100`)")
                st.progress(val / 100)
                st.caption(desc)

        st.markdown(f"""
        <div style="background: rgba(245, 158, 11, 0.1); border-left: 3px solid #f59e0b; padding: 12px; border-radius: 6px; margin-top: 16px;">
            <div style="color: #f59e0b; font-weight: 700; font-size: 0.9rem;">❓ WHY NOT HIGHER CONFIDENCE?</div>
            <div style="color: #e2e8f0; font-size: 0.95rem; margin-top: 4px;">
                "{why_not}"
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🎯 Decision Impact: 'So What?'")
        act_col, trig_col = st.columns(2)
        with act_col:
            st.markdown("##### 🚀 Recommended Actions")
            for act in dossier.get("strategic_actions", []):
                st.markdown(f"- **{act}**")
        with trig_col:
            st.markdown("##### 🔭 Next Signals to Watch")
            for trig in dossier.get("watch_triggers", []):
                st.markdown(f"- 🎯 {trig}")

    # --------------------------------------------------------------------------
    # TAB 3: 4 LIVE TAVILY DATA STREAMS
    # --------------------------------------------------------------------------
    with tab_streams:
        st.markdown("### 📡 4 Parallel Web Intelligence Streams")
        st.caption("Live web signals collected via Tavily Search API with automated source provenance classification.")

        raw_streams = scan.get("raw_streams", [])
        for stream in raw_streams:
            cat = stream.get("category", "Intelligence Stream")
            results = stream.get("results", [])
            query = stream.get("query", "")

            with st.expander(f"📁 **{cat}** ({len(results)} signals)", expanded=True):
                st.caption(f"**Query Executed:** `{query}`")
                for r in results:
                    title = r.get("title", "Untitled")
                    url = r.get("url", "#")
                    snippet = r.get("snippet", "")

                    st.markdown(f"""
                    <div class="evidence-item">
                        <div style="display: flex; justify-content: space-between;">
                            <a href="{url}" target="_blank">{title}</a>
                        </div>
                        <div style="font-size: 0.85rem; color: #94a3b8; margin: 4px 0;">{url}</div>
                        <div style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.4;">{snippet}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Deep Page Extraction Section (Tavily Extract API)
        extracted = scan.get("extracted_pages", [])
        if extracted:
            st.markdown("---")
            st.markdown("#### 🔍 Deep Page Extractions (`tavily.extract`)")
            st.caption("PulseGrid uses Tavily's Extract API to pull full, clean boilerplate-free markdown for deep document and pricing diffs.")
            for ep in extracted:
                with st.expander(f"📄 Full Clean Content: {ep.get('url', 'Document')}", expanded=False):
                    st.code(ep.get("raw_content", "")[:1200] + "\n...", language="markdown")

    # --------------------------------------------------------------------------
    # TAB 4: BASELINE & CHANGE ENGINE
    # --------------------------------------------------------------------------
    with tab_change:
        st.markdown("### 🔄 Baseline & Change Engine")
        st.caption("PulseGrid establishes a baseline upon first scan and detects incremental operational drifts on subsequent passes.")

        change_data = scan.get("change_signals", {})
        is_baseline = change_data.get("is_baseline_first_scan", True)

        if is_baseline:
            st.info(f"📍 **Baseline Established for {company_name}:** This scan represents the initial state snapshot. Future scans will calculate structural diffs (e.g., net hiring shifts, pricing tier updates, forum complaint spikes).")
        else:
            st.success(f"🔍 **Historical Comparison Active:** Compared to prior scan from `{change_data.get('previous_scan_date')}`.")

        st.markdown("#### 📈 Detected Signal Diffs")
        for change_item in change_data.get("summary_changes", []):
            st.markdown(f"- **{change_item}**")

        st.markdown("---")
        st.markdown("#### 👁️ Active Watch Mode Pipeline")
        st.markdown("""
        When a company is in **Watch Mode**, PulseGrid continuously monitors the 4 live streams and adversarial triggers:
        1. **New Signal Detected** ➔ Compare against baseline snapshot
        2. **Reassess Hypothesis** ➔ Calculate confidence delta (`61% → 78%`)
        3. **Adversarial Resweep** ➔ Check if new statements dispute the move
        4. **Alert Strategy Team** ➔ Trigger Executive Notification
        """)
