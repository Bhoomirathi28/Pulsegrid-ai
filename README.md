<div align="center">

# ⚡ PulseGrid AI

### A competitive-intelligence agent that tries to prove its own conclusions wrong

*Built for the Nebius × NVIDIA Global AI Hackathon*

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Model](https://img.shields.io/badge/LLM-NVIDIA%20Nemotron-76B900?logo=nvidia&logoColor=white)
![Search](https://img.shields.io/badge/Search-Tavily-1F6F78)
![License](https://img.shields.io/badge/License-MIT-blue)

[Live Demo](#) · [Video Walkthrough](#) · [Quickstart](#-quickstart) · [Deployment](#-deployment)

<!-- TODO: replace the "#" links above with the Streamlit URL and YouTube link, and add a screenshot:
![PulseGrid AI](docs/screenshot.png) -->

</div>

---

## 📑 Table of Contents

1. [What it does](#-what-it-does)
2. [How it works](#-how-it-works)
3. [Tech stack](#-tech-stack)
4. [Quickstart](#-quickstart)
5. [Configuration](#-configuration)
6. [Deployment](#-deployment)
7. [Confidence score](#-confidence-score)
8. [Track record and learning](#-track-record-and-learning)
9. [Watchlist and alerts](#-watchlist-and-alerts)
10. [How Nemotron and Tavily are used](#-how-nemotron-and-tavily-are-used)
11. [Security](#-security)
12. [Limitations](#-limitations)
13. [Project layout](#-project-layout)
14. [About the names](#-about-the-names)
15. [License](#-license)

---

## 🎯 What it does

Most competitive-intelligence tools run one prompt and print an unverified summary. **PulseGrid AI investigates a company, forms a hypothesis, then actively tries to disprove it** before giving you a score you can audit.

- Every claim links back to a real source retrieved from the live web.
- The confidence score is **calculated in Python**, not guessed by the model, and the factor breakdown is shown in the UI.
- Past predictions are saved, so the system can show how accurate it has actually been.
- All data is live. If an API call fails, the app shows the error. It never invents data unless you explicitly turn on `DEMO_SIMULATION=true`, which puts a red **SIMULATED DATA — NOT LIVE** banner on every screen.

## 🔄 How it works

```text
 Company name
      │
      ▼
 1. INVESTIGATE   4 parallel live-web searches (Tavily): talent, product/pricing,
                  customer friction, market news  →  up to 20 sources
      │
      ▼
 2. HYPOTHESIZE   Nemotron reads the numbered evidence and forms ONE hypothesis
                  (always labelled "HYPOTHESIS — NOT FACT")
      │
      ▼
 3. ATTACK        Nemotron writes counter-queries; Tavily runs a "prove me wrong" search
      │
      ▼
 4. CLASSIFY      Nemotron marks which results genuinely contradict the hypothesis
      │
      ▼
 5. SCORE         Confidence is computed in Python from the evidence (not by the model)
      │
      ▼
 6. EXPLAIN       Model writes only the summary, "Why not higher?" and recommendations
      │
      ▼
 7. BASELINE      Scan is saved as a snapshot; rescan later to see which sources are new
```

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| UI | Streamlit with a custom folk-art (Kolam) theme |
| LLM | NVIDIA `nemotron-3-super-120b-a12b` on **Nebius Token Factory** (OpenAI-compatible API) |
| Web search | **Tavily** (`advanced` depth) |
| Storage | Supabase (Postgres), with automatic fallback to a local JSON file |
| Alerts | Slack webhook, optional SMTP email |
| Automation | GitHub Actions (daily watchlist rescan) |
| Packaging | Docker and Docker Compose |

## 🚀 Quickstart

**Prerequisites:** Python 3.11+, a [Tavily](https://tavily.com) API key, and a [Nebius Token Factory](https://tokenfactory.nebius.com) API key. Supabase is optional.

```bash
# 1. Clone
git clone https://github.com/<your-username>/Pulsegrid-ai.git
cd Pulsegrid-ai

# 2. (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your keys
cp .env.example .env             # Windows: copy .env.example .env
# open .env and fill in TAVILY_API_KEY and NEBIUS_API_KEY

# 5. Verify the model ID your key can use
python check_models.py

# 6. Run the offline sanity checks
python test_logic.py

# 7. Start the app
streamlit run app.py
```

Open **http://localhost:8501**, type a company name, and click Investigate.

## ⚙️ Configuration

Keys are read from `st.secrets` first, then from environment variables / `.env`.

| Variable | Required | Purpose |
|---|---|---|
| `TAVILY_API_KEY` | ✅ | Live web search |
| `NEBIUS_API_KEY` | ✅ | Access to Nemotron on Nebius Token Factory |
| `NEBIUS_MODEL` | ➖ | Defaults to `nvidia/nemotron-3-super-120b-a12b` |
| `SUPABASE_URL` | ➖ | Persistent storage for snapshots, predictions, watchlist |
| `SUPABASE_KEY` | ➖ | Supabase **service_role** key (server-side only, never commit it) |
| `SLACK_WEBHOOK_URL` | ➖ | Slack incoming webhook for alerts |
| `APP_URL` | ➖ | Link included in alert messages |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `ALERT_EMAIL_TO` | ➖ | Optional email alerts |
| `DEMO_SIMULATION` | ➖ | `true` shows fake data under a red banner. Leave unset for live mode. |

### Setting up Supabase (optional)

Without Supabase the app stores data in a local JSON file. That works locally but is wiped on Streamlit Community Cloud restarts.

1. Create a free project at [supabase.com](https://supabase.com).
2. Open **SQL Editor**, paste the contents of [`supabase_schema.sql`](supabase_schema.sql), and run it. This creates `predictions`, `watchlist` and `alert_log` with row-level security on and no public policies.
3. Copy the project URL and the **service_role** key into `SUPABASE_URL` and `SUPABASE_KEY`.

4. For snapshot diffing (rescan comparisons), also run this in the SQL editor:

```sql
create table if not exists scan_cache (
    id bigint generated always as identity primary key,
    company_slug text not null unique,
    company_name text not null,
    raw_streams jsonb not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

## ☁️ Deployment

### Option A: Streamlit Community Cloud (easiest)

1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app pointing at `app.py`.
3. Open **App settings → Secrets** and paste the contents of [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example) with your real values.

### Option B: Docker

```bash
cp .env.example .env             # fill in your keys
docker compose up -d --build
```

The app is served on port **8501** and includes a health check.

### Option C: Nebius Cloud VM

On a fresh Ubuntu VM, clone the repo, create `.env`, then run:

```bash
bash deploy.sh
```

The script installs Docker, opens port 8501 in the firewall, builds the container and prints the public URL.

## 📊 Confidence score

Computed entirely in Python. The UI shows each factor's value and the points it contributed.

| Factor | Weight |
|---|---|
| Source-weighted supporting vs contradicting evidence | 35% |
| Amount of supporting evidence (full marks at 6 items) | 20% |
| Source quality (Primary 1.0 / Secondary 0.7 / Community 0.4) | 20% |
| Recency (undated sources count as 0.4) | 15% |
| Coverage across the 4 streams | 10% |

- The maximum reported score is **95%**.
- If the adversarial search returns nothing, the score is **capped at 60%**, because the hypothesis was not meaningfully tested.

## 🧠 Track record and learning

- Every live investigation is saved as a **prediction**: hypothesis, industry label, pattern signature (the stream types that supported it), confidence and factor breakdown.
- **You** record the outcome: accept or dismiss a model suggestion, or mark it manually. Nemotron may *suggest* "confirmed" or "refuted" on a rescan, but only if it cites a real retrieved URL. Nothing resolves without your click.
- Predictions still pending after **90 days** are marked `expired`.
- **Learning rule:** only when a pattern + industry has **at least 5 resolved** predictions does confidence move toward that group's hit rate, by **at most ±10 points**. The UI explains the change (e.g. *"Adjusted -6 based on 7 past predictions"*). Below 5 it shows *"Not enough history yet (n/5)"*.
- There is no seeded or fake history, so a fresh install starts empty.

## 🔔 Watchlist and alerts

Alerts fire when a watched company is **rescanned**, either manually in the app or by the daily GitHub Action ([`watch.yml`](.github/workflows/watch.yml), 03:30 UTC). They are **not real-time**.

**Triggers** (all computed in Python):
- Confidence moved by 10+ points or crossed a band (Low / Moderate / High)
- A new source with weight ≥ 0.7 appeared
- A prediction was resolved

The same alert is never sent twice (tracked in `alert_log`).

**Setup**
1. Run `supabase_schema.sql` (see [Configuration](#setting-up-supabase-optional)).
2. Create a Slack **incoming webhook** and set `SLACK_WEBHOOK_URL`. Optionally set `APP_URL` and the SMTP variables.
3. In the app, click **Watch this company**, then **Send test alert** to verify the webhook (the message is labelled TEST).
4. For the daily run, add the same values as **GitHub repository secrets**. `watch_runner.py` scans at most 5 companies per run and refuses to run without Supabase, since there would be no stored previous scan to compare against.

## 🤖 How Nemotron and Tavily are used

### Nemotron (via Nebius Token Factory)

Base URL: `https://api.tokenfactory.us-central1.nebius.com/v1/`. Three JSON-mode calls per investigation:

1. **Hypothesis and counter-queries:** from numbered evidence (E1, E2, …) it returns one hypothesis, the supporting evidence IDs, and search queries designed to disprove it.
2. **Adversarial classification:** given the "prove me wrong" results (A1, A2, …), it returns which ones contradict the hypothesis, plus an alternative explanation.
3. **Narrative:** given the already-computed score and breakdown, it writes the executive summary, "Why not higher?" and recommendations.

**Guardrails:** output is parsed robustly (code fences and `<think>` blocks stripped, one retry on invalid JSON). The model cites evidence by ID only. Python maps IDs back to the retrieved Tavily URLs, so a URL the model invents can never appear.

### Tavily

- **Discovery:** 4 parallel `advanced` searches (talent, product/pricing, customer friction, market/news) yield up to 20 sources, each classified Primary / Secondary / Community by domain.
- **Evidence ledger:** a tab lists every retrieved source with its link.
- **Adversarial search:** Nemotron-written counter-queries are run through Tavily to look for contradicting evidence.

## 🔒 Security

- Web content is wrapped in `<web_content>` delimiters and the model is told it is untrusted data. Model JSON is schema-checked, and evidence URLs come only from Tavily results.
- All web and model text is HTML-escaped before rendering. Only `http`/`https` links are rendered as links.
- Company input is validated (max 60 characters), snapshot keys are slugged, and each session is limited to 5 investigations.
- Error messages are redacted of configured keys.
- Keep `.env` and `secrets.toml` out of version control (already in `.gitignore`).

## ⚠️ Limitations

- Hypotheses are inferences from public web snippets, not facts. Wording is "consistent with", never "proves".
- Tavily snippets are short and often undated, so the recency factor is frequently low-information.
- Source type is classified by domain heuristics and can be wrong.
- Change detection compares source URLs only; it does not diff page content. The first scan only saves a baseline.
- There is no background monitoring beyond the daily watchlist job.
- Entity-name collisions (e.g. a company with a common-word name) can pollute results.
- Without Supabase, data lives in a local JSON file, which is ephemeral on Streamlit Community Cloud.

## 🗂️ Project layout

```text
├── app.py                  # Streamlit app: run flow, session limits, results layout
├── ai_engine.py            # Nemotron calls, evidence-ID resolution, Python confidence score
├── search_engine.py        # Tavily streams, retries/timeouts, snapshots, diffing
├── track_record.py         # Predictions, outcomes, 90-day expiry, learning rule
├── alerts.py               # Watchlist, alert triggers, Slack/email delivery
├── watch_runner.py         # Headless daily rescan used by GitHub Actions
├── store.py                # Table store: Supabase or local JSON fallback
├── config.py               # st.secrets / env config, DEMO_SIMULATION flag
├── ui_theme.py             # Kolam theme: CSS + HTML/SVG components (all text escaped)
├── ui_art.py               # Decorative folk-art side panels (original SVG)
├── check_models.py         # Lists available Nemotron model IDs on Nebius
├── test_logic.py           # Offline tests
├── supabase_schema.sql     # predictions, watchlist, alert_log tables
├── Dockerfile              # Production image
├── docker-compose.yml      # One-command container run
├── deploy.sh               # Nebius Cloud VM bootstrap
├── .env.example            # Environment variable template
├── .streamlit/             # Theme config and secrets template
└── .github/workflows/      # Daily watchlist rescan
```

## 🪔 About the names

Section names come from **Nyaya**, classical Indian logic, which required arguing against your own position (*Purva Paksha*) before reaching a verdict (*Nirnaya*). English is always the main label in the app; the Sanskrit appears small beside it.

| Sanskrit | Romanized | Meaning | Where it appears |
|---|---|---|---|
| अनुमान | Anumana | Inference | "Hypothesis — not fact" heading, "Form hypothesis" stage |
| प्रमाण | Pramana | Valid means of knowing (evidence) | "Supporting evidence" heading, "Sort evidence" stage |
| पूर्वपक्ष | Purva Paksha | The opposing position, argued first | "Self-challenge" heading, "Challenge hypothesis" stage |
| निर्णय | Nirnaya | Conclusion, verdict | "Verdict · how the score was calculated" heading, "Verdict" stage |
| स्मृति | Smriti | Memory, what is remembered | "Track record" heading |
| गुप्तचर | Guptachar | Secret agent, scout | "Four agents in the field" heading on the live screen |

In evidence tags, hovering "Official source" shows *Pratyaksha — direct evidence*; "News report" and "Community post" show *Shabda — reported testimony*.

## 📄 License

Released under the [MIT License](LICENSE).
