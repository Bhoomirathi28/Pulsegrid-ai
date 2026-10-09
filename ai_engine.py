import os
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

nebius_api_key = os.getenv("NEBIUS_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")

# 1. Initialize OpenAI-compatible Nebius Token Factory Client
nebius_client = None
if nebius_api_key and "your_" not in nebius_api_key:
    nebius_client = OpenAI(
        base_url="https://api.tokenfactory.us-central1.nebius.com/v1/",
        api_key=nebius_api_key
    )

tavily_client = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None


def execute_adversarial_search(company_name: str, hypothesis: str):
    """Generates counter-queries and searches Tavily for disconfirming evidence."""
    if not tavily_client:
        return ["No Tavily key provided for adversarial check."]

    # Formulate disconfirming query
    counter_query = f"{company_name} delays issues layoffs false rumours controversy"
    try:
        response = tavily_client.search(
            query=counter_query,
            search_depth="advanced",
            max_results=3
        )
        return [
            f"{r.get('title', '')}: {r.get('content', '')} ({r.get('url', '')})"
            for r in response.get("results", [])
        ]
    except Exception as e:
        return [f"Adversarial search warning: {e}"]


def synthesize_threat_dossier(company_name: str, search_data: dict) -> str:
    """3-Phase Reasoning Architecture: Hypothesis -> Adversarial Attack -> Verified Dossier."""
    raw_streams = search_data.get("raw_streams", [])
    delta_highlights = search_data.get("delta_highlights", [])

    # Format raw stream snippets for LLM context
    streams_summary = ""
    for stream in raw_streams:
        cat = stream.get("category", "Unknown")
        streams_summary += f"\n### Stream: {cat}\n"
        for item in stream.get("results", []):
            streams_summary += f"- [{item.get('provenance', 'Source')}] {item.get('title')}: {item.get('snippet')} (URL: {item.get('url')})\n"

    # Fallback if Nebius client is missing or using placeholder key
    if not nebius_client:
        return f"""# ⚡ Executive Threat Dossier: {company_name}

> *Note: Running in local preview mode. Add a valid `NEBIUS_API_KEY` to enable Nemotron 3 synthesis.*

### 🔍 Recent Delta Highlights
{chr(10).join([f"- {d}" for d in delta_highlights])}

### 📊 Raw Data Summary
- Captured **{len(raw_streams)}** web data streams via Tavily.
- Ready for Nemotron 3 adversarial synthesis.
"""

    # Phase 1 & 2: Prompt Nemotron 3 for Initial Correlation & Adversarial Attack
    system_prompt = """You are PulseGrid AI, an autonomous competitive intelligence agent. Your job is to analyze multi-stream web data, correlate weak signals across categories, and perform an adversarial sanity check before reaching conclusions. Never make ungrounded claims. Every claim must cite direct source URLs from the input stream."""

    user_prompt = f"""Analyze the following competitive web data streams for **{company_name}**:

Delta Signals:
{delta_highlights}

Raw Web Data Streams:
{streams_summary}

---

Perform a 3-Phase Intelligence Analysis:
1. **Strategic Hypothesis**: Correlate weak signals across hiring, pricing/docs, customer friction, and market news to form a core strategic thesis.
2. **Adversarial Verification**: Identify potential flaws, counter-arguments, or alternative explanations for this hypothesis.
3. **Confidence Scoring**: Assign an evidence-backed Confidence Score (0-100%) and explain "Why Not Higher?".

Output the final Executive Threat Dossier in clean Markdown using these standard sections:
# ⚡ Executive Threat Dossier: {company_name}
## 🧠 Core Strategic Hypothesis
## 🟢 Supporting Evidence Ledger (with Source URL links)
## 🔴 Adversarial Counter-Evidence & Risks
## 📊 Verified Confidence Score & "Why Not Higher?"
## 🚀 Actionable Executive Recommendations"""

    try:
        response = nebius_client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=2500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during Nemotron 3 synthesis: {e}"
