"""
Génération du rapport personnalisé via Groq API (gratuit).
Modèle : llama-3.3-70b-versatile
Clé gratuite sur : https://console.groq.com
"""

import json
import os
from groq import Groq
from typing import Dict
from question_bank import TRAIT_LABELS, TRAIT_EMOJIS
from adaptive_engine import compute_final_scores, get_trait_interpretation, determine_archetype
from models import Report, TraitScore


def _build_prompt(session: dict, final_scores: Dict[str, float]) -> str:
    trait_details = []
    for trait, score in final_scores.items():
        label = TRAIT_LABELS[trait]
        interp = get_trait_interpretation(trait, score)
        trait_details.append(f"- {label} ({trait}): {score}/100 — {interp}")

    responses_summary = []
    for r in session.get("responses", []):
        responses_summary.append(
            f"Q: {r['question_text']} → Réponse: {r['answer']}/5"
        )

    return f"""Tu es un psychologue bienveillant et expert en psychométrie Big Five.
Tu dois générer un rapport de personnalité structuré et personnalisé en français,
basé sur les scores suivants d'un test adaptatif Big Five.

SCORES BIG FIVE:
{chr(10).join(trait_details)}

RÉPONSES DÉTAILLÉES (pour contexte):
{chr(10).join(responses_summary[:10])}

Génère un rapport JSON strictement dans ce format (sans markdown, juste le JSON brut):
{{
  "overall_summary": "Synthèse globale du profil en 3-4 phrases, bienveillante et nuancée",
  "traits": {{
    "O": {{
      "score": {final_scores['O']},
      "label": "Ouverture",
      "emoji": "🌿",
      "interpretation": "2-3 phrases d'interprétation personnalisée pour ce score précis"
    }},
    "C": {{
      "score": {final_scores['C']},
      "label": "Conscienciosité",
      "emoji": "🎯",
      "interpretation": "2-3 phrases d'interprétation personnalisée pour ce score précis"
    }},
    "E": {{
      "score": {final_scores['E']},
      "label": "Extraversion",
      "emoji": "☀️",
      "interpretation": "2-3 phrases d'interprétation personnalisée pour ce score précis"
    }},
    "A": {{
      "score": {final_scores['A']},
      "label": "Agréabilité",
      "emoji": "💛",
      "interpretation": "2-3 phrases d'interprétation personnalisée pour ce score précis"
    }},
    "N": {{
      "score": {final_scores['N']},
      "label": "Névrosisme",
      "emoji": "🌊",
      "interpretation": "2-3 phrases d'interprétation personnalisée pour ce score précis"
    }}
  }},
  "strengths": [
    "Point fort 1 basé sur les scores dominants",
    "Point fort 2",
    "Point fort 3"
  ],
  "areas_of_attention": [
    "Axe de développement 1 formulé positivement",
    "Axe de développement 2"
  ],
  "recommendations": [
    "Recommandation concrète 1 (communication, travail ou bien-être)",
    "Recommandation concrète 2",
    "Recommandation concrète 3"
  ],
  "disclaimer": "Ce rapport est informatif et non médical. Il ne constitue pas un diagnostic psychologique. Pour tout accompagnement approfondi, consultez un professionnel qualifié."
}}

Règles:
- Sois bienveillant(e), nuancé(e) et non-normatif
- Évite tout jugement de valeur
- Les recommandations doivent être pratiques et actionnables
- Réponds UNIQUEMENT avec le JSON, sans explication ni balise markdown"""


async def generate_report(session: dict) -> Report:
    """Génère le rapport via Groq API (gratuit)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY non définie. "
            "Créez une clé gratuite sur https://console.groq.com"
        )

    client = Groq(api_key=api_key)
    final_scores = compute_final_scores(session)
    prompt = _build_prompt(session, final_scores)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.7,
    )

    full_response = response.choices[0].message.content or ""

    # Nettoyer les éventuelles balises markdown
    try:
        cleaned = full_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])

        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"L'IA n'a pas retourné un JSON valide: {e}\n{full_response[:500]}")

    traits = {}
    for trait_key, trait_data in data.get("traits", {}).items():
        traits[trait_key] = TraitScore(
            score=float(trait_data.get("score", final_scores.get(trait_key, 50))),
            label=trait_data.get("label", TRAIT_LABELS.get(trait_key, trait_key)),
            emoji=trait_data.get("emoji", TRAIT_EMOJIS.get(trait_key, "")),
            interpretation=trait_data.get("interpretation", ""),
        )

    archetype = determine_archetype(final_scores)

    return Report(
        archetype=archetype,
        overall_summary=data.get("overall_summary", ""),
        traits=traits,
        strengths=data.get("strengths", []),
        areas_of_attention=data.get("areas_of_attention", []),
        recommendations=data.get("recommendations", []),
        disclaimer=data.get(
            "disclaimer",
            "Ce rapport est informatif et non médical. Il ne constitue pas un diagnostic.",
        ),
    )
