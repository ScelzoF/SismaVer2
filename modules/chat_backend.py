"""
Chat backend con fallback locale per SismaVer2.

Strategia:
  1. Prova a connettersi a Supabase (timeout 2 s hard — thread con join).
  2. Se Supabase non è raggiungibile (DNS, timeout, tabella assente…)
     passa automaticamente al backend locale (file JSON in data/).
  3. Il fallback locale gestisce le regioni tramite il campo 'regione'
     in ogni messaggio (unico file, filtro per regione) — stessa struttura
     della tabella Supabase.
"""

import concurrent.futures
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------
_DATA_DIR = Path(__file__).parent.parent / "data"
_LOCAL_CHAT_FILE = _DATA_DIR / "chat_local.json"
_MAX_LOCAL_MESSAGES = 500   # evita crescita illimitata del file
_SUPABASE_TIMEOUT = 2       # secondi — fail fast se DNS morto

FUSO_ITALIA = timezone(timedelta(hours=2))   # UTC+2 ora legale; cambia a 1 in inverno


# ---------------------------------------------------------------------------
# Utilità comuni
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(FUSO_ITALIA).isoformat()


def _sanitize(text: str) -> str:
    return re.sub(r"<.*?>", "", text).strip()


# ---------------------------------------------------------------------------
# Backend locale (JSON)
# ---------------------------------------------------------------------------
class LocalBackend:
    """
    Salva i messaggi in data/chat_local.json.
    Thread-safety: Streamlit esegue un solo thread per sessione, quindi
    non servono lock espliciti.
    """

    def __init__(self):
        _DATA_DIR.mkdir(exist_ok=True)
        if not _LOCAL_CHAT_FILE.exists():
            _LOCAL_CHAT_FILE.write_text("[]", encoding="utf-8")

    # ------------------------------------------------------------------
    def _read_all(self) -> list:
        try:
            return json.loads(_LOCAL_CHAT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _write_all(self, messages: list):
        # Mantieni solo gli ultimi _MAX_LOCAL_MESSAGES
        _LOCAL_CHAT_FILE.write_text(
            json.dumps(messages[-_MAX_LOCAL_MESSAGES:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    def load_messages(
        self,
        regione_filtro: str = "Tutte le regioni",
        limit: int = 50,
        descending: bool = True,
    ) -> list:
        msgs = self._read_all()
        if regione_filtro != "Tutte le regioni":
            msgs = [m for m in msgs if m.get("regione") == regione_filtro]
        if descending:
            msgs = list(reversed(msgs))
        return msgs[:limit]

    def load_geo_messages(self, limit: int = 200) -> list:
        msgs = self._read_all()
        return [m for m in msgs if m.get("lat") is not None and m.get("lon") is not None][-limit:]

    def save_message(self, data: dict) -> bool:
        msgs = self._read_all()
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": _now_iso(),
            "nickname": _sanitize(data.get("nickname", "Anonimo")),
            "message": _sanitize(data.get("message", "")),
            "regione": data.get("regione", "Tutte le regioni"),
            "user_id": data.get("user_id", ""),
            "is_emergency": bool(data.get("is_emergency", False)),
            "is_moderated": bool(data.get("is_moderated", False)),
            "moderation_level": data.get("moderation_level", ""),
            "moderation_score": float(data.get("moderation_score", 0.0)),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
        }
        msgs.append(entry)
        self._write_all(msgs)
        return True


# ---------------------------------------------------------------------------
# Backend Supabase (con probe di connettività)
# ---------------------------------------------------------------------------
class SupabaseBackend:
    def __init__(self, client, table: str = "chat_messages"):
        self._sb = client
        self._table = table

    def load_messages(
        self,
        regione_filtro: str = "Tutte le regioni",
        limit: int = 50,
        descending: bool = True,
    ) -> list:
        q = self._sb.table(self._table).select("*")
        if regione_filtro != "Tutte le regioni":
            q = q.eq("regione", regione_filtro)
        q = q.order("timestamp", desc=descending).limit(limit)
        resp = q.execute()
        return resp.data if hasattr(resp, "data") else []

    def load_geo_messages(self, limit: int = 200) -> list:
        resp = (
            self._sb.table(self._table)
            .select("*")
            .not_.is_("lat", "null")
            .not_.is_("lon", "null")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data if hasattr(resp, "data") else []

    def save_message(self, data: dict) -> bool:
        resp = self._sb.table(self._table).insert(data).execute()
        if hasattr(resp, "error") and resp.error:
            raise RuntimeError(str(resp.error))
        return True


# ---------------------------------------------------------------------------
# Factory: restituisce (backend, is_online, status_message)
# ---------------------------------------------------------------------------
def get_backend(supabase_url: str, supabase_key: str):
    """
    Tenta la connessione a Supabase con timeout hard di _SUPABASE_TIMEOUT secondi.
    Se Supabase non risponde entro il timeout (es. DNS morto), cade subito
    sul LocalBackend senza bloccare l'app.
    Ritorna (SupabaseBackend, True, "") oppure (LocalBackend, False, motivo).
    """
    def _probe():
        from supabase import create_client
        if not supabase_url.startswith("https://"):
            raise ValueError("URL non valido")
        client = create_client(supabase_url, supabase_key)
        # Probe reale: DNS + TCP + auth + query → fallisce se tutto è morto
        client.table("chat_messages").select("id").limit(1).execute()
        return client

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_probe)
            client = future.result(timeout=_SUPABASE_TIMEOUT)
        return SupabaseBackend(client), True, ""

    except concurrent.futures.TimeoutError:
        return LocalBackend(), False, "timeout connessione (>2s)"
    except Exception as exc:
        motivo = str(exc)
        if "Name or service not known" in motivo or "Errno -2" in motivo:
            motivo = "server Supabase non raggiungibile (rete)"
        elif "does not exist" in motivo:
            motivo = "tabella chat_messages non trovata"
        return LocalBackend(), False, motivo
