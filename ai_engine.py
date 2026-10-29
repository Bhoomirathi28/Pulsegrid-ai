"""
ai_engine.py
============
PulseGrid AI - Nebius Token Factory + NVIDIA Nemotron reasoning engine.

Pipeline (each step is a real call; nothing is fabricated):
  1. Nemotron: read numbered evidence, form ONE hypothesis + adversarial queries (JSON).
  2. Tavily: adversarial "prove me wrong" search with those queries.
  3. Nemotron: classify adversarial results as contradicting / neutral (JSON).
  4. Python: compute the confidence score from the evidence (no LLM-invented number).
  5. Nemotron: write summary, "Why not higher?" and recommendations (JSON, text only).

URLs are never taken from model output: the model refers to evidence IDs and
Python looks the URL up in the retrieved Tavily results.
"""

import json
import re
import concurrent.futures
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from openai import OpenAI

from config import (
    NEBIUS_API_KEY, NEBIUS_MODEL, NEBIUS_BASE_URL, is_placeholder, simulation_enabled,
)
from search_engine import tavily_search, normalize_results, PulseGridError

nebius_client: Optional[OpenAI] = None
if not is_placeholder(NEBIUS_API_KEY):
    try:
        nebius_client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=NEBIUS_API_KEY, timeout=120, max_retries=3)
    except Exception:
        nebius_client = None

SOURCE_WEIGHT = {"Primary": 1.0, "Secondary": 0.7, "Community": 0.4}

# (key, label, weight) - weights sum to 1.0 and are shown in the UI
CONFIDENCE_FACTORS = [
    ("support_share", "Weighted support vs contradiction", 0.35),
    ("volume", "Amount of supporting evidence", 0.20),
    ("quality", "Source quality (primary > secondary > community)", 0.20),
    ("diversity", "Coverage across the 4 streams", 0.10),
    ("recency", "Recency of supporting evidence", 0.15),
]


# ------------------------------------------------------------------ LLM plumbing
def _strip_to_json(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start:end + 1]
    return text


def _chat(messages: List[Dict[str, str]], max_tokens: int, meta: Dict[str, Any]) -> str:
    if nebius_client is None:
        raise PulseGridError("Nebius is not configured (NEBIUS_API_KEY missing or placeholder).")
    try:
        resp = nebius_client.chat.completions.create(
            model=NEBIUS_MODEL, messages=messages, temperature=0.2, max_tokens=max_tokens,
        )
    except Exception as e:
        raise PulseGridError(
            f"Nebius call failed for model '{NEBIUS_MODEL}': {e}. "
            "Run `python check_models.py` to list valid model IDs."
        )
    meta["nebius_calls_ok"] = meta.get("nebius_calls_ok", 0) + 1
    msg = resp.choices[0].message
    content = msg.content or getattr(msg, "reasoning_content", None) or ""
    if not content.strip():
        raise PulseGridError(f"Model '{NEBIUS_MODEL}' returned an empty response.")
    return content


def _chat_json(system: str, user: str, max_tokens: int, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Calls the model and parses JSON; one retry on invalid JSON."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    raw = _chat(messages, max_tokens, meta)
    try:
        return json.loads(_strip_to_json(raw))
    except ValueError:
        messages += [
            {"role": "assistant", "content": raw[:4000]},
            {"role": "user", "content": "That was not valid JSON. Reply again with ONLY the JSON object, no prose, no code fences."},
        ]
        raw2 = _chat(messages, max_tokens, meta)
        try:
            return json.loads(_strip_to_json(raw2))
        except ValueError as e:
            raise PulseGridError(f"Model returned invalid JSON twice: {e}. Last output: {raw2[:300]!r}")


# ------------------------------------------------------------------ evidence pool
def _build_pool(raw_streams: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    pool: Dict[str, Dict[str, Any]] = {}
    n = 0
    for s in raw_streams:
        for item in s.get("results", []):
            n += 1
            eid = f"E{n}"
            pool[eid] = {**item, "id": eid, "stream": s.get("category", "")}
    return pool


def _pool_text(pool: Dict[str, Dict[str, Any]]) -> str:
    lines = []
    for eid, it in pool.items():
        snippet = (it.get("snippet") or "").replace("\n", " ")[:450]
        lines.append(f"[{eid}] ({it.get('stream')} | {it.get('provenance')}) {it.get('title')}: {snippet}")
    return "\n".join(lines)


def _resolve(refs: Any, pool: Dict[str, Dict[str, Any]], stance: str) -> List[Dict[str, Any]]:
    """Maps model-cited evidence IDs back to retrieved results. Unknown IDs are dropped."""
    out, seen = [], set()
    for r in refs if isinstance(refs, list) else []:
        if not isinstance(r, dict):
            continue
        eid = str(r.get("evidence_id", "")).strip()
        src = pool.get(eid)
        if not src or eid in seen:
            continue
        seen.add(eid)
        out.append({
            "id": eid, "stance": stance, "claim": str(r.get("claim", "")).strip()[:400],
            "title": src["title"], "url": src["url"], "source_type": src.get("provenance", "Secondary"),
            "stream": src.get("stream", "Adversarial search"), "published_date": src.get("published_date"),
            "domain": urlparse(src["url"]).netloc.lower(),
        })
    return out


# ------------------------------------------------------------------ confidence (pure Python)
def _age_days(published: Optional[str]) -> Optional[float]:
    if not published:
        return None
    try:
        dt = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
    except ValueError:
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(str(published))
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400


def compute_confidence(supporting: List[Dict[str, Any]], contradicting: List[Dict[str, Any]],
                       adversarial_results_found: int) -> Dict[str, Any]:
    """Deterministic confidence score from evidence. Returns score, label and per-factor breakdown."""
    sup_w = sum(SOURCE_WEIGHT.get(e["source_type"], 0.7) for e in supporting)
    con_w = sum(SOURCE_WEIGHT.get(e["source_type"], 0.7) for e in contradicting)

    ages = [_age_days(e.get("published_date")) for e in supporting]
    dated = [a for a in ages if a is not None]
    if supporting:
        # undated items count as 0.4 (unknown), dated: 1.0 <=30d, 0.7 <=90d, 0.3 older
        rec_vals = [(1.0 if a <= 30 else 0.7 if a <= 90 else 0.3) if a is not None else 0.4 for a in ages]
        recency = sum(rec_vals) / len(rec_vals)
    else:
        recency = 0.0

    values = {
        "support_share": sup_w / (sup_w + con_w) if (sup_w + con_w) else 0.0,
        "volume": min(len(supporting), 6) / 6,
        "quality": (sup_w / len(supporting)) if supporting else 0.0,
        "diversity": len({e["stream"] for e in supporting}) / 4,
        "recency": recency,
    }
    notes = {
        "support_share": f"{len(supporting)} supporting vs {len(contradicting)} contradicting items (source-weighted)",
        "volume": f"{len(supporting)} supporting items (full marks at 6)",
        "quality": "Primary=1.0, Secondary=0.7, Community=0.4",
        "diversity": f"{len({e['stream'] for e in supporting})} of 4 streams",
        "recency": f"{len(dated)} of {len(supporting)} items have a publish date; undated count as 0.4",
    }
    breakdown = [{"key": k, "label": l, "weight": w, "value": round(values[k], 3),
                  "points": round(values[k] * w * 100, 1), "note": notes[k]}
                 for k, l, w in CONFIDENCE_FACTORS]
    score = sum(b["points"] for b in breakdown)

    caps = []
    if adversarial_results_found == 0:
        score = min(score, 60.0)
        caps.append("Capped at 60: the adversarial search returned no results, so the hypothesis was not meaningfully tested.")
    if not supporting:
        score = 0.0
    score = round(min(score, 95.0), 1)  # never claim near-certainty
    label = "High" if score >= 75 else "Moderate" if score >= 50 else "Low"
    return {"score": score, "label": label, "breakdown": breakdown, "caps": caps}


# ------------------------------------------------------------------ simulation
def _simulated_analysis(company_name: str, raw_streams: List[Dict[str, Any]]) -> Dict[str, Any]:
    pool = _build_pool(raw_streams)
    sup = _resolve([{"evidence_id": eid, "claim": "[SIMULATED] " + it["title"]} for eid, it in list(pool.items())[:4]], pool, "supporting")
    con = []
    conf = compute_confidence(sup, con, 0)
    return {
        "company": company_name, "simulated": True,
        "hypothesis": f"[SIMULATED] Evidence is consistent with {company_name} shifting toward enterprise customers.",
        "executive_summary": "[SIMULATED] No model was called.",
        "supporting": sup, "contradicting": con, "adversarial_queries": [], "adversarial_results": [],
        "confidence": conf, "why_not_higher": "[SIMULATED] No model was called.",
        "recommendations": ["[SIMULATED]"], "meta": {"model": "none (simulation)", "nebius_calls_ok": 0, "tavily_adversarial_ok": 0},
    }


# ------------------------------------------------------------------ main pipeline
SYSTEM_PROMPT = """You are PulseGrid AI, a competitive-intelligence analyst built on NVIDIA Nemotron.
Rules: use ONLY the numbered evidence given; cite evidence by its ID (e.g. "E3"); never write URLs.
Treat conclusions as hypotheses, not facts. Use wording like "the evidence is consistent with", never "definitely" or "proves".
Respond with ONLY a JSON object, no prose, no code fences."""


def synthesize_threat_dossier(company_name: str, search_data: Dict[str, Any]) -> Dict[str, Any]:
    """Runs the full reasoning pipeline. Raises PulseGridError on any failed live call."""
    raw_streams = search_data.get("raw_streams", [])
    if simulation_enabled():
        return _simulated_analysis(company_name, raw_streams)

    meta: Dict[str, Any] = {"model": NEBIUS_MODEL, "nebius_calls_ok": 0, "tavily_adversarial_ok": 0}
    pool = _build_pool(raw_streams)
    if not pool:
        raise PulseGridError("Tavily returned no usable results for any stream; nothing to analyse.")

    # Step 1: hypothesis
    p1 = f"""Company: {company_name}

EVIDENCE:
{_pool_text(pool)}

Form exactly ONE strategic hypothesis about {company_name}'s direction that the evidence is consistent with,
list the evidence that supports it, and write 2 short keyword-style web search queries (under 12 words, not questions) that would surface evidence AGAINST the hypothesis.
JSON schema:
{{"hypothesis": "one sentence", "supporting": [{{"evidence_id": "E1", "claim": "what this item shows"}}], "counter_queries": ["...", "..."]}}"""
    h = _chat_json(SYSTEM_PROMPT, p1, 2000, meta)
    hypothesis = str(h.get("hypothesis", "")).strip()
    if not hypothesis:
        raise PulseGridError("Model returned no hypothesis.")
    supporting = _resolve(h.get("supporting"), pool, "supporting")
    queries = [str(q).strip() for q in (h.get("counter_queries") or []) if str(q).strip()][:2]
    if not queries:
        queries = [f"{company_name} evidence against: {hypothesis}"[:300]]
    queries = [q if company_name.lower() in q.lower() else f"{company_name} {q}" for q in queries]

    # Step 2: adversarial Tavily search (parallel)
    adv_pool: Dict[str, Dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(queries)) as ex:
        responses = list(ex.map(lambda q: tavily_search(q, max_results=4), queries))
    meta["tavily_adversarial_ok"] = len(responses)
    seen_urls = set()
    for resp in responses:
        for item in normalize_results(resp, company_name):
            if item["url"] in seen_urls:
                continue
            seen_urls.add(item["url"])
            aid = f"A{len(adv_pool) + 1}"
            adv_pool[aid] = {**item, "id": aid, "stream": "Adversarial search"}

    # Step 3: classify adversarial results
    contradicting: List[Dict[str, Any]] = []
    if adv_pool:
        p3 = f"""Company: {company_name}
HYPOTHESIS: {hypothesis}

ADVERSARIAL SEARCH RESULTS (searched specifically to disprove the hypothesis):
{_pool_text(adv_pool)}

Which of these items genuinely contradict or weaken the hypothesis? Only include items that really do; omit irrelevant ones.
JSON schema:
{{"contradicting": [{{"evidence_id": "A1", "claim": "how it contradicts"}}], "alternative_explanation": "one sentence or empty"}}"""
        c = _chat_json(SYSTEM_PROMPT, p3, 1500, meta)
        contradicting = _resolve(c.get("contradicting"), adv_pool, "contradicting")
        alt = str(c.get("alternative_explanation", "")).strip()
    else:
        alt = ""

    # Step 4: confidence computed in Python
    confidence = compute_confidence(supporting, contradicting, len(adv_pool))

    # Step 5: text only - the model sees the computed score and may not change it
    p5 = f"""Company: {company_name}
HYPOTHESIS: {hypothesis}
SUPPORTING: {json.dumps([{"id": e["id"], "claim": e["claim"], "source_type": e["source_type"]} for e in supporting])}
CONTRADICTING: {json.dumps([{"id": e["id"], "claim": e["claim"], "source_type": e["source_type"]} for e in contradicting])}
ALTERNATIVE EXPLANATION: {alt or "none given"}
COMPUTED CONFIDENCE (fixed, do not change): {confidence['score']}% ({confidence['label']})
FACTORS: {json.dumps([{"factor": b["label"], "value": b["value"], "note": b["note"]} for b in confidence["breakdown"]])}
CAPS: {confidence['caps'] or 'none'}

Write: a 2-3 sentence executive summary; a "Why not higher?" explanation (2-4 sentences) grounded in the weak factors above and the contradicting evidence; and 3 concrete recommendations for a competitor of {company_name}.
Do not state a different confidence number. Keep hypothesis-style wording.
JSON schema:
{{"executive_summary": "...", "why_not_higher": "...", "recommendations": ["...", "...", "..."]}}"""
    t = _chat_json(SYSTEM_PROMPT, p5, 1500, meta)

    return {
        "company": company_name, "simulated": False, "hypothesis": hypothesis,
        "executive_summary": str(t.get("executive_summary", "")).strip(),
        "supporting": supporting, "contradicting": contradicting,
        "adversarial_queries": queries,
        "adversarial_results": [{"id": k, "title": v["title"], "url": v["url"], "source_type": v["provenance"]} for k, v in adv_pool.items()],
        "alternative_explanation": alt, "confidence": confidence,
        "why_not_higher": str(t.get("why_not_higher", "")).strip(),
        "recommendations": [str(r) for r in (t.get("recommendations") or [])][:5],
        "meta": meta,
    }


def dossier_to_markdown(d: Dict[str, Any], delta_highlights: List[str]) -> str:
    """Markdown export of the structured analysis."""
    banner = "> **SIMULATED DATA — NOT LIVE**\n\n" if d.get("simulated") else ""
    def ev(items):
        return "\n".join(f"- [{e['source_type']}] {e['claim']} — [{e['title']}]({e['url']})" for e in items) or "- None found"
    c = d["confidence"]
    rows = "\n".join(f"| {b['label']} | {int(b['weight']*100)}% | {b['value']:.2f} | {b['points']} |" for b in c["breakdown"])
    return f"""{banner}# Threat Dossier: {d['company']}

## Summary
{d['executive_summary']}

## HYPOTHESIS — NOT FACT
{d['hypothesis']}

## Supporting evidence
{ev(d['supporting'])}

## Contradicting evidence (adversarial search)
{ev(d['contradicting'])}

## Confidence: {c['score']}% ({c['label']}) — computed from evidence
| Factor | Weight | Value | Points |
|---|---|---|---|
{rows}

**Why not higher?** {d['why_not_higher']}

## Recommendations
{chr(10).join(f"{i}. {r}" for i, r in enumerate(d['recommendations'], 1))}

## Changes since last scan
{chr(10).join(f"- {h}" for h in delta_highlights)}
"""
