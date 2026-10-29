"""
track_record.py
===============
स्मृति SMRITI - every hypothesis is saved as a prediction and can later be marked
confirmed / refuted (by the user, optionally from a model suggestion that must cite a
real retrieved URL). Pending predictions expire after 90 days.

Learning rule (pure Python): once a (pattern_signature, industry) group has >= 5
resolved predictions, new confidence for that group moves toward the group's hit rate
by at most 10 points. Below 5 resolved, nothing is adjusted. No seeded history.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from store import Table, now_iso
from search_engine import is_valid_url, PulseGridError

INDUSTRIES = ["SaaS", "devtools", "AI model provider", "hardware", "fintech", "consumer", "other"]
STATUSES = ["pending", "confirmed", "refuted", "expired"]
MIN_RESOLVED = 5
MAX_ADJUST = 10.0
EXPIRY_DAYS = 90

# stream category -> signal type used in the pattern signature
SIGNAL_TYPES = {"Talent": "hiring", "Product": "product_change",
                "Customer Friction": "customer_friction", "Market": "market_news"}

predictions = Table("predictions")


def signal_type(stream: str) -> Optional[str]:
    for key, val in SIGNAL_TYPES.items():
        if stream.startswith(key):
            return val
    return None


def pattern_signature(analysis: Dict[str, Any]) -> List[str]:
    """Sorted signal types of the supporting evidence that formed the hypothesis."""
    return sorted({t for t in (signal_type(e.get("stream", "")) for e in analysis.get("supporting", [])) if t})


def normalize_industry(label: Any) -> str:
    s = str(label or "").strip().lower()
    for ind in INDUSTRIES:
        if s == ind.lower():
            return ind
    return "other"


def _parse_time(s: Any) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def expire_old(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=EXPIRY_DAYS)
    for r in rows:
        created = _parse_time(r.get("created_at"))
        if r.get("status") == "pending" and created and created < cutoff:
            fields = {"status": "expired", "resolved_at": now_iso(),
                      "resolution_note": f"No outcome recorded within {EXPIRY_DAYS} days."}
            predictions.update(r["id"], fields)
            r.update(fields)
    return rows


def list_predictions(company_slug: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = predictions.select(company_slug=company_slug) if company_slug else predictions.select()
    rows = expire_old(rows)
    return sorted(rows, key=lambda r: str(r.get("created_at", "")), reverse=True)


def _group_key(pattern: Any, industry: str) -> str:
    return json.dumps(sorted(pattern or [])) + "|" + industry


def latest_confidence(company_slug: str) -> Optional[Dict[str, Any]]:
    """Confidence of the most recent saved prediction for a company (read BEFORE saving the new one)."""
    rows = list_predictions(company_slug)
    return {"confidence": rows[0]["confidence"]} if rows and rows[0].get("confidence") is not None else None


def pattern_stats(rows: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    rows = list_predictions() if rows is None else rows
    groups: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        k = _group_key(r.get("pattern_signature"), r.get("industry", "other"))
        g = groups.setdefault(k, {"pattern": sorted(r.get("pattern_signature") or []), "industry": r.get("industry", "other"),
                                  "confirmed": 0, "refuted": 0, "pending": 0, "expired": 0})
        g[r.get("status", "pending")] = g.get(r.get("status", "pending"), 0) + 1
    out = []
    for g in groups.values():
        g["resolved"] = g["confirmed"] + g["refuted"]
        g["hit_rate"] = round(g["confirmed"] / g["resolved"], 3) if g["resolved"] else None
        out.append(g)
    return sorted(out, key=lambda g: (-g["resolved"], -g["pending"]))


def history_adjustment(pattern: List[str], industry: str, score: float,
                       rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """How past resolved predictions with the same pattern+industry adjust this score."""
    rows = list_predictions() if rows is None else rows
    k = _group_key(pattern, industry)
    resolved = [r for r in rows if _group_key(r.get("pattern_signature"), r.get("industry", "other")) == k
                and r.get("status") in ("confirmed", "refuted")]
    n = len(resolved)
    if n < MIN_RESOLVED:
        return {"n": n, "adjustment": 0.0, "hit_rate": None,
                "message": f"Not enough history yet ({n}/{MIN_RESOLVED}) for this pattern."}
    hit = sum(r["status"] == "confirmed" for r in resolved) / n
    adj = round(max(-MAX_ADJUST, min(MAX_ADJUST, hit * 100 - score)), 1)
    return {"n": n, "adjustment": adj, "hit_rate": round(hit, 3),
            "message": f"Adjusted {adj:+g} based on {n} past predictions with this pattern ({hit:.0%} confirmed)."}


def apply_history(analysis: Dict[str, Any], label_fn) -> None:
    """Adds pattern/industry and applies the learning rule to analysis['confidence'] in place."""
    conf = analysis["confidence"]
    pattern = pattern_signature(analysis)
    industry = normalize_industry(analysis.get("industry"))
    h = history_adjustment(pattern, industry, conf["score"])
    conf["base_score"] = conf["score"]
    if h["adjustment"]:
        conf["score"] = round(max(0.0, min(95.0, conf["score"] + h["adjustment"])), 1)
        conf["label"] = label_fn(conf["score"])
    conf["history"] = h
    analysis["pattern_signature"] = pattern
    analysis["industry"] = industry


def save_prediction(company_name: str, company_slug: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    conf = analysis["confidence"]
    return predictions.insert({
        "company_slug": company_slug, "company_name": company_name,
        "industry": analysis.get("industry", "other"),
        "hypothesis": analysis["hypothesis"],
        "pattern_signature": analysis.get("pattern_signature", []),
        "confidence": conf["score"],
        "factors": {"breakdown": conf["breakdown"], "caps": conf["caps"],
                    "base_score": conf.get("base_score"), "history": conf.get("history")},
        "status": "pending", "resolved_at": None, "resolution_url": None, "resolution_note": None,
    })


def resolve(prediction_id: str, status: str, url: str = "", note: str = "") -> None:
    if status not in ("confirmed", "refuted", "pending"):
        raise PulseGridError(f"Invalid status: {status}")
    url = (url or "").strip()
    if url and not is_valid_url(url):
        raise PulseGridError("Resolution URL must start with http:// or https://")
    predictions.update(prediction_id, {
        "status": status,
        "resolved_at": None if status == "pending" else now_iso(),
        "resolution_url": url or None, "resolution_note": (note or "").strip()[:500] or None,
    })


def suggest_resolutions(company_name: str, company_slug: str, search_data: Dict[str, Any],
                        analysis: Dict[str, Any], chat_json, pool_text, build_pool) -> List[Dict[str, Any]]:
    """On a rescan, asks Nemotron whether new evidence confirms/refutes earlier pending
    predictions. A suggestion is kept only if it cites a real retrieved result; the user
    still has to accept it."""
    pending = [r for r in list_predictions(company_slug) if r.get("status") == "pending"][:3]
    if not pending:
        return []
    pool = build_pool(search_data.get("raw_streams", []))
    for a in analysis.get("adversarial_results", []):
        pool[a["id"]] = {"title": a["title"], "url": a["url"], "snippet": "", "provenance": a.get("source_type"),
                         "stream": "Adversarial search"}
    preds = "\n".join(f'[P{i + 1}] ({str(r.get("created_at", ""))[:10]}) {r["hypothesis"]}' for i, r in enumerate(pending))
    prompt = f"""Company: {company_name}
EARLIER PREDICTIONS (hypotheses made in previous scans):
{preds}

NEW EVIDENCE:
{pool_text(pool)}

For each earlier prediction, does the new evidence clearly CONFIRM it, clearly REFUTE it, or neither?
Only answer confirmed/refuted if one specific evidence item directly shows it; otherwise "none".
JSON schema:
{{"suggestions": [{{"prediction": "P1", "suggestion": "confirmed|refuted|none", "evidence_id": "E3", "reason": "one sentence"}}]}}"""
    meta: Dict[str, Any] = {}
    out = chat_json(prompt, meta)
    results = []
    for s in out.get("suggestions", []) if isinstance(out.get("suggestions"), list) else []:
        if not isinstance(s, dict):
            continue
        label = str(s.get("suggestion", "")).strip().lower()
        pid = str(s.get("prediction", "")).strip().upper()
        eid = str(s.get("evidence_id", "")).strip()
        if label not in ("confirmed", "refuted") or not pid.startswith("P") or eid not in pool:
            continue
        try:
            row = pending[int(pid[1:]) - 1]
        except (ValueError, IndexError):
            continue
        results.append({"prediction_id": row["id"], "hypothesis": row["hypothesis"], "suggestion": label,
                        "url": pool[eid]["url"], "title": pool[eid]["title"],
                        "reason": str(s.get("reason", "")).strip()[:300]})
    analysis["meta"]["nebius_calls_ok"] = analysis["meta"].get("nebius_calls_ok", 0) + meta.get("nebius_calls_ok", 0)
    return results
