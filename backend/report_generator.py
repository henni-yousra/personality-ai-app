"""
Génération du rapport personnalisé via Groq API (gratuit).
Modèle : llama-3.3-70b-versatile
Validation Pydantic stricte du JSON + une relance en cas d'échec.
"""

import json
import os
import re
from groq import Groq
from typing import Dict, List
from pydantic import BaseModel, Field, field_validator, ValidationError

from question_bank import TRAIT_LABELS, TRAIT_EMOJIS, ANSWER_MAX
from adaptive_engine import (
    compute_final_scores,
    get_trait_interpretation,
    determine_archetype,
    ensure_traits_latent,
    TRAITS,
)
from models import Report, TraitScore

REQUIRED_TRAITS = frozenset({"O", "C", "E", "A", "N"})
VARIANCE_UNCERTAINTY_THRESHOLD = 0.15


_INTERP_PLACEHOLDERS = frozenset(
    {
        "...",
        "…",
        "..",
        ".",
        "n/a",
        "na",
        "tbd",
        "xxx",
        "etc.",
        "etc",
    }
)


class _LLMTraitEntry(BaseModel):
    model_config = {"extra": "forbid"}

    score: float = Field(ge=0, le=100)
    label: str = Field(min_length=1, max_length=100)
    emoji: str = Field(min_length=1, max_length=2)
    interpretation: str = Field(min_length=50, max_length=8000)

    @field_validator("interpretation")
    @classmethod
    def interpretation_must_be_substantive(cls, v: str) -> str:
        s = (v or "").strip()
        low = s.lower()

        if low in _INTERP_PLACEHOLDERS:
            raise ValueError(
                f"Interpretation cannot be a placeholder. Got: '{s}'"
            )

        if re.fullmatch(r"[\s.…]{1,20}", s):
            raise ValueError(
                "Interpretation cannot be only ellipsis or whitespace"
            )

        if s.startswith("...") and len(s) < 55:
            raise ValueError(
                "Interpretation starting with '...' must be at least 55 chars "
                "(2-3 complete sentences)"
            )

        sentence_count = len([x for x in s.split('.') if x.strip()])
        if sentence_count < 2:
            raise ValueError(
                f"Interpretation must contain at least 2 sentences. Got {sentence_count}"
            )

        return v

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError(f"Score must be 0-100, got {v}")
        return v


class _LLMReportPayload(BaseModel):
    model_config = {"extra": "forbid"}

    overall_summary: str = Field(min_length=5)
    traits: Dict[str, _LLMTraitEntry]
    strengths: List[str] = Field(min_length=1)
    areas_of_attention: List[str] = Field(min_length=1)
    recommendations: List[str] = Field(min_length=1)
    disclaimer: str = Field(min_length=20)

    @field_validator("traits")
    @classmethod
    def exactly_big_five(cls, v: Dict[str, _LLMTraitEntry]) -> Dict[str, _LLMTraitEntry]:
        if set(v.keys()) != REQUIRED_TRAITS:
            raise ValueError("traits doit contenir exactement O, C, E, A, N")
        return v


def _latent_lines(session: dict) -> str:
    ensure_traits_latent(session)
    lines = []
    latent = session.get("traits_latent", {})
    for t in TRAITS:
        st = latent.get(t, {})
        lines.append(
            f"- {TRAIT_LABELS[t]} ({t}): mean_latent={st.get('mean', 0.5):.3f}, "
            f"variance_of_mean={st.get('variance', 0):.4f}, n={st.get('n', 0)}"
        )
    return "\n".join(lines)


def _traits_block_example_json(final_scores: Dict[str, float]) -> str:
    """Exemple JSON homogène pour les 5 traits (évite que le LLM copie « ... »)."""
    parts = []
    interp_hint = (
        "Deux à trois phrases complètes en français, nuancées et personnalisées pour ce score "
        "(texte réel, jamais de points de suspension seuls ni « ... » comme réponse)."
    )
    for key in ("O", "C", "E", "A", "N"):
        label = TRAIT_LABELS[key]
        emoji = TRAIT_EMOJIS[key]
        sc = final_scores[key]
        parts.append(
            f'''    "{key}": {{
      "score": {sc},
      "label": "{label}",
      "emoji": "{emoji}",
      "interpretation": "{interp_hint}"
    }}'''
        )
    return ",\n".join(parts)


def _build_prompt(session: dict, final_scores: Dict[str, float]) -> str:
    trait_details = []
    for trait, score in final_scores.items():
        label = TRAIT_LABELS[trait]
        interp = get_trait_interpretation(trait, score)
        trait_details.append(f"- {label} ({trait}): {score}/100 — {interp}")

    responses_summary = []
    for r in session.get("responses", []):
        responses_summary.append(
            f"Q: {r['question_text']} → Réponse: {r['answer']}/{ANSWER_MAX}"
        )

    latent_block = _latent_lines(session)

    return f"""Tu es un psychologue bienveillant et expert en psychométrie Big Five.
Tu dois générer un rapport de personnalité structuré et personnalisé en français,
basé sur les scores suivants d'un test adaptatif Big Five.

SCORES BIG FIVE:
{chr(10).join(trait_details)}

ESTIMATION LATENTE (moyenne 0-1 sur le trait, variance de la moyenne, nombre de réponses):
{latent_block}

RÉPONSES DÉTAILLÉES (pour contexte):
{chr(10).join(responses_summary[:12])}

Génère un rapport JSON strictement dans ce format (sans markdown, juste le JSON brut).
Pour CHAQUE trait, le champ "interpretation" doit être remplacé par un vrai texte de 2 à 3 phrases
(comme pour un rapport humain), pas des abréviations ni « ... ».

Structure attendue :
{{
  "overall_summary": "Synthèse globale du profil en 3-4 phrases, bienveillante et nuancée",
  "traits": {{
{_traits_block_example_json(final_scores)}
  }},
  "strengths": ["Point fort 1", "Point fort 2", "Point fort 3"],
  "areas_of_attention": ["Axe de développement 1", "Axe de développement 2"],
  "recommendations": ["Recommandation 1", "Recommandation 2", "Recommandation 3"],
  "disclaimer": "Ce rapport est informatif et non médical. Il ne constitue pas un diagnostic psychologique. Pour tout accompagnement approfondi, consultez un professionnel qualifié."
}}

Règles:
- Sois bienveillant(e), nuancé(e) et non-normatif
- Les clés de traits doivent être exactement O, C, E, A, N
- Chaque "interpretation" : minimum deux phrases complètes, personnalisées au score indiqué
- Réponds UNIQUEMENT avec le JSON, sans explication ni balise markdown"""


def _strip_json_markdown(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
    return cleaned.strip()


def _parse_llm_payload(content: str) -> _LLMReportPayload:
    data = json.loads(_strip_json_markdown(content))
    return _LLMReportPayload.model_validate(data)


def _groq_once(client: Groq, prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.7,
    )
    return response.choices[0].message.content or ""


def _apply_uncertainty(session: dict, traits: Dict[str, TraitScore]) -> Dict[str, TraitScore]:
    ensure_traits_latent(session)
    latent = session.get("traits_latent", {})
    out = dict(traits)
    for key, ts in out.items():
        st = latent.get(key, {})
        var_m = float(st.get("variance", 0))
        if var_m > VARIANCE_UNCERTAINTY_THRESHOLD:
            note = (
                " Profil à confirmer sur ce trait — mesure encore incertaine "
                f"(variance de la moyenne élevée : {var_m:.3f})."
            )
            out[key] = ts.model_copy(
                update={"interpretation": (ts.interpretation or "").rstrip() + note}
            )
    return out


async def generate_report(session: dict) -> Report:
    """
    Generates personality report with progressive retry strategy.

    Retry strategy:
    1. First attempt: Standard prompt
    2. Second attempt: Enhanced prompt with stricter formatting instructions
    3. Fallback: Return error with session data for manual review
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not defined. Create free key at https://console.groq.com"
        )

    client = Groq(api_key=api_key)
    final_scores = compute_final_scores(session)

    prompt = _build_prompt(session, final_scores)
    last_err: Exception | None = None
    payload: _LLMReportPayload | None = None

    try:
        full_response = _groq_once(client, prompt)
        payload = _parse_llm_payload(full_response)
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        last_err = e
        enhanced_prompt = (
            _build_prompt(session, final_scores)
            + "\n\n**CRITICAL REQUIREMENTS:**\n"
            + "1. Return ONLY valid JSON, no markdown or explanation\n"
            + "2. Each 'interpretation' field MUST be 2-3 complete sentences in French\n"
            + "3. NO placeholders like '...', 'etc.', 'tbd', or 'n/a'\n"
            + "4. Minimum 50 characters per interpretation\n"
            + "5. Traits MUST be exactly: O, C, E, A, N\n"
            + "6. All numeric scores must be 0-100"
        )

        try:
            full_response = _groq_once(client, enhanced_prompt)
            payload = _parse_llm_payload(full_response)
        except (json.JSONDecodeError, ValidationError, ValueError) as e2:
            last_err = e2
            print(f"[WARN] Second attempt failed: {e2}")

    if payload is None:
        raise ValueError(
            f"Failed to generate valid report after 2 attempts. "
            f"Last error: {last_err}. "
            f"Session ID: {session.get('session_id')}. "
            f"Scores: {final_scores}"
        )

    traits: Dict[str, TraitScore] = {}
    for trait_key, trait_data in payload.traits.items():
        traits[trait_key] = TraitScore(
            score=float(trait_data.score),
            label=trait_data.label or TRAIT_LABELS.get(trait_key, trait_key),
            emoji=trait_data.emoji or TRAIT_EMOJIS.get(trait_key, ""),
            interpretation=trait_data.interpretation,
        )

    traits = _apply_uncertainty(session, traits)
    archetype = determine_archetype(final_scores)

    return Report(
        archetype=archetype,
        overall_summary=payload.overall_summary,
        traits=traits,
        strengths=list(payload.strengths),
        areas_of_attention=list(payload.areas_of_attention),
        recommendations=list(payload.recommendations),
        disclaimer=payload.disclaimer,
    )
