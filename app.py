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
from ai_engine import (synthesize_threat_dossier, dossier_to_markdown, nebius_client,
                       confidence_label, chat_json_for, _build_pool, _pool_text)
import track_record as tr
import store
from search_engine import make_slug
import ui_theme as ui

st.set_page_config(page_title="PulseGrid AI", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")
ui.inject_theme()

SIMULATED = simulation_enabled()
MAX_RUNS_PER_SESSION = 5
COMPANY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&'\-]{0,59}$")

for key, default in (("search_data", None), ("dossier_content", None), ("active_company", ""),
                     ("run_error", None), ("run_count", 0), ("suggestions", []), ("saved_prediction", None), ("track_error", None)):
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
        st.session_state.suggestions, st.session_state.saved_prediction, st.session_state.track_error = [], None, None
        if not SIMULATED:
            slug = make_slug(target_company)
            try:  # track record must never break an investigation
                st.session_state.suggestions = tr.suggest_resolutions(
                    target_company, slug, search_data, analysis,
                    chat_json_for({"suggestions": list}, "resolution step"), _pool_text, _build_pool)
            except Exception as e:
                st.session_state.track_error = f"Could not check earlier predictions: {redact(e)}"
            try:
                tr.apply_history(analysis, confidence_label)
                st.session_state.saved_prediction = tr.save_prediction(target_company, slug, analysis)
            except Exception as e:
                st.session_state.track_error = f"Could not save prediction: {redact(e)}"
    except PulseGridError as e:
        st.session_state.run_error = redact(e)
    except Exception as e:  # unexpected - still show the real message
        st.session_state.run_error = f"{type(e).__name__}: {redact(e)}"
    live_ph.empty()

if st.session_state.run_error:
    st.error(f"Live API call failed — no data was faked.\n\n{st.session_state.run_error}")

# ---------------------------------------------------------------- results
# Order: status -> summary -> tabs -> actions -> (under the hood, track record)
d = st.session_state.dossier_content
sd = st.session_state.search_data
if d and sd:
    ui.render(ui.status_html(sd["diff"], d.get("simulated", False), d["meta"]["model"], sd["storage_backend"]))
    for w in sd.get("storage_warnings", []):
        st.warning(w)
    ui.render(ui.summary_html(d))
    ui.render(ui.spacer(32))

    t_ev, t_self, t_score, t_chg, t_src = st.tabs(["Evidence", "Self-challenge", "Score", "Changes", "Sources"])

    with t_ev:
        ui.render(ui.pulse_grid_html(d, sd["raw_streams"]))
        ui.render(ui.evidence_tab_html(d))

    with t_self:
        ui.render(ui.selfchallenge_html(d))

    with t_score:
        ui.render(ui.calc_html(d))

    with t_chg:
        diff = sd["diff"]
        if diff["first_scan"]:
            ui.render('<div class="stitle">Changes<span class="sub">परिवर्तन</span></div>'
                      '<div class="p2" style="margin-top:12px">First scan — baseline saved. Rescan later to see what changed. No changes are claimed.</div>')
        else:
            new = diff["new_signals"]
            body = "".join(
                f'<div class="qrow"><span class="qt">{ui.esc(n["category"])}</span><span class="qq">'
                f'{ui.link(n["url"], n["title"])}</span></div>' for n in new) or \
                '<div class="empty">No new sources since the previous scan.</div>'
            ui.render(f'<div class="stitle">Changes<span class="sub">परिवर्तन · matched by source URL</span></div>'
                      f'<div class="cap" style="margin-top:8px">{len(new)} new source(s); {diff["gone_count"]} previously seen source(s) did not appear.</div>{body}')

    with t_src:
        for s in sd["raw_streams"]:
            ui.render(f'<div class="stitle">{ui.esc(s.get("category", ""))} · {len(s.get("results", []))}</div>')
            for it in s.get("results", []):
                ui.render(f'<div class="ev sup" style="background:var(--inner);border-color:var(--line)"><div><div class="cl">{ui.esc(it.get("title"))}</div>'
                          f'<div class="cap">{ui.esc((it.get("snippet") or "")[:300])}</div>'
                          f'<div class="mt"><span class="tag">{ui.esc(it.get("provenance"))}</span>{ui.link(it.get("url", ""), it.get("url", ""))}</div></div></div>')

    ui.render(ui.spacer(32))
    a_left, a_right = st.columns([3, 2], gap="large")
    with a_left:
        ui.render(ui.watch_next_html(d))
    with a_right:
        if st.button("Save baseline", type="secondary", use_container_width=True):
            st.toast(f"Baseline is saved automatically after every scan (store: {sd['storage_backend']}).")
        st.download_button("Download report", data=dossier_to_markdown(d, sd["delta_highlights"]),
                           file_name=f"{re.sub(r'[^a-z0-9]+', '_', st.session_state.active_company.lower())}_pulsegrid.md",
                           mime="text/markdown", use_container_width=True)
elif not st.session_state.run_error and not (launch_btn and company_input.strip()):
    ui.render(ui.idle_html(tavily_client is not None, nebius_client is not None, NEBIUS_MODEL))

# ---------------------------------------------------------------- smriti suggestions (need a decision, so shown above the fold)
if st.session_state.suggestions:
    ui.render('<div class="stitle" style="color:#E9A93B">Earlier predictions new evidence may resolve<span class="sub">स्मृति</span></div>')
    for i, sg in enumerate(st.session_state.suggestions):
        ui.render(ui.suggestion_html(sg))
        a1, a2, _ = st.columns([1, 1, 3])
        if a1.button("Accept", key=f"acc{i}", use_container_width=True):
            tr.resolve(sg["prediction_id"], sg["suggestion"], sg["url"], "Accepted model suggestion: " + sg["reason"])
            st.session_state.suggestions = [x for j, x in enumerate(st.session_state.suggestions) if j != i]
            st.rerun()
        if a2.button("Dismiss", key=f"dis{i}", use_container_width=True):
            st.session_state.suggestions = [x for j, x in enumerate(st.session_state.suggestions) if j != i]
            st.rerun()
if st.session_state.track_error:
    st.warning(st.session_state.track_error)

# ---------------------------------------------------------------- collapsed bottom sections
ui.render(ui.spacer(32))
if d and sd:
    with st.expander("Under the hood"):
        ui.render(ui.under_hood_html(d, sd))

rows = []
try:
    rows = tr.list_predictions()
except Exception as e:
    st.warning(f"Track record unavailable: {redact(e)}")
with st.expander("Track record · स्मृति Smriti"):
    ui.render(ui.smriti_html(rows, tr.pattern_stats(rows) if rows else [], store.backend()))
    pending = [r for r in rows if r.get("status") == "pending"]
    if pending:
        st.markdown("**Mark an outcome manually**")
        labels = {f'{r.get("company_name")} · {str(r.get("created_at", ""))[:10]} · {r["hypothesis"][:70]}': r for r in pending}
        pick = st.selectbox("Prediction", list(labels))
        outcome = st.radio("Outcome", ["confirmed", "refuted"], horizontal=True)
        res_url = st.text_input("Evidence URL (optional, http/https)")
        res_note = st.text_input("Note (optional)", max_chars=300)
        if st.button("Save outcome"):
            try:
                tr.resolve(labels[pick]["id"], outcome, res_url, res_note)
                st.rerun()
            except PulseGridError as e:
                st.error(str(e))
