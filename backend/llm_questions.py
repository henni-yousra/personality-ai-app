"""
Reformulation optionnelle des questions via Groq (même stack que le rapport).
Variable d'environnement : LLM_QUESTION_REFORMULATION=true|1|yes
"""

import os
from groq import Groq


def maybe_reformulate_question_text(original: str) -> str:
    flag = os.getenv("LLM_QUESTION_REFORMULATION", "").lower()
    if flag not in ("1", "true", "yes", "on"):
        return original

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return original

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
        if len(text) < 8:
            return original
        return text.split("\n")[0].strip().strip('"').strip("'")
    except Exception:
        return original
