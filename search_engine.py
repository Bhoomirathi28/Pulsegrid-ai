import os
import concurrent.futures
from urllib.parse import urlparse
from tavily import TavilyClient
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

tavily_client = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None

supabase_client: Client = None
if supabase_url and supabase_key and "your_" not in supabase_url:
    try:
        supabase_client = create_client(supabase_url, supabase_key)
    except Exception:
        supabase_client = None


def classify_source_type(url: str, company_name: str) -> str:
    domain = urlparse(url).netloc.lower()
    company_clean = company_name.lower().replace(" ", "")

    if any(k in domain for k in ["reddit.com", "news.ycombinator.com", "twitter.com", "x.com"]):
        return "Community"
    elif company_clean in domain or "docs." in domain or "blog." in domain:
        return "Primary"
    else:
        return "Secondary"


def search_stream(company_name: str, category: str, query: str):
    if not tavily_client:
        return {"category": category, "results": []}
    try:
        response = tavily_client.search(
            query=f"{company_name} {query}",
            search_depth="advanced",
            max_results=5
        )
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
                "provenance": classify_source_type(r.get("url", ""), company_name)
            }
            for r in response.get("results", [])
        ]
        return {"category": category, "results": results}
    except Exception as e:
        print(f"Search error in {category}: {e}")
        return {"category": category, "results": []}


def compute_snapshot_diff(previous_streams, current_streams):
    if not previous_streams:
        return ["Initial scan baseline established. Future scans will highlight changes."]

    prev_urls = set()
    for s in previous_streams:
        for item in s.get("results", []):
            if item.get("url"):
                prev_urls.add(item.get("url"))

    new_signals = []
    for s in current_streams:
        cat = s.get("category", "")
        for item in s.get("results", []):
            if item.get("url") and item.get("url") not in prev_urls:
                new_signals.append(f"[{cat}] New signal detected: {item['title']} ({item['provenance']})")

    return new_signals if new_signals else ["No new delta changes detected since last scan."]


def run_pulsegrid_search(company_name: str):
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
