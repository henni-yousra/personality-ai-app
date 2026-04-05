"""
Stockage des sessions au format JSON.
Chaque session est un fichier JSON dans backend/data/sessions/.
"""

import json
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data" / "sessions"


def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str) -> Path:
    return DATA_DIR / f"{session_id}.json"


def save_session(session_id: str, data: dict):
    _ensure_dir()
    data["updated_at"] = datetime.utcnow().isoformat()
    with open(_session_path(session_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_session(session_id: str) -> Optional[dict]:
    path = _session_path(session_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_session(session_id: str, email: str) -> dict:
    session = {
        "session_id": session_id,
        "email": email,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "responses": [],
        "used_question_ids": [],
        "completed": False,
        "report": None,
        "resend_count": 0,
        "last_resend": None,
        "scores": {
            "O": {"total": 0, "count": 0},
            "C": {"total": 0, "count": 0},
            "E": {"total": 0, "count": 0},
            "A": {"total": 0, "count": 0},
            "N": {"total": 0, "count": 0},
        },
        "traits_latent": {
            "O": {"mean": 0.5, "variance": 0.25, "n": 0, "m2": 0.0},
            "C": {"mean": 0.5, "variance": 0.25, "n": 0, "m2": 0.0},
            "E": {"mean": 0.5, "variance": 0.25, "n": 0, "m2": 0.0},
            "A": {"mean": 0.5, "variance": 0.25, "n": 0, "m2": 0.0},
            "N": {"mean": 0.5, "variance": 0.25, "n": 0, "m2": 0.0},
        },
    }
    save_session(session_id, session)
    return session
