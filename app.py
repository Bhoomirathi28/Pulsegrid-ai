import os
import streamlit as st
from dotenv import load_dotenv

from search_engine import run_pulsegrid_search
from ai_engine import synthesize_threat_dossier

load_dotenv()

# ==============================================================================
# 1. Page Configuration & Dark Theme Styling
# ==============================================================================
st.set_page_config(
    page_title="PulseGrid AI — Competitive Threat Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Executive Dark Cyber Intelligence Theme CSS
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

    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
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

    /* Card Component */
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
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    .badge-secondary {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    .badge-community {
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Delta Signal Items */
    .delta-item {
        background: rgba(15, 23, 42, 0.8);
        border-left: 4px solid #38bdf8;
        border-radius: 4px 8px 8px 4px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.75rem;
        color: #e2e8f0;
        font-size: 0.95rem;
    }

    /* Custom Streamlit Buttons */
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
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. Sidebar: System Health & Technical Specs
# ==============================================================================
def is_valid_key(key: str) -> bool:
    if not key:
        return False
    key_clean = key.strip().lower()
    return not any(p in key_clean for p in ["your_", "placeholder", "xxx", "change_me", "todo"])


tavily_key = os.getenv("TAVILY_API_KEY", "")
nebius_key = os.getenv("NEBIUS_API_KEY", "")
supabase_url = os.getenv("SUPABASE_URL", "")

with st.sidebar:
    st.markdown("## ⚡ PulseGrid AI")
    st.caption("Autonomous Competitive Intelligence Engine")
    st.markdown("---")

    st.markdown("### 🔌 System Health & Integrations")

    # Tavily Status
    if is_valid_key(tavily_key):
        st.markdown("🟢 **Tavily Search API**: Connected (4-Stream)")
    else:
        st.markdown("🔴 **Tavily Search API**: Missing Key")

    # Nebius / NVIDIA Nemotron Status
    if is_valid_key(nebius_key):
        st.markdown("🟢 **Nebius Token Factory**: Connected *(Nemotron 3 Super 120B)*")
    else:
        st.markdown("🟠 **Nebius Token Factory**: Local Preview Mode")

    # Supabase Status
    if is_valid_key(supabase_url):
        st.markdown("🟢 **Supabase Cache**: Connected *(Delta Diffing Active)*")
    else:
        st.markdown("⚪ **Supabase Cache**: Offline / Memory Mode")

    st.markdown("---")
    st.markdown("### 🛠️ Architecture Specs")
    st.markdown("""
    - **Reasoning Model**: NVIDIA Nemotron-3 Super (120B)
    - **Inference Engine**: Nebius Token Factory
    - **Web Retrieval**: Tavily Multi-Stream Parallel RAG
    - **Delta Engine**: Supabase Snapshot Cache Diffing
    - **Analysis Flow**: 3-Phase Adversarial Verification
    """)

    st.markdown("---")
    st.caption("PulseGrid AI v2.0 • Autonomous Threat Scanner")


# ==============================================================================
# 3. Main Interface: Header & Investigation Trigger
# ==============================================================================
st.markdown("""
<div class="main-header">
    <div class="main-title">⚡ PulseGrid AI: Autonomous Threat Scanner</div>
    <div class="main-subtitle">
        Scan live web streams across <b>Talent & Hiring</b>, <b>Product & Pricing</b>, <b>Customer Friction</b>, 
        and <b>Market News</b>, then challenge findings through <b>3-Phase Adversarial Verification</b>.
    </div>
</div>
""", unsafe_allow_html=True)

# Input Column Layout
col1, col2 = st.columns([3, 1])

with col1:
    company_input = st.text_input(
        "Target Company / Competitor",
        value="",
        placeholder="e.g. OpenAI, Anthropic, Databricks, Mistral AI, Cohere",
        help="Enter the exact company or brand name you wish to investigate."
    )

with col2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    launch_btn = st.button("🚀 Launch Investigation", use_container_width=True)

# Initialize Session State
if "search_data" not in st.session_state:
    st.session_state.search_data = None
if "dossier_content" not in st.session_state:
    st.session_state.dossier_content = None
if "active_company" not in st.session_state:
    st.session_state.active_company = ""


# ==============================================================================
# 4. Live Progress Stepper & Investigation Execution
# ==============================================================================
if launch_btn and company_input.strip():
    target_company = company_input.strip()
    st.session_state.active_company = target_company

    with st.status(f"⚡ Investigating '{target_company}'...", expanded=True) as status:
        # Step 1: Multi-Stream Search
        st.write("📡 **Step 1/3**: Scanning 4 parallel Tavily web streams across Talent, Pricing, Friction, and News...")
        search_data = run_pulsegrid_search(target_company)
        st.session_state.search_data = search_data

        # Step 2: Delta Signals
        st.write("🔍 **Step 2/3**: Calculating Delta Signals vs historical snapshot in Supabase cache...")
        deltas = search_data.get("delta_highlights", [])
        st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;↳ Found {len(deltas)} delta signal highlights.")

        # Step 3: Nemotron Adversarial Synthesis
        st.write("🧠 **Step 3/3**: Executing Nemotron 3 Adversarial Synthesis & Verification...")
        dossier = synthesize_threat_dossier(target_company, search_data)
        st.session_state.dossier_content = dossier

        status.update(
            label=f"✅ Investigation Complete for {target_company}!",
            state="complete",
            expanded=False
        )


# ==============================================================================
# 5. Tabbed Results Display
# ==============================================================================
if st.session_state.dossier_content and st.session_state.search_data:
    company_name = st.session_state.active_company
    search_data = st.session_state.search_data
    dossier = st.session_state.dossier_content

    tab1, tab2, tab3 = st.tabs([
        "⚡ Executive Threat Dossier",
        "🔍 Delta Signals",
        "🌐 Evidence Ledger (Raw Streams)"
    ])

    # --------------------------------------------------------------------------
    # Tab 1: Executive Threat Dossier
    # --------------------------------------------------------------------------
    with tab1:
        col_header, col_download = st.columns([3, 1])
        with col_header:
            st.markdown(f"### 🛡️ Threat Intelligence Dossier: `{company_name}`")
        with col_download:
            st.download_button(
                label="📥 Download Dossier (.md)",
                data=dossier,
                file_name=f"{company_name.lower()}_pulsegrid_dossier.md",
                mime="text/markdown",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown(dossier)

    # --------------------------------------------------------------------------
    # Tab 2: Delta Signals
    # --------------------------------------------------------------------------
    with tab2:
        st.markdown("### 🔍 Historical Baseline Delta Highlights")
        st.caption("New or modified signals detected since the last baseline snapshot in Supabase.")

        delta_signals = search_data.get("delta_highlights", [])
        if delta_signals:
            for signal in delta_signals:
                st.markdown(f"<div class='delta-item'>⚡ {signal}</div>", unsafe_allow_html=True)
        else:
            st.info("No delta differences detected from prior scans. Current data established as fresh baseline.")

    # --------------------------------------------------------------------------
    # Tab 3: Evidence Ledger (Raw Streams)
    # --------------------------------------------------------------------------
    with tab3:
        st.markdown("### 🌐 Evidence Ledger across 4 Parallel Streams")
        st.caption("Raw intelligence retrieved via Tavily with source provenance classification.")

        raw_streams = search_data.get("raw_streams", [])

        if raw_streams:
            for stream in raw_streams:
                category = stream.get("category", "Intelligence Stream")
                results = stream.get("results", [])

                with st.expander(f"📁 {category} ({len(results)} items)", expanded=True):
                    if not results:
                        st.caption("No signals retrieved for this category.")
                    else:
                        for idx, item in enumerate(results, 1):
                            provenance = item.get("provenance", "Secondary")
                            badge_class = "badge-secondary"
                            if provenance == "Primary":
                                badge_class = "badge-primary"
                            elif provenance == "Community":
                                badge_class = "badge-community"

                            title = item.get("title", "Untitled Signal")
                            snippet = item.get("snippet", "No snippet available.")
                            url = item.get("url", "#")

                            st.markdown(f"""
                            <div class="glass-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                    <span style="font-weight: 600; font-size: 1rem; color: #f1f5f9;">{idx}. {title}</span>
                                    <span class="{badge_class}">{provenance}</span>
                                </div>
                                <div style="color: #94a3b8; font-size: 0.9rem; line-height: 1.5; margin-bottom: 8px;">
                                    {snippet}
                                </div>
                                <div>
                                    <a href="{url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 0.85rem; font-family: 'JetBrains Mono', monospace;">
                                        🔗 {url}
                                    </a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.info("No raw stream data available. Click 'Launch Investigation' above to scan.")

elif not launch_btn:
    st.markdown("""
    <div style="text-align: center; padding: 4rem 1rem; color: #64748b;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
        <div style="font-size: 1.25rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.5rem;">
            Ready to Investigate
        </div>
        <div>
            Enter a target competitor above and click <b>Launch Investigation</b> to execute multi-stream threat scanning.
        </div>
    </div>
    """, unsafe_allow_html=True)
