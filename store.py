"""
store.py
========
Tiny table store used by the track record and alerts: Supabase when configured,
otherwise a local JSON file (fine locally; resets on Streamlit Cloud restarts).
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from search_engine import supabase_client

_DIR = os.path.dirname(os.path.abspath(__file__))
_lock = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def backend() -> str:
    return "supabase" if supabase_client else "local"


class Table:
    def __init__(self, name: str):
        self.name = name
        self.path = os.path.join(_DIR, f".pulsegrid_{name}.json")

    # ---- local JSON
    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (FileNotFoundError, ValueError, OSError):
            return []

    def _save(self, rows: List[Dict[str, Any]]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)

    # ---- API
    def insert(self, row: Dict[str, Any]) -> Dict[str, Any]:
        row = {"id": str(uuid.uuid4()), "created_at": now_iso(), **row}
        if supabase_client:
            supabase_client.table(self.name).insert(row).execute()
        else:
            with _lock:
                rows = self._load()
                rows.append(row)
                self._save(rows)
        return row

    def select(self, **eq: Any) -> List[Dict[str, Any]]:
        if supabase_client:
            q = supabase_client.table(self.name).select("*")
            for k, v in eq.items():
                q = q.eq(k, v)
            return q.execute().data or []
        return [r for r in self._load() if all(r.get(k) == v for k, v in eq.items())]

    def update(self, row_id: str, fields: Dict[str, Any]) -> None:
        if supabase_client:
            supabase_client.table(self.name).update(fields).eq("id", row_id).execute()
            return
        with _lock:
            rows = self._load()
            for r in rows:
                if r.get("id") == row_id:
                    r.update(fields)
            self._save(rows)

    def delete(self, row_id: str) -> None:
        if supabase_client:
            supabase_client.table(self.name).delete().eq("id", row_id).execute()
            return
        with _lock:
            self._save([r for r in self._load() if r.get("id") != row_id])

    def first(self, **eq: Any) -> Optional[Dict[str, Any]]:
        rows = self.select(**eq)
        return rows[0] if rows else None
