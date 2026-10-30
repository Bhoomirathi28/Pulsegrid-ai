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
import time

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
                     ("track_error", None), ("alert_msg", None), ("pending_company", None), ("form_error", None), ("scan_n", None),
                     ("run", None), ("run_log", [])):
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


def execute(target_company: str, left_ph, right_ph) -> None:
    """Runs one investigation with real calls, redrawing the thinking screen as each step finishes.
    Everything the later screens show is stored in session_state (run, search_data, dossier_content, run_log)."""
    st.session_state.run_count += 1
    st.session_state.active_company = target_company
    st.session_state.search_data = None
    st.session_state.dossier_content = None
    st.session_state.scan_n = None
    st.session_state.suggestions, st.session_state.saved_prediction, st.session_state.track_error = [], None, None
    run = {"company": target_company, "t0": time.time(), "events": [], "error": None, "done": False, "sup": 0, "con": 0,
           "stages": [{"status": "WAITING", "detail": tpl} for (_, _, _, tpl) in ui.STAGES]}
    st.session_state.run = run
    log: list = []
    st.session_state.run_log = log

    def redraw() -> None:
        ui.render(ui.thinking_left_html(run), left_ph)
        ui.render(ui.kolam_panel_html(run), right_ph)

    def stage(i: int, status: str, detail: str = None) -> None:
        run["stages"][i]["status"] = status
        if detail is not None:
            run["stages"][i]["detail"] = detail
        redraw()

    def add(kind: str, text: str) -> None:
        run["events"].append({"t": time.time() - run["t0"], "kind": kind, "text": text})
        redraw()

    def verdict_text(score: float) -> str:
        name, nxt, pts = ui.band5(score)
        return f"{name} · {pts:g} points from {nxt}" if nxt else f"{name} · top band"

    def on_event(kind: str, text: str, data: dict = None) -> None:
        data = data or {}
        step = data.get("step")
        if step == "verdict":  # the log line uses the display band, so build it here
            text = f"confidence {data['score']:g} · {verdict_text(data['score'])}"
        run["events"].append({"t": time.time() - run["t0"], "kind": kind, "text": text})
        if step == "hypothesis":
            run["sup"] = data["cited"]
            stage(2, "DONE", f"Nemotron cited {data['cited']} evidence items")
            stage(3, "RUNNING")
        elif step == "challenge":
            run["con"] = data["contradict"]
            stage(3, "DONE", f"{data['queries']} counter-searches · {data['results']} results · {data['contradict']} contradict")
            stage(4, "RUNNING")
        elif step == "verdict":
            stage(4, "DONE", f"Score computed in Python · {data['score']:g} · {ui.band5(data['score'])[0]}")
        else:
            redraw()

    try:
        stage(0, "RUNNING")
        search_data = run_pulsegrid_search(target_company, on_event=lambda k, t: add(k, t))
        st.session_state.search_data = search_data
        items = [it for s in search_data["raw_streams"] for it in s.get("results", [])]
        n_by = {k: sum(1 for it in items if it.get("provenance") == k) for k in ("Primary", "Secondary", "Community")}
        stage(0, "DONE", f"4 parallel Tavily streams · {len(items)} sources")
        stage(1, "DONE", f"Official {n_by['Primary']} · News {n_by['Secondary']} · Community {n_by['Community']} · weighted")
        add("PYTHON", f"sorted {len(items)} sources · weights official 1.0 / news 0.7 / community 0.4")
        stage(2, "RUNNING")

        analysis = synthesize_threat_dossier(target_company, search_data, on_event=on_event)
        st.session_state.dossier_content = analysis
        if analysis.get("simulated"):
            run["sup"], run["con"] = len(analysis["supporting"]), 0
            stage(2, "DONE", "SIMULATED — no model was called")
            stage(3, "DONE", "SIMULATED — no counter-search was run")
            stage(4, "DONE", f"Score computed in Python · {analysis['confidence']['score']:g} · {ui.band5(analysis['confidence']['score'])[0]}")
        stage(5, "RUNNING")
        save_and_alert(target_company, search_data, analysis, run, add)
        stage(4, "DONE", f"Score computed in Python · {analysis['confidence']['score']:g} · {ui.band5(analysis['confidence']['score'])[0]}")
        run["done"] = True
        redraw()
    except Exception as e:  # PulseGridError or unexpected - show the real (redacted) message
        run["error"] = redact(e) if isinstance(e, PulseGridError) else f"{type(e).__name__}: {redact(e)}"
        for stg in run["stages"]:
            if stg["status"] == "RUNNING":
                stg["status"] = "FAILED"
        st.session_state.dossier_content = None
        redraw()


def save_and_alert(company: str, search_data: dict, analysis: dict, run: dict, add) -> None:
    """Track record + baseline + alert check. Failures here never break the investigation;
    each outcome is recorded in run_log for the actions screen."""
    log = st.session_state.run_log
    if SIMULATED:
        for label in ("Earlier predictions", "Prediction saved", "Baseline saved", "Alert check"):
            log.append({"label": label, "mark": "none", "text": "Skipped — simulation mode saves nothing"})
        run["stages"][5].update(status="DONE", detail="Skipped — simulation mode saves nothing")
        return
    slug = make_slug(company)

    # earlier predictions (before saving the new one)
    try:
        pending_n = min(3, sum(1 for r in tr.list_predictions(slug) if r.get("status") == "pending"))
        if pending_n:
            st.session_state.suggestions = tr.suggest_resolutions(
                company, slug, search_data, analysis,
                chat_json_for({"suggestions": list}, "resolution step"), _pool_text, _build_pool)
            m = len(st.session_state.suggestions)
            log.append({"label": "Earlier predictions", "mark": "ok",
                        "text": f"Checked {pending_n} pending · {m} may be resolved → review in Track record"})
            add("NEMOTRON", f"checked {pending_n} earlier predictions · {m} may be resolved")
        else:
            log.append({"label": "Earlier predictions", "mark": "ok", "text": "No pending predictions"})
    except Exception as e:
        st.session_state.track_error = f"Could not check earlier predictions: {redact(e)}"
        log.append({"label": "Earlier predictions", "mark": "fail", "text": f"Failed: {redact(e)}"})

    # prediction
    prev, pred_ok = None, False
    try:
        prev = tr.latest_confidence(slug)  # read BEFORE saving the new prediction
        tr.apply_history(analysis, confidence_label)
        st.session_state.saved_prediction = tr.save_prediction(company, slug, analysis)
        st.session_state.scan_n = len(tr.list_predictions(slug))
        h = analysis["confidence"].get("history") or {}
        log.append({"label": "Prediction saved", "mark": "ok", "text": f"Track record ({store.backend()}) · {h.get('message', '—')}"})
        if h.get("adjustment"):
            add("PYTHON", f"track record adjusted confidence {h['adjustment']:+g} → {analysis['confidence']['score']:g}")
        pred_ok = True
    except Exception as e:
        st.session_state.track_error = f"Could not save prediction: {redact(e)}"
        log.append({"label": "Prediction saved", "mark": "fail", "text": f"Failed: {redact(e)}"})

    # baseline (saved inside run_pulsegrid_search; report what happened)
    write_warn = [w for w in search_data.get("storage_warnings", []) if "write failed" in w]
    if write_warn:
        log.append({"label": "Baseline saved", "mark": "fail", "text": redact("; ".join(write_warn))})
    else:
        log.append({"label": "Baseline saved", "mark": "ok",
                    "text": f"scan_cache ({search_data['storage_backend']}) · next scan compares against this"})

    # alert check
    try:
        if not alerts.is_watched(slug):
            alert = {"mark": "none", "text": "Not watched — no alert check", "short": "not watched"}
        else:
            why: dict = {}
            al = alerts.evaluate(company, slug, analysis, search_data["diff"], prev,
                                 prefs=alerts.watchlist.first(company_slug=slug), explain=why)
            if not al:
                alert = {"mark": "none", "text": why.get("reason", "No trigger"), "short": "no trigger"}
            else:
                sent = alerts.send_if_new(al)
                if sent:
                    names = ", ".join("Slack" if c == "slack" else c for c in sent)
                    alert = {"mark": "ok", "text": f"Sent to {names}: " + "; ".join(al["reasons"]), "short": f"sent to {names}"}
                else:
                    alert = {"mark": "none", "text": "Skipped: already sent earlier", "short": "already sent"}
    except Exception as e:
        alert = {"mark": "fail", "text": f"Failed: {redact(e)}", "short": "alert failed"}
    log.append({"label": "Alert check", "mark": alert["mark"], "text": alert["text"]})
    add("PYTHON", f"alert check · {alert['text']}")
    base = "baseline not saved" if write_warn else "baseline saved"
    run["stages"][5].update(status="DONE" if pred_ok else "FAILED",
                            detail=f"{'Prediction saved' if pred_ok else 'Prediction not saved'} · {base} · {alert['short']}")


# ---------------------------------------------------------------- screens
def fill_company(name: str) -> None:
    st.session_state.company_input = name


def screen_investigate() -> None:
    with st.container(key="inv_col"):
        ui.render(ui.investigate_top_html(tavily_client is not None, nebius_client is not None, NEBIUS_MODEL, SIMULATED))
        with st.form("investigate", border=False):
            c_in, c_btn = st.columns([4, 1.3], vertical_alignment="bottom")
            company = c_in.text_input("Company", key="company_input", placeholder="Company to investigate, e.g. Databricks",
                                      max_chars=60, label_visibility="collapsed")
            submitted = c_btn.form_submit_button("Investigate", type="primary", use_container_width=True)
        if submitted and company.strip() and start_investigation(company):
            st.rerun()
        if st.session_state.form_error:
            st.error(st.session_state.form_error)
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            ui.render('<span class="try">Try:</span>')
            for name in ("Databricks", "Figma", "Notion"):
                st.button(name, key=f"chip_{name}", on_click=fill_company, args=(name,))
        if has_results():
            st.button(f"← Back to results · {st.session_state.active_company}", key="back_to_results",
                      type="tertiary", on_click=go, args=("results",))
        ui.render(ui.spacer(20))
        ui.render(ui.pillars_html())
        ui.render(ui.footer_html())


def screen_thinking() -> None:
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        left_ph = st.empty()
    with right:
        right_ph = st.empty()
    pending = st.session_state.pending_company
    if pending:
        st.session_state.pending_company = None
        with right:
            wait_ph = st.empty()
            wait_ph.caption("Appears when the verdict is ready")
        execute(pending, left_ph, right_ph)
        wait_ph.empty()
    run = st.session_state.get("run")
    if not run:
        go("investigate")
        st.rerun()
    ui.render(ui.thinking_left_html(run), left_ph)
    ui.render(ui.kolam_panel_html(run), right_ph)
    if run["error"]:
        with left:
            st.error(f"Live API call failed — no data was faked.\n\n{run['error']}")
            st.button("Try again", key="try_again", type="primary", on_click=go, args=("investigate",))
    elif run["done"] and has_results():
        with right:
            st.button("See results · परिणाम Parinaam →", key="see_results", type="primary",
                      use_container_width=True, on_click=go, args=("results",))
            st.caption("Appears when the verdict is ready")


def screen_results() -> None:
    d = st.session_state.dossier_content
    sd = st.session_state.search_data
    ui.render(ui.results_status_html(d, sd, st.session_state.scan_n))
    for w in sd.get("storage_warnings", []):
        st.warning(w)
    ui.render(ui.hero_html(d))
    ui.render(ui.spacer(28))
    ui.render(ui.evidence_columns_html(d))
    ui.render(ui.spacer(12))
    ui.render(ui.why_html(d))
    ui.render(ui.spacer(20))
    t_score, t_self, t_chg, t_src, t_how = st.tabs(["Score breakdown", "Self-challenge log", "What changed", "All sources", "How it ran"])
    with t_score:
        ui.render(ui.score_tab_html(d))
    with t_self:
        ui.render(ui.selfchallenge_log_html(d))
    with t_chg:
        ui.render(ui.changes_html(sd))
    with t_src:
        ui.render(ui.sources_html(sd))
    with t_how:
        run = st.session_state.get("run") or {}
        ui.render(ui.how_it_ran_html(d, sd, run.get("events")))
    ui.render(ui.spacer(20))
    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        st.button("← Back to the pattern", type="tertiary", on_click=go, args=("thinking",))
        st.button("See recommended actions →", type="primary", on_click=go, args=("actions",))


def screen_actions() -> None:
    d = st.session_state.dossier_content
    sd = st.session_state.search_data
    ui.render(ui.actions_head_html(d))
    ui.render(ui.rec_cards_html(d))
    ui.render(ui.spacer(24))
    c_log, c_keep = st.columns([3, 2], gap="large")
    with c_log:
        ui.render(ui.after_analysis_html(st.session_state.run_log))
    with c_keep:
        ui.render('<div class="lab">Keep an eye on it</div>')
        slug_now = make_slug(st.session_state.active_company)
        watched = False
        try:
            watched = alerts.is_watched(slug_now)
        except Exception as e:
            st.warning(f"Watchlist unavailable: {redact(e)}")
        if watched:
            if st.button("Stop watching", key="unwatch", type="primary", use_container_width=True):
                alerts.unwatch(slug_now)
                st.rerun()
        elif st.button("Watch this company", key="watch", type="primary", use_container_width=True,
                       disabled=d.get("simulated", False)):
            try:
                alerts.watch(slug_now, st.session_state.active_company)
                st.rerun()
            except Exception as e:
                st.error(f"Could not save to watchlist: {redact(e)}")
        st.download_button("Download report", key="dl_report", data=dossier_to_markdown(d, sd["delta_highlights"]),
                           file_name=f"{re.sub(r'[^a-z0-9]+', '_', st.session_state.active_company.lower())}_pulsegrid.md",
                           mime="text/markdown", use_container_width=True)
        st.button("New investigation", key="new_inv", use_container_width=True, on_click=go, args=("investigate",))
        st.caption("Alerts fire on rescans (manual or daily), not in real time.")
    ui.render(ui.spacer(16))
    st.button("← Back to results", key="back_results", type="tertiary", on_click=go, args=("results",))
    ui.render(ui.kolam_footer_html())


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
if screen == "splash":  # first load of a session only; the overlay fades itself out after 2s
    ui.render(ui.splash_html())
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
