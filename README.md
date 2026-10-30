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
- **Adversarial search:** four Tavily counter-searches, one per challenge type: CUTS (layoffs, shutdowns), STATEMENTS (official denials), ALTERNATIVE (another explanation), ABSENCE (evidence that should exist). Nemotron writes the queries; Python templates fill any it leaves out. TIMING is checked in Python from the supporting evidence's publish dates (no search). The Self-challenge tab shows, per type: intent, exact query, result count, outcome (contradicts / neutral / nothing found) and top URL, plus "N of 5 challenge types checked"; a failed search shows as "not checked". If the counter-searches return nothing, the score is capped at 60 because the hypothesis was not meaningfully tested.

## Confidence score (computed in Python)
**Each evidence item** gets a weight = tier × specificity × recency, capped at 0.85:

| | |
|---|---|
| Tier | A official 1.0 (company site, careers/job pages, .gov) · B news 0.7 · C blogs 0.45 · D forums 0.25 |
| Specificity | specific 1.0 / vague 0.5. Specific = the source's own text names money, numbers, dates or products/versions. Job pages are vague by default. |
| Recency | halves every 45 days; undated items count as 45 days old |

Items about the same event count once. The model's "related items" links are only accepted when the titles share 2+ distinctive words and the dates are within 14 days. All job ads on one careers site count as one hiring signal. At most 3 items per domain count. Counted items combine with noisy-OR: strength = 1 − Π(1 − w).

| Factor | Weight |
|---|---|
| Evidence strength (noisy-OR) | 70% |
| Support vs contradiction, scaled by strength | 20% |
| Coverage across the 4 streams, scaled by strength | 10% |

**Bands:** Confirmed 85+ (only with a counted, specific Tier-A item; otherwise capped at 84) · Likely 65–84 · Plausible 45–64 · Speculative 25–44 · Unsupported 0–24. Maximum 95. The UI shows each item's weight ("Tier A · specific · 12d ago · w 0.82 · domain"), the factor points, how many points to the next band, and **what would raise / lower** the score (each computed by re-running the formula on changed evidence).

The formula version is stored with every prediction; a confidence-change alert is skipped when the previous score came from an older formula.

## Track record
- Every live investigation is saved automatically as a **prediction** (hypothesis, industry label, pattern signature = the stream types that supported it, confidence, factor breakdown).
- Outcomes are recorded by **you**: accept or dismiss a model suggestion, or mark one manually. Nemotron may *suggest* "confirmed" or "refuted" on a rescan, but only if it cites a real retrieved URL; nothing is resolved without your click.
- Predictions still pending after **90 days** are marked `expired`.
- **Learning rule:** only when a pattern + industry has **at least 5 resolved** predictions is confidence moved toward that group's hit rate, by **at most ±10 points**, and the UI says how (e.g. "Adjusted -6 based on 7 past predictions"). Below 5 it shows "Not enough history yet (n/5)". There is no seeded or fake history, so a fresh install starts empty.
- Stored in Supabase (`predictions` table) or a local file if Supabase isn't configured.

## Alerts and watchlist
Alerts fire when a watched company is **rescanned** (manually in the app, or by the daily GitHub Action in `.github/workflows/watch.yml`). They are **not real-time**.

Triggers (computed in Python): confidence moved by 10+ points or crossed a band (Unsupported / Speculative / Plausible / Likely / Confirmed); a new source with source weight ≥ 0.7 appeared (Primary 1.0 / Secondary 0.7 / Community 0.4); a prediction was resolved. The same alert is never sent twice (`alert_log`).

Setup:
1. Run `supabase_schema.sql` in the Supabase SQL editor (tables `predictions`, `watchlist`, `alert_log`, RLS on, no public policies; the app uses the service_role key server-side).
2. Create a Slack **incoming webhook** and set `SLACK_WEBHOOK_URL` (and optionally `APP_URL`). Email is optional: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `ALERT_EMAIL_TO`.
3. In the app, click **Watch this company**, and **Send test alert** to check the webhook (the message is labelled TEST).
4. For the daily run, add the same values as GitHub repo secrets. `watch_runner.py` scans at most 5 companies per run and refuses to run without Supabase (there would be no stored previous scan to compare against).

## About the names
Section names come from Nyaya, classical Indian logic, which required arguing against your own position (Purva Paksha) before reaching a verdict (Nirnaya). English is always the main label in the app; the Sanskrit appears small beside it.

| Sanskrit | Romanized | Meaning | Where it appears in PulseGrid |
|---|---|---|---|
| अनुमान | Anumana | Inference | "Hypothesis — not fact" heading and the "Form hypothesis" stage |
| प्रमाण | Pramana | Valid means of knowing (evidence) | "Supporting evidence" heading and the "Sort evidence" stage |
| पूर्वपक्ष | Purva Paksha | The opposing position, argued first | "Self-challenge" heading and the "Challenge hypothesis" stage |
| निर्णय | Nirnaya | Conclusion, verdict | "Verdict · how the score was calculated" heading and the "Verdict" stage |
| स्मृति | Smriti | Memory, what is remembered | "Track record" heading |
| गुप्तचर | Guptachar | Secret agent, scout | "Four agents in the field" heading on the live screen |

In evidence tags, hovering "Official source" shows *Pratyaksha — direct evidence*, and "News report" / "Community post" show *Shabda — reported testimony*.

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
