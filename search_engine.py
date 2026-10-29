"""
search_engine.py
================
PulseGrid AI - Autonomous Competitive Intelligence Agent
4-stream parallel Tavily search, source provenance classification,
and snapshot diffing (Supabase with local JSON fallback).

No fabricated data: failures raise PulseGridError. Mock data is only used
when DEMO_SIMULATION=true is set explicitly.
"""

import json
import os
import time
import concurrent.futures
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional, Tuple

from tavily import TavilyClient

from config import (
    TAVILY_API_KEY, SUPABASE_URL, SUPABASE_KEY, is_placeholder, simulation_enabled,
)

LOCAL_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pulsegrid_cache.json")
TAVILY_TIMEOUT = 40
TAVILY_ATTEMPTS = 3

STREAMS = [
    ("Talent & Hiring Signals", "hiring jobs careers R&D engineer hiring surge"),
    ("Product & Pricing Drift", "pricing plans API documentation changelog updates"),
    ("Customer Friction & Complaints", "reddit hacker news issue complaint outage feedback"),
    ("Market & News Signals", "funding acquisition launch partnership press release"),
]


class PulseGridError(Exception):
    """A live API call failed. Message is safe to show in the UI."""


# ------------------------------------------------------------------ clients
tavily_client: Optional[TavilyClient] = None
if not is_placeholder(TAVILY_API_KEY):
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception:
        tavily_client = None

supabase_client = None
if not is_placeholder(SUPABASE_URL) and not is_placeholder(SUPABASE_KEY):
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase_client = None


# ------------------------------------------------------------------ helpers
def classify_source_type(url: str, company_name: str) -> str:
    """Classifies source URLs into Primary, Secondary, or Community evidence."""
    try:
        domain = urlparse(url).netloc.lower()
        company_clean = "".join(ch for ch in company_name.lower() if ch.isalnum())

        community_domains = ["reddit.com", "news.ycombinator.com", "twitter.com", "x.com", "discord.com", "medium.com"]
        if any(k in domain for k in community_domains):
            return "Community"
        elif (company_clean and company_clean in domain.replace("-", "")) or any(
            domain.startswith(k) for k in ["docs.", "blog.", "status.", "careers.", "api."]
        ):
            return "Primary"
        return "Secondary"
    except Exception:
        return "Secondary"


def is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def tavily_search(query: str, max_results: int = 5, topic: str = "general") -> Dict[str, Any]:
    """Tavily search with timeout and retries. Raises PulseGridError on failure."""
    if simulation_enabled():
        raise PulseGridError("tavily_search called while simulation is enabled")
    if tavily_client is None:
        raise PulseGridError("Tavily is not configured (TAVILY_API_KEY missing or placeholder).")
    last: Optional[Exception] = None
    for attempt in range(TAVILY_ATTEMPTS):
        try:
            return tavily_client.search(
                query=query[:395], search_depth="advanced", max_results=max_results,
                topic=topic, timeout=TAVILY_TIMEOUT,
            )
        except Exception as e:
            last = e
            msg = str(e).lower()
            if any(k in msg for k in ("401", "403", "unauthorized", "invalid api key", "forbidden")):
                break  # retrying won't help
            time.sleep(1.5 * (attempt + 1))
    raise PulseGridError(f"Tavily search failed for '{query[:60]}': {last}")


def normalize_results(response: Dict[str, Any], company_name: str) -> List[Dict[str, Any]]:
    items = []
    for r in response.get("results", []):
        url = r.get("url", "")
        if not is_valid_url(url):
            continue
        items.append({
            "title": r.get("title") or "Untitled",
            "url": url,
            "snippet": r.get("content", "") or "",
            "provenance": classify_source_type(url, company_name),
            "published_date": r.get("published_date"),
        })
    return items


# ------------------------------------------------------------------ simulation
def _generate_mock_results(company_name: str, category: str) -> List[Dict[str, Any]]:
    """Only used when DEMO_SIMULATION=true. URLs are fake."""
    c = company_name.strip().capitalize()
    cl = c.lower().replace(" ", "")
    if "Talent" in category:
        return [
            {"title": f"[SIMULATED] {c} Careers: Staff Inference Infrastructure Engineer",
             "url": f"https://careers.{cl}.com/jobs/staff-infra", "provenance": "Primary", "published_date": None,
             "snippet": "Scaling low-latency inference clusters. GPU kernel optimization and distributed scheduling required."},
            {"title": f"[SIMULATED] {c} adds enterprise infrastructure hires",
             "url": f"https://example.com/{cl}-headcount", "provenance": "Secondary", "published_date": None,
             "snippet": f"{c} reportedly added enterprise infrastructure specialists over the last two months."},
        ]
    if "Product" in category:
        return [
            {"title": f"[SIMULATED] {c} changelog: dedicated instances",
             "url": f"https://docs.{cl}.com/changelog/dedicated", "provenance": "Primary", "published_date": None,
             "snippet": "New dedicated tier with SLA, VPC peering and custom quotas."},
            {"title": f"[SIMULATED] {c} pricing update",
             "url": f"https://{cl}.com/pricing", "provenance": "Primary", "published_date": None,
             "snippet": "Usage-based overages now include burst smoothing for high-concurrency accounts."},
        ]
    if "Friction" in category:
        return [
            {"title": f"[SIMULATED] r/LocalLLaMA: latency during peak hours on {c}",
             "url": "https://reddit.com/r/LocalLLaMA/comments/simulated", "provenance": "Community", "published_date": None,
             "snippet": "Responses slower at US peak hours; speculation about capacity prioritisation."},
            {"title": f"[SIMULATED] HN: {c} API rate limits",
             "url": "https://news.ycombinator.com/item?id=0", "provenance": "Community", "published_date": None,
             "snippet": "Developers report tighter free-tier limits."},
        ]
    return [
        {"title": f"[SIMULATED] {c} announces enterprise partnership",
         "url": "https://example.com/simulated-partnership", "provenance": "Secondary", "published_date": None,
         "snippet": f"{c} announces multi-region deployment agreements."},
        {"title": f"[SIMULATED] {c} completes SOC 2 Type II",
         "url": "https://example.com/simulated-soc2", "provenance": "Secondary", "published_date": None,
         "snippet": f"{c} completes security certifications for regulated customers."},
    ]


def search_stream(company_name: str, category: str, query: str) -> Dict[str, Any]:
    """Executes a search for one intelligence stream. Raises PulseGridError on failure."""
    if simulation_enabled():
        return {"category": category, "query": query, "results": _generate_mock_results(company_name, category)}
    topic = "news" if category.startswith("Market") else "general"
    response = tavily_search(f"{company_name} {query}", max_results=5, topic=topic)
    return {"category": category, "query": f"{company_name} {query}",
            "results": normalize_results(response, company_name)}


# ------------------------------------------------------------------ snapshots
def _read_local_cache() -> Dict[str, Any]:
    try:
        with open(LOCAL_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError, OSError):
        return {}


def load_previous_snapshot(slug: str) -> Tuple[Optional[List[Dict[str, Any]]], str, Optional[str]]:
    """Returns (previous_streams or None, backend used, warning or None). Reads BEFORE any write."""
    warning = None
    if supabase_client:
        try:
            res = supabase_client.table("scan_cache").select("raw_streams").eq("company_slug", slug).execute()
            rows = res.data or []
            return (rows[0].get("raw_streams") if rows else None), "supabase", None
        except Exception as e:
            warning = f"Supabase read failed, using local cache: {e}"
    entry = _read_local_cache().get(slug)
    return (entry.get("raw_streams") if entry else None), "local", warning


def save_snapshot(slug: str, company_name: str, streams: List[Dict[str, Any]], backend: str) -> Optional[str]:
    """Saves the new snapshot. Always writes local copy; also Supabase when it is the active backend."""
    warning = None
    if backend == "supabase" and supabase_client:
        try:
            supabase_client.table("scan_cache").upsert(
                {"company_slug": slug, "company_name": company_name, "raw_streams": streams},
                on_conflict="company_slug",
            ).execute()
        except Exception as e:
            warning = f"Supabase write failed (saved locally only): {e}"
    try:
        cache = _read_local_cache()
        cache[slug] = {"company_slug": slug, "company_name": company_name, "raw_streams": streams}
        with open(LOCAL_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except OSError as e:
        warning = (warning + "; " if warning else "") + f"Local cache write failed: {e}"
    return warning


def compute_snapshot_diff(previous_streams: Optional[List[Dict[str, Any]]],
                          current_streams: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compares current streams to the previous snapshot. No previous scan => no change claims."""
    if not previous_streams:
        return {"first_scan": True, "new_signals": [], "gone_count": 0,
                "highlights": ["First scan — baseline saved. Rescan later to see what changed."]}

    prev_urls = {i.get("url") for s in previous_streams for i in s.get("results", []) if i.get("url")}
    cur_urls = {i.get("url") for s in current_streams for i in s.get("results", []) if i.get("url")}

    new_signals = []
    for s in current_streams:
        for item in s.get("results", []):
            if item.get("url") and item["url"] not in prev_urls:
                new_signals.append({"category": s.get("category", ""), "title": item.get("title", ""),
                                    "url": item["url"], "provenance": item.get("provenance", "")})
    gone = len(prev_urls - cur_urls)
    if new_signals:
        highlights = [f"[{n['category']}] New source since last scan: {n['title']} ({n['provenance']})" for n in new_signals]
    else:
        highlights = ["No new sources since the previous scan."]
    return {"first_scan": False, "new_signals": new_signals, "gone_count": gone, "highlights": highlights}


# ------------------------------------------------------------------ pipeline
def run_pulsegrid_search(company_name: str) -> Dict[str, Any]:
    """
    1. Read previous snapshot (BEFORE writing).
    2. Run 4 Tavily streams in parallel (raises PulseGridError if any fail).
    3. Diff against previous snapshot.
    4. Save the new snapshot (skipped in simulation mode so fake data never pollutes the cache).
    """
    slug = company_name.strip().lower()
    simulated = simulation_enabled()
    warnings: List[str] = []

    if simulated:
        previous, backend = None, "none (simulation)"
    else:
        previous, backend, warn = load_previous_snapshot(slug)
        if warn:
            warnings.append(warn)

    current: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(search_stream, company_name, cat, q) for cat, q in STREAMS]
        for f in futures:
            current.append(f.result())  # propagates PulseGridError; order preserved

    diff = compute_snapshot_diff(previous, current)

    if not simulated and current:
        warn = save_snapshot(slug, company_name, current, backend)
        if warn:
            warnings.append(warn)

    return {
        "raw_streams": current,
        "delta_highlights": diff["highlights"],
        "diff": diff,
        "simulated": simulated,
        "storage_backend": backend,
        "storage_warnings": warnings,
        "tavily_calls_ok": 0 if simulated else len(current),
    }
