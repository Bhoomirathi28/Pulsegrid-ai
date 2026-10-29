"""
app.py
======
PulseGrid AI - competitive intelligence that argues with itself.
Nebius x NVIDIA Global AI Hackathon. Streamlit UI ("Kolam" theme in ui_theme.py).
"""

import re
import streamlit as st

from config import simulation_enabled, NEBIUS_MODEL, redact
from search_engine import run_pulsegrid_search, PulseGridError, tavily_client
from ai_engine import synthesize_threat_dossier, dossier_to_markdown, nebius_client
import ui_theme as ui

st.set_page_config(page_title="PulseGrid AI", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")
ui.inject_theme()

SIMULATED = simulation_enabled()
MAX_RUNS_PER_SESSION = 5
COMPANY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&'\-]{0,59}$")

for key, default in (("search_data", None), ("dossier_content", None), ("active_company", ""),
                     ("run_error", None), ("run_count", 0)):
    if key not in st.session_state:
        st.session_state[key] = default

if SIMULATED:
    ui.render(ui.sim_banner_html())

# ---------------------------------------------------------------- header + input
c_title, c_input, c_btn = st.columns([5, 3, 1.5], vertical_alignment="bottom")
with c_title:
    ui.render(ui.header_html())
with c_input:
    company_input = st.text_input("Company", value="", placeholder="e.g. Databricks", max_chars=60)
with c_btn:
    launch_btn = st.button("Investigate", type="primary", use_container_width=True)
ui.render(ui.divider_html())

live_ph = st.empty()

# ---------------------------------------------------------------- run (real calls; failures are shown)
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

    ui.render(ui.live_html(None, 0), live_ph)
    try:
        search_data = run_pulsegrid_search(target_company)
        st.session_state.search_data = search_data
        counts = [len(s.get("results", [])) for s in search_data["raw_streams"]]
        ui.render(ui.live_html(counts, 0), live_ph)

        analysis = synthesize_threat_dossier(
            target_company, search_data,
            on_progress=lambda n: ui.render(ui.live_html(counts, n), live_ph),
        )
        st.session_state.dossier_content = analysis
    except PulseGridError as e:
        st.session_state.run_error = redact(e)
    except Exception as e:  # unexpected - still show the real message
        st.session_state.run_error = f"{type(e).__name__}: {redact(e)}"
    live_ph.empty()

if st.session_state.run_error:
    st.error(f"Live API call failed — no data was faked.\n\n{st.session_state.run_error}")

# ---------------------------------------------------------------- results
d = st.session_state.dossier_content
sd = st.session_state.search_data
if d and sd:
    ui.render(ui.status_html(sd["diff"], d.get("simulated", False), d["meta"]["model"], sd["storage_backend"]))
    for w in sd.get("storage_warnings", []):
        st.warning(w)
    ui.render(ui.hero_html(d["hypothesis"], d["executive_summary"], d["confidence"]))
    ui.render(ui.pulse_grid_html(d, sd["raw_streams"]))
    ui.render(ui.evidence_columns_html(d))

    left, right = st.columns(2)
    with left:
        ui.render(ui.calc_html(d))
    with right:
        ui.render(ui.watch_html(d))
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Save baseline", type="secondary", use_container_width=True):
                st.toast(f"Baseline is saved automatically after every scan (store: {sd['storage_backend']}).")
        with b2:
            st.download_button("Download .md", data=dossier_to_markdown(d, sd["delta_highlights"]),
                               file_name=f"{re.sub(r'[^a-z0-9]+', '_', st.session_state.active_company.lower())}_pulsegrid.md",
                               mime="text/markdown", use_container_width=True)

    with st.expander("View all sources"):
        if not sd["diff"]["first_scan"]:
            news = sd["diff"]["new_signals"]
            ui.render(f'<div class="cap">{len(news)} source(s) are new since the previous scan; '
                      f'{sd["diff"]["gone_count"]} previously seen source(s) did not appear.</div>')
        for s in sd["raw_streams"]:
            ui.render(f'<div class="stitle" style="margin-top:18px">{ui.esc(s.get("category", ""))} · {len(s.get("results", []))}</div>')
            for it in s.get("results", []):
                ui.render(f'<div class="ev sup" style="background:var(--inner);border-color:var(--line)"><div><div class="cl">{ui.esc(it.get("title"))}</div>'
                          f'<div class="cap">{ui.esc((it.get("snippet") or "")[:300])}</div>'
                          f'<div class="mt"><span class="tag">{ui.esc(it.get("provenance"))}</span>{ui.link(it.get("url", ""), it.get("url", ""))}</div></div></div>')
elif not st.session_state.run_error and not (launch_btn and company_input.strip()):
    ui.render(ui.idle_html(tavily_client is not None, nebius_client is not None, NEBIUS_MODEL))
