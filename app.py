"""
app.py
======
PulseGrid AI - competitive intelligence that argues with itself.
Nebius x NVIDIA Global AI Hackathon. Streamlit UI ("Kolam" theme in ui_theme.py).

Screens (st.session_state["screen"]): splash -> investigate -> thinking -> results -> actions,
plus two pages in the top nav: watchlist and track_record. Results live in session_state,
so they survive moving between screens and pages.
"""

import re
import streamlit as st

from config import simulation_enabled, NEBIUS_MODEL, redact
from search_engine import run_pulsegrid_search, PulseGridError, tavily_client
from ai_engine import (synthesize_threat_dossier, dossier_to_markdown, nebius_client,
                       confidence_label, chat_json_for, _build_pool, _pool_text)
import track_record as tr
import alerts
import store
from search_engine import make_slug
import ui_theme as ui

st.set_page_config(page_title="PulseGrid AI", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")
ui.inject_theme()

SIMULATED = simulation_enabled()
MAX_RUNS_PER_SESSION = 5
COMPANY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&'\-]{0,59}$")
FLOW = ["investigate", "thinking", "results", "actions"]
NAV = [("investigate", "Investigate"), ("watchlist", "Watchlist"), ("track_record", "Track record")]

for key, default in (("screen", "splash"), ("search_data", None), ("dossier_content", None), ("active_company", ""),
                     ("run_error", None), ("run_count", 0), ("suggestions", []), ("saved_prediction", None),
                     ("track_error", None), ("alert_msg", None), ("pending_company", None), ("form_error", None)):
    if key not in st.session_state:
        st.session_state[key] = default


def go(screen: str) -> None:
    st.session_state.screen = screen


def has_results() -> bool:
    return bool(st.session_state.dossier_content and st.session_state.search_data)


# ---------------------------------------------------------------- shared chrome
def header(screen: str) -> None:
    c_brand, c_right = st.columns([1, 2], vertical_alignment="center")
    with c_brand:
        ui.render(ui.brand_html())
    with c_right:
        if screen in FLOW[1:]:
            ui.render(ui.tracker_html(FLOW.index(screen)))
        else:
            with st.container(horizontal=True, horizontal_alignment="right", gap="medium"):
                for key, label in NAV:
                    st.button(label, key=f"nav_{key}", type="tertiary", on_click=go, args=(key,))
    ui.render(ui.hair_html())


# ---------------------------------------------------------------- run (real calls; failures are shown)
def start_investigation(company: str) -> bool:
    """Validates and queues a run; the thinking screen executes it."""
    company = company.strip()
    if not COMPANY_RE.match(company):
        st.session_state.form_error = "Company name: 1-60 characters; letters, numbers, spaces and . , & ' - only."
        return False
    if st.session_state.run_count >= MAX_RUNS_PER_SESSION and not SIMULATED:
        st.session_state.form_error = (f"Limit reached: {MAX_RUNS_PER_SESSION} investigations per session. "
                                       "Reload the page to start a new session.")
        return False
    st.session_state.form_error = None
    st.session_state.pending_company = company
    st.session_state.screen = "thinking"
    return True


def execute(target_company: str, live_ph) -> None:
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
                prev = tr.latest_confidence(slug)   # read BEFORE saving the new prediction
                tr.apply_history(analysis, confidence_label)
                st.session_state.saved_prediction = tr.save_prediction(target_company, slug, analysis)
            except Exception as e:
                prev = None
                st.session_state.track_error = f"Could not save prediction: {redact(e)}"
            st.session_state.alert_msg = None
            try:  # alerts must never break an investigation
                if alerts.is_watched(slug):
                    al = alerts.evaluate(target_company, slug, analysis, search_data["diff"], prev, prefs=alerts.watchlist.first(company_slug=slug))
                    if al:
                        sent = alerts.send_if_new(al)
                        st.session_state.alert_msg = ("Alert sent via " + ", ".join(sent)) if sent else "Alert already sent earlier (not repeated)."
                    else:
                        st.session_state.alert_msg = "On watchlist: no alert triggered by this rescan."
            except Exception as e:
                st.session_state.alert_msg = f"Alert failed: {redact(e)}"
    except PulseGridError as e:
        st.session_state.run_error = redact(e)
    except Exception as e:  # unexpected - still show the real message
        st.session_state.run_error = f"{type(e).__name__}: {redact(e)}"


# ---------------------------------------------------------------- screens
def screen_investigate() -> None:
    ui.render(ui.idle_html(tavily_client is not None, nebius_client is not None, NEBIUS_MODEL))
    with st.form("investigate", border=False):
        c_in, c_btn = st.columns([4, 1.3], vertical_alignment="bottom")
        company = c_in.text_input("Company", key="company_input", placeholder="Company to investigate, e.g. Databricks",
                                  max_chars=60, label_visibility="collapsed")
        submitted = c_btn.form_submit_button("Investigate", type="primary", use_container_width=True)
    if submitted and company.strip() and start_investigation(company):
        st.rerun()
    if st.session_state.form_error:
        st.error(st.session_state.form_error)


def screen_thinking() -> None:
    live_ph = st.empty()
    pending = st.session_state.pending_company
    if pending:
        st.session_state.pending_company = None
        execute(pending, live_ph)
        live_ph.empty()
    if st.session_state.run_error:
        st.error(f"Live API call failed — no data was faked.\n\n{st.session_state.run_error}")
        st.button("Try again", type="primary", on_click=go, args=("investigate",))
    elif has_results():
        st.button("See results →", key="see_results", type="primary", on_click=go, args=("results",))
    else:
        go("investigate")
        st.rerun()


def screen_results() -> None:
    d = st.session_state.dossier_content
    sd = st.session_state.search_data
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
            ui.render(ui.section_label("What changed") +
                      '<div class="p2" style="margin-top:12px">First scan — baseline saved. Rescan later to see what changed. No changes are claimed.</div>')
        else:
            new = diff["new_signals"]
            body = "".join(
                f'<div class="qrow"><span class="qt">{ui.esc(n["category"])}</span><span class="qq">'
                f'{ui.link(n["url"], n["title"])}</span></div>' for n in new) or \
                '<div class="empty">No new sources since the previous scan.</div>'
            ui.render(ui.section_label("What changed") +
                      f'<div class="cap" style="margin-top:8px">Matched by source URL: {len(new)} new source(s); {diff["gone_count"]} previously seen source(s) did not appear.</div>{body}')
    with t_src:
        for s in sd["raw_streams"]:
            ui.render(ui.section_label(f'{s.get("category", "")} · {len(s.get("results", []))}', small=True))
            for it in s.get("results", []):
                ui.render(f'<div class="ev sup" style="background:var(--inner);border-color:var(--line)"><div><div class="cl">{ui.esc(it.get("title"))}</div>'
                          f'<div class="cap">{ui.esc((it.get("snippet") or "")[:300])}</div>'
                          f'<div class="mt">{ui.tag_html(it.get("provenance"))}{ui.link(it.get("url", ""), it.get("url", ""))}</div></div></div>')
    with st.expander("Under the hood"):
        ui.render(ui.under_hood_html(d, sd))
    ui.render(ui.spacer(24))
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        st.button("← Back to the pattern", type="tertiary", on_click=go, args=("thinking",))
        st.button("See recommended actions →", type="primary", on_click=go, args=("actions",))


def screen_actions() -> None:
    d = st.session_state.dossier_content
    sd = st.session_state.search_data
    ui.render(ui.watch_next_html(d))
    slug_now = make_slug(st.session_state.active_company)
    watched = False
    try:
        watched = alerts.is_watched(slug_now)
    except Exception:
        pass
    if watched:
        if st.button("Stop watching", type="primary"):
            alerts.unwatch(slug_now)
            st.rerun()
    elif st.button("Watch this company", type="primary", disabled=d.get("simulated", False)):
        try:
            alerts.watch(slug_now, st.session_state.active_company)
            st.rerun()
        except Exception as e:
            st.error(f"Could not save to watchlist: {redact(e)}")
    if st.session_state.alert_msg:
        st.caption(st.session_state.alert_msg)
    st.download_button("Download report", data=dossier_to_markdown(d, sd["delta_highlights"]),
                       file_name=f"{re.sub(r'[^a-z0-9]+', '_', st.session_state.active_company.lower())}_pulsegrid.md",
                       mime="text/markdown")
    st.button("New investigation", on_click=go, args=("investigate",))
    st.button("← Back to results", type="tertiary", on_click=go, args=("results",))


def page_watchlist() -> None:
    ui.render(ui.section_label("Watchlist"))
    try:
        rows = alerts.list_watched()
    except Exception as e:
        rows = []
        st.warning(f"Watchlist unavailable: {redact(e)}")
    if not rows:
        ui.render('<div class="empty">No companies watched yet. Investigate a company and click Watch.</div>')
    for r in rows:
        ui.render(f'<div class="p2">{ui.esc(r.get("company_name"))}</div>')
    if st.button("Send test alert"):
        try:
            st.toast("TEST alert sent via " + ", ".join(alerts.test_alert(st.session_state.active_company or "Test company")))
        except PulseGridError as e:
            st.error(str(e))


def page_track_record() -> None:
    if st.session_state.suggestions:
        ui.render(ui.section_label("Earlier predictions new evidence may resolve"))
        for i, sg in enumerate(st.session_state.suggestions):
            ui.render(ui.suggestion_html(sg))
            a1, a2, _ = st.columns([1, 1, 3])
            if a1.button("Accept", key=f"acc{i}", use_container_width=True):
                tr.resolve(sg["prediction_id"], sg["suggestion"], sg["url"], "Accepted model suggestion: " + sg["reason"])
                try:
                    slug_r = make_slug(st.session_state.active_company)
                    if alerts.is_watched(slug_r):
                        alerts.send_if_new(alerts.resolution_alert(st.session_state.active_company, slug_r,
                                           {"id": sg["prediction_id"], "hypothesis": sg["hypothesis"]}, sg["suggestion"], sg["url"]))
                except Exception:
                    pass  # alert failure must not block resolving
                st.session_state.suggestions = [x for j, x in enumerate(st.session_state.suggestions) if j != i]
                st.rerun()
            if a2.button("Dismiss", key=f"dis{i}", use_container_width=True):
                st.session_state.suggestions = [x for j, x in enumerate(st.session_state.suggestions) if j != i]
                st.rerun()
    if st.session_state.track_error:
        st.warning(st.session_state.track_error)

    rows = []
    try:
        rows = tr.list_predictions()
    except Exception as e:
        st.warning(f"Track record unavailable: {redact(e)}")
    ui.render(ui.smriti_html(rows, tr.pattern_stats(rows) if rows else [], store.backend()))
    pending = [r for r in rows if r.get("status") == "pending"]
    if pending:
        with st.expander("Mark an outcome manually"):
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


SCREENS = {"investigate": screen_investigate, "thinking": screen_thinking, "results": screen_results,
           "actions": screen_actions, "watchlist": page_watchlist, "track_record": page_track_record}

# ---------------------------------------------------------------- dispatch
screen = st.session_state.screen
if screen == "splash":
    screen = st.session_state.screen = "investigate"
if screen in ("results", "actions") and not has_results():
    screen = st.session_state.screen = "investigate"

ui.render(ui.strip_html())
ui.render(ui.screen_css(dotted=screen in ("investigate", "thinking"),
                        active_nav=screen if screen in dict(NAV) else ""))
if SIMULATED:
    ui.render(ui.sim_banner_html())
header(screen)
SCREENS[screen]()
