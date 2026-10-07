# ⚡ PulseGrid AI
### Autonomous Competitive Intelligence Agent That Has to Prove Its Own Conclusions
*Built for the Nebius x NVIDIA Global AI Hackathon*

---

## 🎯 Overview
Most competitive intelligence tools take a single query, run an LLM prompt, and output an unverified summary. 

**PulseGrid AI reverses the paradigm:**
PulseGrid does not trust its first answer. It acts like an elite investigative intelligence analyst:
1. **Investigate:** Parallel live-web scanning across 4 intelligence streams via **Tavily Search API**.
2. **Detect & Baseline:** Caches snapshots in **Supabase** (`scan_cache`) and computes real historical diffs.
3. **Correlate:** Synthesizes cross-signal patterns using **NVIDIA Nemotron 3 Super (120B)** via **Nebius Token Factory**.
4. **Hypothesize:** Generates strategic hypotheses (explicitly marked *HYPOTHESIS — NOT FACT*).
5. **Attack ("Prove Me Wrong"):** Actively formulates adversarial search queries to attempt to falsify its own hypothesis.
6. **Audit & Trust Layer™:** Calculates a multi-factor, evidence-backed confidence score with a transparent *"Why Not Higher?"* assessment.
7. **Decide & Watch:** Delivers high-impact executive counter-moves and initiates persistent 72h watch mode monitoring.

---

## 🛠️ Tech Stack
- **Web Search & Adversarial Retrieval:** [Tavily Search API](https://tavily.com) (4 parallel streams + falsification search)
- **Reasoning Engine:** [Nebius Token Factory](https://tokenfactory.nebius.com) (`nvidia/nemotron-3-super-120b` & `nvidia/nemotron-3-ultra-550b`)
- **Database & Snapshot Caching:** [Supabase](https://supabase.com) (`supabase-py` with local fallback)
- **Web UI:** [Streamlit](https://streamlit.io) (Dark cyber-intelligence obsidian & NVIDIA green design)
- **Configuration:** `python-dotenv`

---

## 🚀 Quickstart

### 1. Installation
Clone or navigate to the directory:
```bash
cd pulsegrid-ai
python -m pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your credentials:
```env
TAVILY_API_KEY=tvly-xxxxxxxxxxxx
NEBIUS_API_KEY=nebius-xxxxxxxxxxxx
NEBIUS_MODEL=nvidia/nemotron-3-super-120b
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```
*(Note: If API keys are not supplied, PulseGrid features an intelligent simulation fallback so you can demo the entire end-to-end interface and adversarial pipeline out-of-the-box!)*

### 3. Supabase Schema (Optional but Recommended)
In your Supabase SQL Editor:
```sql
create table if not exists scan_cache (
    id bigint generated always as identity primary key,
    company_slug text not null unique,
    company_name text not null,
    raw_streams jsonb not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📂 Project Architecture
```text
pulsegrid-ai/
├── search_engine.py       # 4 parallel Tavily streams, Supabase cache, source provenance, diffing
├── ai_engine.py           # Nemotron 3 synthesis, adversarial audit, Trust Layer™ confidence scoring
├── app.py                 # Streamlit high-tech UI, adversarial breakdown tabs, live status
├── requirements.txt       # Project dependencies
├── .env.example           # API credentials template
└── README.md              # Project documentation
```
