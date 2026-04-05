"""
Reformulation optionnelle des questions via Groq (même stack que le rapport).
Variable d'environnement : LLM_QUESTION_REFORMULATION=true|1|yes
"""

import logging
import os
import time
from typing import Tuple

from groq import Groq

logger = logging.getLogger(__name__)


def maybe_reformulate_question_text(
    original: str, question_id: str = ""
) -> Tuple[str, bool]:
    """
    Retourne (texte_affiché, reformulated).
    Si la reformulation est inactive ou échoue, retourne (original, False).
    """
    flag = os.getenv("LLM_QUESTION_REFORMULATION", "").lower()
    if flag not in ("1", "true", "yes", "on"):
        return original, False

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return original, False

    t0 = time.perf_counter()
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Reformule cette affirmation de test de personnalité Big Five en français, "
                        "sur un ton naturel et clair. Une seule phrase, une seule intention. "
                        "Ne demande aucune information sensible (santé, politique, religion, etc.). "
                        "Ne numérote pas. Réponds uniquement par la phrase reformulée, sans guillemets.\n\n"
                        f"{original}"
                    ),
                }
            ],
            max_tokens=256,
            temperature=0.5,
        )
        text = (response.choices[0].message.content or "").strip()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if len(text) < 8:
            return original, False
        out = text.split("\n")[0].strip().strip('"').strip("'")
        if out == original.strip():
            return original, False
        logger.info(
            "question_reformulated question_id=%s groq_ms=%.1f",
            question_id or "?",
            elapsed_ms,
        )
        return out, True
    except Exception:
        return original, False
