"""
search_engine.py
================
PulseGrid AI - Autonomous Competitive Intelligence Agent
Multi-Stream Parallel Search, Source Provenance Classification,
Supabase Caching, and Historical Snapshot Diffing.
"""

import os
import concurrent.futures
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from tavily import TavilyClient
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

def _is_placeholder(val: str) -> bool:
    if not val:
        return True
    val_lower = val.lower()
    return any(p in val_lower for p in ["your_", "your-", "placeholder", "xxx", "todo", "example", "none"])

# 1. Initialize Tavily Client
tavily_client: Optional[TavilyClient] = None
if not _is_placeholder(TAVILY_API_KEY):
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception:
        tavily_client = None

# 2. Initialize Supabase Client
supabase_client: Optional[Client] = None
if not _is_placeholder(SUPABASE_URL) and not _is_placeholder(SUPABASE_KEY):
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase_client = None


def classify_source_type(url: str, company_name: str) -> str:
    """Classifies source URLs into Primary, Secondary, or Community evidence."""
    try:
        domain = urlparse(url).netloc.lower()
        company_clean = company_name.lower().replace(" ", "")

        community_domains = ["reddit.com", "news.ycombinator.com", "twitter.com", "x.com", "discord.com", "medium.com"]
        if any(k in domain for k in community_domains):
            return "Community"
        elif company_clean in domain or any(k in domain for k in ["docs.", "blog.", "status.", "careers.", "api."]):
            return "Primary"
        else:
            return "Secondary"
    except Exception:
        return "Secondary"


def _generate_mock_results(company_name: str, category: str) -> List[Dict[str, Any]]:
    """Provides realistic fallback intelligence streams when running without live API keys."""
    company = company_name.strip().capitalize()
    if "Talent" in category:
        return [
            {
                "title": f"{company} Careers: Staff Distributed Systems & Inference Infrastructure Engineer",
                "url": f"https://careers.{company.lower()}.com/jobs/staff-infra-2026",
                "snippet": f"Scaling core low-latency model inference clusters. Experience with GPU kernel optimization, vLLM, and distributed scheduling required.",
                "provenance": "Primary"
            },
            {
                "title": f"LinkedIn Signal: Surge in {company} Headcount across Enterprise Solutions",
                "url": f"https://linkedin.com/pulse/{company.lower()}-headcount-acceleration",
                "snippet": f"Over the past 60 days, {company} added 18 enterprise infrastructure specialists, indicating an aggressive pivot toward corporate procurement.",
                "provenance": "Secondary"
            }
        ]
    elif "Pricing" in category or "Product" in category:
        return [
            {
                "title": f"{company} Changelog: Dedicated Private VPC Instances & Custom Model Quotas",
                "url": f"https://docs.{company.lower()}.com/changelog/2026-dedicated-vpcs",
                "snippet": f"Announcing new Enterprise Dedicated Tiers: Guaranteed SLA 99.99%, VPC peering, volume tiering, and custom token pricing starting at $2,500/mo.",
                "provenance": "Primary"
            },
            {
                "title": f"{company} Pricing Page Update: API Rate Tier Rebalancing",
                "url": f"https://{company.lower()}.com/pricing",
                "snippet": f"Pro plan remains standard while usage-based overages now feature automated burst smoothing for high-concurrency enterprise accounts.",
                "provenance": "Primary"
            }
        ]
    elif "Friction" in category or "Complaint" in category:
        return [
            {
                "title": f"r/LocalLLaMA: Anyone noticed queue degradation on {company} during US peak hours?",
                "url": f"https://reddit.com/r/LocalLLaMA/comments/{company.lower()}_latency_issues",
                "snippet": f"Responses taking 4-7 seconds during peak hours. Speculation that cluster capacity is prioritized for dedicated enterprise contracts.",
                "provenance": "Community"
            },
            {
                "title": f"Hacker News Discussion: {company} API concurrency rate limits",
                "url": f"https://news.ycombinator.com/item?id=38914022",
                "snippet": f"Developers reporting tighter free tier limits while business seats experience uninterrupted priority lane access.",
                "provenance": "Community"
            }
        ]
    else:  # Market & News
        return [
            {
                "title": f"TechCrunch: {company} Signs Strategic Tier-1 Enterprise Multi-Cloud Partnership",
                "url": f"https://techcrunch.com/2026/02/{company.lower()}-enterprise-expansion",
                "snippet": f"{company} announces strategic multi-region deployment agreements with global software vendors for private inference nodes.",
                "provenance": "Secondary"
            },
            {
                "title": f"PR Newswire: {company} Completes SOC 2 Type II and HIPAA Compliance Milestones",
                "url": f"https://prnewswire.com/news-releases/{company.lower()}-security-certifications",
                "snippet": f"{company} fulfills enterprise security requirements, opening direct procurement with regulated financial and healthcare institutions.",
                "provenance": "Secondary"
            }
        ]


def search_stream(company_name: str, category: str, query: str) -> Dict[str, Any]:
    """Executes an advanced search query for a specific intelligence stream."""
    if not tavily_client:
        return {
            "category": category,
            "query": query,
            "results": _generate_mock_results(company_name, category)
        }

    try:
        response = tavily_client.search(
            query=f"{company_name} {query}",
            search_depth="advanced",
            max_results=5
        )
        results = [
            {
                "title": r.get("title", "Untitled Signal"),
                "url": r.get("url", ""),
                "snippet": r.get("content", r.get("snippet", "")),
                "provenance": classify_source_type(r.get("url", ""), company_name)
            }
            for r in response.get("results", [])
        ]
        return {"category": category, "query": query, "results": results}
    except Exception as e:
        print(f"Search warning for stream [{category}]: {e}")
        return {
            "category": category,
            "query": query,
            "results": _generate_mock_results(company_name, category)
        }


def compute_snapshot_diff(previous_streams: Optional[List[Dict[str, Any]]], current_streams: List[Dict[str, Any]]) -> List[str]:
    """Compares current search streams against the historical snapshot to detect delta shifts."""
    if not previous_streams:
        return [
            "Initial intelligence baseline established.",
            f"Captured baseline across {len(current_streams)} strategic streams.",
            "Subsequent scans will calculate delta changes and signal drift against this snapshot."
        ]

    prev_urls = set()
    for s in previous_streams:
        for item in s.get("results", []):
            if item.get("url"):
                prev_urls.add(item.get("url"))

    new_signals = []
    for s in current_streams:
        cat = s.get("category", "")
        for item in s.get("results", []):
            url = item.get("url")
            if url and url not in prev_urls:
                new_signals.append(f"[{cat}] New signal detected: {item.get('title', 'Signal')} ({item.get('provenance', 'Source')})")

    return new_signals if new_signals else ["No major delta changes detected since previous baseline scan."]


def run_pulsegrid_search(company_name: str) -> Dict[str, Any]:
    """
    Main Intelligence Pipeline:
    1. Fetches historical snapshot from Supabase table `scan_cache`.
    2. Runs 4 parallel Tavily search streams via ThreadPoolExecutor.
    3. Calculates delta signals against baseline.
    4. Upserts newest snapshot to Supabase `scan_cache`.
    5. Returns dict with `raw_streams` and `delta_highlights`.
    """
    company_slug = company_name.strip().lower()
    previous_streams = None

    # 1. Fetch Previous Snapshot from Supabase (for snapshot diffing)
    if supabase_client:
        try:
            res = supabase_client.table("scan_cache").select("*").eq("company_slug", company_slug).execute()
            if res.data and len(res.data) > 0:
                previous_streams = res.data[0].get("raw_streams", [])
        except Exception as e:
            print(f"Supabase cache read warning: {e}")

    # 2. Parallel 4-Stream Tavily Search
    streams = [
        ("Talent & Hiring Signals", "hiring jobs careers R&D engineer hiring surge"),
        ("Product & Pricing Drift", "pricing plans API documentation changelog updates"),
        ("Customer Friction & Complaints", "reddit hacker news issue complaint outage feedback"),
        ("Market & News Signals", "funding acquisition launch partnership press release")
    ]

    current_streams = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(search_stream, company_name, cat, q)
            for cat, q in streams
        ]
        for future in concurrent.futures.as_completed(futures):
            current_streams.append(future.result())

    # Sort streams to preserve consistent category order
    category_order = [cat for cat, _ in streams]
    current_streams.sort(key=lambda s: category_order.index(s.get("category", "")) if s.get("category") in category_order else 99)

    # 3. Calculate Delta Signals
    deltas = compute_snapshot_diff(previous_streams, current_streams)

    # 4. Update Supabase with Newest Snapshot
    if supabase_client and current_streams:
        try:
            supabase_client.table("scan_cache").upsert({
                "company_slug": company_slug,
                "company_name": company_name,
                "raw_streams": current_streams
            }).execute()
        except Exception as e:
            print(f"Supabase cache write warning: {e}")

    return {
        "raw_streams": current_streams,
        "delta_highlights": deltas
    }
