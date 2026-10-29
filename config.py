"""
config.py
=========
Central configuration: reads st.secrets (Streamlit Cloud) with os.getenv / .env fallback.
"""

import os
from dotenv import load_dotenv

load_dotenv()

NEBIUS_BASE_URL = "https://api.tokenfactory.us-central1.nebius.com/v1/"
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"


def get_secret(name: str, default: str = "") -> str:
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass  # no secrets.toml / not running under Streamlit
    return os.getenv(name, default).strip()


def is_placeholder(val: str) -> bool:
    if not val:
        return True
    v = val.lower()
    return any(p in v for p in ["your_", "your-", "placeholder", "xxx", "todo", "example"])


def simulation_enabled() -> bool:
    return get_secret("DEMO_SIMULATION").lower() == "true"


TAVILY_API_KEY = get_secret("TAVILY_API_KEY")
NEBIUS_API_KEY = get_secret("NEBIUS_API_KEY")
NEBIUS_MODEL = get_secret("NEBIUS_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")
SLACK_WEBHOOK_URL = get_secret("SLACK_WEBHOOK_URL")
APP_URL = get_secret("APP_URL")
SMTP_HOST = get_secret("SMTP_HOST")
SMTP_PORT = get_secret("SMTP_PORT", "587")
SMTP_USER = get_secret("SMTP_USER")
SMTP_PASSWORD = get_secret("SMTP_PASSWORD")
ALERT_EMAIL_TO = get_secret("ALERT_EMAIL_TO")


def redact(msg: object) -> str:
    """Removes any configured secret values from an error message before it is shown."""
    text = str(msg)
    for secret in (TAVILY_API_KEY, NEBIUS_API_KEY, SUPABASE_KEY, SLACK_WEBHOOK_URL, SMTP_PASSWORD):
        if secret and len(secret) >= 8:
            text = text.replace(secret, "***")
    return text
