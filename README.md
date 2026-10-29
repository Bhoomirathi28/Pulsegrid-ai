# ⚡ PulseGrid AI
### A competitive-intelligence agent that tries to prove its own conclusions wrong
*Built for the Nebius x NVIDIA Global AI Hackathon*

- **Demo URL:** `TODO: add Streamlit Community Cloud URL`
- **Video:** `TODO: add YouTube link`
- **Screenshot:** `TODO: add docs/screenshot.png` → `![PulseGrid AI](docs/screenshot.png)`

---

## Overview
Most competitive-intelligence tools run one prompt and print an unverified summary. PulseGrid does this instead:

1. **Investigate:** four parallel live-web streams via **Tavily** (talent, product/pricing, customer friction, market news).
2. **Hypothesize:** **NVIDIA Nemotron** (on **Nebius Token Factory**) reads the numbered evidence and forms ONE hypothesis, shown as *HYPOTHESIS — NOT FACT*.
3. **Attack:** Nemotron writes counter-queries; Tavily runs an adversarial "prove me wrong" search.
4. **Classify:** Nemotron marks which adversarial results genuinely contradict the hypothesis.
5. **Score:** the confidence score is computed in Python from the evidence (not by the model), with the factor breakdown shown in the UI.
6. **Explain:** the model writes only the "Why not higher?" text, the summary and recommendations.
7. **Baseline:** each scan is saved as a snapshot; rescan later to see which sources are new.

All data shown is live. If an API call fails, the app shows the error. It never substitutes fake data unless you explicitly set `DEMO_SIMULATION=true`, which puts a red **SIMULATED DATA — NOT LIVE** banner on every screen.

## How Nemotron is used
Model: `nvidia/nemotron-3-super-120b-a12b` on Nebius Token Factory (OpenAI-compatible API, base URL `https://api.tokenfactory.us-central1.nebius.com/v1/`). Verify the IDs your key can use with `python check_models.py`.

Three JSON-mode calls per investigation:
1. **Hypothesis + counter-queries:** from numbered evidence (E1, E2, ...) it returns one hypothesis, the supporting evidence IDs, and search queries designed to disprove it.
2. **Adversarial classification:** given the Tavily "prove me wrong" results (A1, A2, ...), it returns which ones contradict the hypothesis, plus an alternative explanation.
3. **Narrative:** given the already-computed score and factor breakdown, it writes the executive summary, "Why not higher?" and recommendations.

Guardrails: output is parsed robustly (code fences and `<think>` blocks stripped, one retry on invalid JSON). The model cites evidence by ID only; Python maps IDs back to the retrieved Tavily URLs, so a URL the model invents can never appear.

## How Tavily is used
- **Discovery:** 4 parallel `advanced` searches (talent, product/pricing, customer friction, market/news) → up to 20 sources, each classified Primary / Secondary / Community by domain.
- **Investigation:** the evidence ledger tab lists every retrieved source with its link.
- **Adversarial search:** Nemotron-written counter-queries are run through Tavily to look for contradicting evidence. If this search returns nothing, the confidence score is capped at 60 because the hypothesis was not meaningfully tested.

## Confidence score (computed in Python)
| Factor | Weight |
|---|---|
| Source-weighted supporting vs contradicting evidence | 35% |
| Amount of supporting evidence (full marks at 6 items) | 20% |
| Source quality (Primary 1.0 / Secondary 0.7 / Community 0.4) | 20% |
| Recency (undated sources count as 0.4) | 15% |
| Coverage across the 4 streams | 10% |

Maximum reported score is 95%. The UI shows each factor's value and points.

## Security notes
- Web content is wrapped in `<web_content>` delimiters and the model is told it is untrusted data; model JSON is schema-checked and evidence URLs come only from Tavily results.
- All web/model text is HTML-escaped before rendering; only http/https links are rendered as links.
- Company input is validated (max 60 chars), snapshot keys are slugged, and each session is limited to 5 investigations.
- Error messages are redacted of configured keys.

## Limitations
- Hypotheses are inferences from public web snippets, not facts. Wording is "consistent with", never "proves".
- Tavily snippets are short and often undated, so the recency factor is frequently low-information.
- Source type is classified by domain heuristics and can be wrong.
- Change detection compares source URLs only; it does not diff page content. The first scan only saves a baseline. There is no background monitoring: rescan manually to see what changed.
- Quality depends on Tavily results and the model's reading of them. Entity-name collisions (e.g. a common-word company name) can pollute results.
- Without Supabase, snapshots are stored in a local JSON file, which is ephemeral on Streamlit Community Cloud.

## Quickstart
```bash
pip install -r requirements.txt
cp .env.example .env        # fill in keys
python check_models.py      # confirm the Nemotron model ID
python test_logic.py        # offline sanity checks
streamlit run app.py
```

Keys are read from `st.secrets` first, then environment / `.env`. For Streamlit Community Cloud, paste the contents of `.streamlit/secrets.toml.example` (with real values) into *App settings → Secrets*.

Optional Supabase table (snapshot diffing; otherwise a local JSON file is used). `SUPABASE_KEY` is the **service_role** key: server-side only, keep it in secrets and never commit it.
```sql
create table if not exists scan_cache (
    id bigint generated always as identity primary key,
    company_slug text not null unique,
    company_name text not null,
    raw_streams jsonb not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

## Project layout
```text
├── app.py              # Streamlit app: run flow, session limits, results layout
├── ui_theme.py         # Kolam theme: CSS + HTML/SVG components (all text escaped)
├── ai_engine.py        # Nemotron calls, evidence-ID resolution, Python confidence score
├── search_engine.py    # Tavily streams, retries/timeouts, snapshots (Supabase + local), diffing
├── config.py           # st.secrets / env config, DEMO_SIMULATION flag
├── check_models.py     # lists available Nemotron model IDs on Nebius
├── test_logic.py       # offline tests
└── .streamlit/secrets.toml.example
```

## License
MIT
