"""
watch_runner.py
===============
Headless rescan of the watchlist, sending alerts when something changed.
Run by .github/workflows/watch.yml once a day (or manually: python watch_runner.py).

Alerts fire on rescans only - this is not real-time monitoring.
Needs Supabase: without it there is no stored previous scan to compare against, so the
runner refuses to run (pass --allow-local only for local testing).
"""

import sys

import alerts
import store
import track_record as tr
from ai_engine import synthesize_threat_dossier, confidence_label
from config import simulation_enabled, redact
from search_engine import run_pulsegrid_search, make_slug, PulseGridError


def scan_one(row) -> str:
    name, slug = row["company_name"], row["company_slug"] or make_slug(row["company_name"])
    prev = tr.latest_confidence(slug)   # read BEFORE saving the new prediction
    sd = run_pulsegrid_search(name)
    analysis = synthesize_threat_dossier(name, sd)
    tr.apply_history(analysis, confidence_label)
    alert = alerts.evaluate(name, slug, analysis, sd["diff"], prev, prefs=row)
    tr.save_prediction(name, slug, analysis)
    if not alert:
        return f"{name}: scanned, nothing to alert ({analysis['confidence']['score']}%)"
    sent = alerts.send_if_new(alert)
    return f"{name}: alert {'sent via ' + ', '.join(sent) if sent else 'already sent earlier (skipped)'}"


def main() -> int:
    if simulation_enabled():
        print("DEMO_SIMULATION is on; refusing to send alerts from simulated data.")
        return 2
    if store.backend() != "supabase" and "--allow-local" not in sys.argv:
        print("Supabase is not configured: no stored previous scan, so alerts would be meaningless. Set SUPABASE_URL/SUPABASE_KEY.")
        return 2
    watched = alerts.list_watched()
    print(f"{len(watched)} watched; scanning at most {alerts.MAX_WATCH_PER_RUN} (credit cap)")
    failures = 0
    for row in watched[:alerts.MAX_WATCH_PER_RUN]:
        try:
            print(scan_one(row))
        except (PulseGridError, Exception) as e:   # one company failing must not stop the rest
            failures += 1
            print(f"{row.get('company_name')}: FAILED - {redact(e)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
