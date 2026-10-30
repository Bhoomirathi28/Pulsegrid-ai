"""
alerts.py
=========
Watchlist + alerts. Alerts fire when a company is RESCANNED (manually in the app, or by
the daily watch_runner.py GitHub Action) - never in real time.

Triggers (all computed in Python from real scan data):
  * confidence moved by >= CONF_MOVE points, or crossed a band (Low / Moderate / High)
  * new source(s) appeared whose source weight (Primary 1.0 / Secondary 0.7 / Community 0.4)
    is >= NEW_SIGNAL_MIN_WEIGHT
  * a prediction was resolved
The same alert is never sent twice (alert_log dedupe key).
"""

import hashlib
import json
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

import requests

from config import (SLACK_WEBHOOK_URL, APP_URL, SMTP_HOST, SMTP_PORT, SMTP_USER,
                    SMTP_PASSWORD, ALERT_EMAIL_TO, redact, is_placeholder)
from store import Table
from search_engine import PulseGridError, is_valid_url

CONF_MOVE = 10.0
NEW_SIGNAL_MIN_WEIGHT = 0.7
SOURCE_WEIGHT = {"Primary": 1.0, "Secondary": 0.7, "Community": 0.4}
MAX_WATCH_PER_RUN = 5

watchlist = Table("watchlist")
alert_log = Table("alert_log")


# ------------------------------------------------------------------ watchlist
def watch(company_slug: str, company_name: str) -> Dict[str, Any]:
    existing = watchlist.first(company_slug=company_slug)
    if existing:
        return existing
    return watchlist.insert({"company_slug": company_slug, "company_name": company_name,
                             "conf_move": CONF_MOVE, "min_weight": NEW_SIGNAL_MIN_WEIGHT, "active": True})


def unwatch(company_slug: str) -> None:
    for r in watchlist.select(company_slug=company_slug):
        watchlist.delete(r["id"])


def is_watched(company_slug: str) -> bool:
    return watchlist.first(company_slug=company_slug) is not None


def list_watched() -> List[Dict[str, Any]]:
    return [r for r in watchlist.select() if r.get("active", True)]


# ------------------------------------------------------------------ channels
def slack_configured() -> bool:
    return not is_placeholder(SLACK_WEBHOOK_URL) and SLACK_WEBHOOK_URL.startswith("https://hooks.slack.com/")


def email_configured() -> bool:
    return all(not is_placeholder(v) for v in (SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO))


def mrkdwn(text: Any) -> str:
    """Slack requires & < > to be escaped in message text."""
    return str(text if text is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _slack_link(url: str, text: str) -> str:
    return f"<{url}|{mrkdwn(text)}>" if is_valid_url(url) and "|" not in url and ">" not in url else mrkdwn(text)


def build_blocks(alert: Dict[str, Any], test: bool = False) -> List[Dict[str, Any]]:
    title = f"{'[TEST] ' if test else ''}PulseGrid alert: {alert['company']}"
    blocks: List[Dict[str, Any]] = [
        {"type": "header", "text": {"type": "plain_text", "text": title[:150]}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(f"• {mrkdwn(r)}" for r in alert["reasons"])[:2900]}},
    ]
    if alert.get("confidence"):
        c = alert["confidence"]
        old = "first scan" if c.get("old") is None else f"{c['old']:g}% ({mrkdwn(c['old_band'])})"
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
                       "text": f"*Confidence:* {old} → {c['new']:g}% ({mrkdwn(c['new_band'])})"}})
    if alert.get("top_evidence"):
        lines = [f"• {_slack_link(e['url'], e['claim'] or e['title'])} _({mrkdwn(e['source_type'])})_" for e in alert["top_evidence"]]
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*Top evidence*\n" + "\n".join(lines)[:2900]}})
    foot = "Alerts fire on rescans, not in real time."
    if is_valid_url(APP_URL):
        foot += f" <{APP_URL}|Open PulseGrid>"
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": foot}]})
    return blocks


def send_slack(alert: Dict[str, Any], test: bool = False) -> None:
    if not slack_configured():
        raise PulseGridError("Slack is not configured (set SLACK_WEBHOOK_URL to an https://hooks.slack.com/ webhook).")
    try:
        r = requests.post(SLACK_WEBHOOK_URL, json={"text": f"PulseGrid alert: {alert['company']}", "blocks": build_blocks(alert, test)}, timeout=15)
    except requests.RequestException as e:
        raise PulseGridError(f"Slack request failed: {redact(e)}")
    if r.status_code != 200:
        raise PulseGridError(f"Slack returned HTTP {r.status_code}: {redact(r.text[:200])}")


def send_email(alert: Dict[str, Any], test: bool = False) -> None:
    if not email_configured():
        raise PulseGridError("Email is not configured (SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO).")
    msg = EmailMessage()
    msg["Subject"] = f"{'[TEST] ' if test else ''}PulseGrid alert: {alert['company']}"
    msg["From"], msg["To"] = SMTP_USER, ALERT_EMAIL_TO
    body = "\n".join(f"- {r}" for r in alert["reasons"])
    for e in alert.get("top_evidence", []):
        body += f"\n* {e['claim'] or e['title']} ({e['url']})"
    msg.set_content(body + "\n\nAlerts fire on rescans, not in real time.")
    try:
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT or 587), timeout=20) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.send_message(msg)
    except Exception as e:
        raise PulseGridError(f"Email failed: {redact(e)}")


def deliver(alert: Dict[str, Any], test: bool = False) -> List[str]:
    """Sends to every configured channel; returns the channels used. Raises if none is configured."""
    sent, errors = [], []
    for name, ok, fn in (("slack", slack_configured(), send_slack), ("email", email_configured(), send_email)):
        if ok:
            try:
                fn(alert, test)
                sent.append(name)
            except PulseGridError as e:
                errors.append(str(e))
    if not sent:
        raise PulseGridError("; ".join(errors) or "No alert channel is configured (set SLACK_WEBHOOK_URL).")
    return sent


def test_alert(company: str = "Test company") -> List[str]:
    alert = {"company": company, "reasons": ["This is a TEST message from PulseGrid. No real change was detected."],
             "confidence": None, "top_evidence": []}
    return deliver(alert, test=True)


# ------------------------------------------------------------------ triggers
def band(label_or_score: Any) -> str:
    if isinstance(label_or_score, str):
        return label_or_score
    return "High" if label_or_score >= 75 else "Moderate" if label_or_score >= 50 else "Low"


def dedupe_key(slug: str, kind: str, detail: Any) -> str:
    return hashlib.sha1(f"{slug}|{kind}|{json.dumps(detail, sort_keys=True, default=str)}".encode()).hexdigest()


def top_evidence(analysis: Dict[str, Any], n: int = 3) -> List[Dict[str, Any]]:
    ranked = sorted(analysis.get("supporting", []), key=lambda e: -SOURCE_WEIGHT.get(e.get("source_type"), 0.7))
    return [{"claim": e.get("claim", ""), "title": e.get("title", ""), "url": e["url"], "source_type": e.get("source_type", "")} for e in ranked[:n]]


def evaluate(company_name: str, slug: str, analysis: Dict[str, Any], diff: Dict[str, Any],
             prev: Optional[Dict[str, Any]], prefs: Optional[Dict[str, Any]] = None,
             explain: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Returns an alert dict if any trigger fires, else None. `prev` = {'confidence': float} from the previous scan.
    If `explain` is a dict and nothing fires, explain['reason'] says why (for the UI)."""
    prefs = prefs or {}
    move = float(prefs.get("conf_move", CONF_MOVE))
    min_w = float(prefs.get("min_weight", NEW_SIGNAL_MIN_WEIGHT))
    new_score = analysis["confidence"]["score"]
    new_band = analysis["confidence"]["label"]
    reasons, keys, conf = [], [], None

    if prev and prev.get("confidence") is not None:
        old = float(prev["confidence"])
        crossed = band(old) != band(new_score)
        if abs(new_score - old) >= move or crossed:
            why = f"Confidence moved {new_score - old:+.1f} points" + (f" and crossed from {band(old)} to {new_band}" if crossed else "")
            reasons.append(why)
            keys.append(("confidence", [round(old), round(new_score)]))
            conf = {"old": old, "new": new_score, "old_band": band(old), "new_band": new_band}

    if not diff.get("first_scan"):
        heavy = [n for n in diff.get("new_signals", []) if SOURCE_WEIGHT.get(n.get("provenance"), 0.7) >= min_w]
        if heavy:
            reasons.append(f"{len(heavy)} new source(s) with weight ≥ {min_w:g}: " + "; ".join(n["title"] for n in heavy[:3]))
            keys.append(("new_signals", sorted(n["url"] for n in heavy)))

    if not reasons:
        if explain is not None:
            if prev and prev.get("confidence") is not None:
                conf_txt = f"confidence {new_score - float(prev['confidence']):+.1f}"
            else:
                conf_txt = "no earlier confidence to compare"
            if diff.get("first_scan"):
                src_txt = "no earlier snapshot to compare sources"
            elif min_w == NEW_SIGNAL_MIN_WEIGHT:
                src_txt = "no new official/news sources"
            else:
                src_txt = f"no new sources with weight ≥ {min_w:g}"
            explain["reason"] = f"No trigger: {conf_txt}, {src_txt}"
        return None
    if conf is None:
        conf = {"old": prev.get("confidence") if prev else None, "new": new_score,
                "old_band": band(prev["confidence"]) if prev and prev.get("confidence") is not None else "", "new_band": new_band}
    return {"company": company_name, "slug": slug, "reasons": reasons, "confidence": conf,
            "top_evidence": top_evidence(analysis), "keys": [dedupe_key(slug, k, d) for k, d in keys]}


def resolution_alert(company_name: str, slug: str, prediction: Dict[str, Any], status: str, url: str = "") -> Dict[str, Any]:
    ev = [{"claim": "Resolution source", "title": url, "url": url, "source_type": ""}] if is_valid_url(url) else []
    return {"company": company_name, "slug": slug,
            "reasons": [f"A prediction was marked {status.upper()}: {prediction.get('hypothesis', '')}"],
            "confidence": None, "top_evidence": ev, "keys": [dedupe_key(slug, "resolved", [prediction.get("id"), status])]}


def send_if_new(alert: Dict[str, Any]) -> Optional[List[str]]:
    """Sends the alert unless every one of its trigger keys was already sent. Logs only after delivery."""
    fresh = [k for k in alert["keys"] if not alert_log.first(dedupe_key=k)]
    if not fresh:
        return None
    sent = deliver(alert)
    for k in fresh:
        alert_log.insert({"company_slug": alert["slug"], "dedupe_key": k, "channels": sent})
    return sent
