"""
Préparation optionnelle des questions via Groq.

Variables d'environnement :
- LLM_QUESTION_GENERATION=true|1|yes   -> génère une variante équivalente
- LLM_QUESTION_REFORMULATION=true|1|yes -> reformule la question finale
"""

import logging
import os
import time
from typing import Iterable, Tuple

from groq import Groq

logger = logging.getLogger(__name__)


def _flag_enabled(name: str) -> bool:
    return os.getenv(name, "").lower() in ("1", "true", "yes", "on")


def _sanitize_one_line(text: str) -> str:
    return (text or "").strip().split("\n")[0].strip().strip('"').strip("'")


def _safe_text_or_original(candidate: str, fallback: str) -> str:
    """Retourne un texte sûr (une ligne, longueur OK) ou le fallback normalisé (strip)."""
    out = _sanitize_one_line(candidate)
    if len(out) < 8:
        return (fallback or "").strip()
    return out


def _build_generation_prompt(original: str, options: Iterable[str]) -> str:
    options_block = "\n".join(f"- {opt}" for opt in options)
    return (
        "Tu es expert en psychométrie Big Five.\n"
        "Génère UNE nouvelle question équivalente à la question d'origine, en français.\n"
        "Contraintes strictes:\n"
        "- une seule phrase, une seule intention\n"
        "- langage clair, non discriminant\n"
        "- ne demande aucune information sensible (santé, politique, religion, etc.)\n"
        "- reste compatible avec exactement les mêmes options de réponse\n"
        "- ne mentionne pas les options dans la question\n"
        "Réponds uniquement par la question générée, sans guillemets.\n\n"
        f"Question d'origine:\n{original}\n\n"
        f"Options qui doivent rester valides:\n{options_block}\n"
    )


def _build_reformulation_prompt(original: str) -> str:
    return (
        "Reformule cette question de test de personnalité Big Five en français, "
        "sur un ton naturel et clair. Une seule phrase, une seule intention. "
        "Ne demande aucune information sensible (santé, politique, religion, etc.). "
        "Ne numérote pas. Réponds uniquement par la phrase reformulée, sans guillemets.\n\n"
        f"{original}"
    )


def _groq_text(client: Groq, prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.5,
    )
    return response.choices[0].message.content or ""


def maybe_prepare_question_text(
    original: str,
    question_id: str = "",
    option_labels: Iterable[str] = (),
) -> Tuple[str, bool, bool]:
    """
    Retourne (texte_affiché, reformulated, generated).
    - generated=True si une nouvelle variante équivalente a été générée.
    - reformulated=True si la question finale a été reformulée.
    """
    use_generation = _flag_enabled("LLM_QUESTION_GENERATION")
    use_reformulation = _flag_enabled("LLM_QUESTION_REFORMULATION")
    if not use_generation and not use_reformulation:
        return original, False, False

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return original, False, False

    try:
        client = Groq(api_key=api_key)
    except Exception:
        return original, False, False

    # Référence unique pour les comparaisons : évite faux positifs si `original` a des espaces
    # en tête/fin alors que le fallback renvoie la même chaîne sans strip explicite côté candidat.
    baseline = (original or "").strip()
    base_text = baseline
    was_generated = False
    was_reformulated = False

    if use_generation:
        t0 = time.perf_counter()
        try:
            generated_raw = _groq_text(
                client,
                _build_generation_prompt(baseline, option_labels),
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            candidate = _safe_text_or_original(generated_raw, baseline)
            cand_norm = candidate.strip()
            if cand_norm != baseline:
                base_text = cand_norm
                was_generated = True
                logger.info(
                    "question_generated question_id=%s groq_ms=%.1f",
                    question_id or "?",
                    elapsed_ms,
                )
        except Exception:
            base_text = baseline

    if use_reformulation:
        t0 = time.perf_counter()
        try:
            reform_baseline = base_text.strip()
            reform_raw = _groq_text(client, _build_reformulation_prompt(reform_baseline))
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            candidate = _safe_text_or_original(reform_raw, reform_baseline)
            cand_norm = candidate.strip()
            if cand_norm != reform_baseline:
                base_text = cand_norm
                was_reformulated = True
                logger.info(
                    "question_reformulated question_id=%s groq_ms=%.1f",
                    question_id or "?",
                    elapsed_ms,
                )
        except Exception:
            pass

    return base_text, was_reformulated, was_generated
