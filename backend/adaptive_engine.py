"""
Moteur adaptatif de sélection de questions et de scoring.
Stratégie : équilibrer la couverture des traits en sélectionnant
toujours le trait le moins répondu, puis une question aléatoire pour ce trait.
"""

import random
import math
from typing import Optional, List, Dict, Tuple
from question_bank import (
    QUESTIONS,
    ANSWER_OPTIONS,
    ANSWER_MIN,
    ANSWER_MAX,
    TRAIT_LABELS,
    TRAIT_EMOJIS,
)
from models import Question, AnswerOption, Archetype


TRAITS = ["O", "C", "E", "A", "N"]

# ── 6 Archétypes de personnalité ──────────────────────────────────────────────
# Chaque profil définit le score Big Five "idéal" de cet archétype (0-100).
# L'archétype retenu est celui dont le profil est le plus proche des scores réels.
ARCHETYPES = [
    {
        "name": "Le Visionnaire",
        "emoji": "◉",
        "tagline": "Créatif, inspirant et tourné vers l'avenir",
        "description": (
            "Vous voyez le monde comme un terrain d'exploration infini. "
            "Votre imagination débordante et votre enthousiasme naturel "
            "inspirent ceux qui vous entourent. Vous aimez bousculer les idées reçues "
            "et proposer des perspectives nouvelles."
        ),
        "profile": {"O": 80, "C": 50, "E": 72, "A": 58, "N": 42},
    },
    {
        "name": "Le Logicien",
        "emoji": "■",
        "tagline": "Analytique, précis et indépendant",
        "description": (
            "Vous adorez résoudre des problèmes complexes et aller au fond des choses. "
            "Votre esprit rigoureux et votre curiosité intellectuelle font de vous "
            "un penseur exceptionnel. Vous préférez la réflexion solitaire "
            "aux grandes assemblées."
        ),
        "profile": {"O": 78, "C": 76, "E": 24, "A": 50, "N": 48},
    },
    {
        "name": "Le Gardien",
        "emoji": "●",
        "tagline": "Fiable, bienveillant et ancré",
        "description": (
            "Vous êtes le pilier sur lequel les autres s'appuient. "
            "Organisé(e) et attentionné(e), vous créez un environnement sécurisant "
            "et chaleureux autour de vous. Votre sens du devoir et votre générosité "
            "sont des forces remarquables."
        ),
        "profile": {"O": 44, "C": 76, "E": 52, "A": 78, "N": 24},
    },
    {
        "name": "L'Architecte",
        "emoji": "▲",
        "tagline": "Ambitieux, stratégique et déterminé",
        "description": (
            "Vous avez une vision claire et la volonté de la réaliser. "
            "Votre sens de l'organisation et votre détermination font de vous "
            "un leader naturel. Vous excellez à structurer des projets complexes "
            "et à mobiliser votre énergie vers des objectifs concrets."
        ),
        "profile": {"O": 56, "C": 82, "E": 70, "A": 34, "N": 38},
    },
    {
        "name": "L'Empathique",
        "emoji": "◆",
        "tagline": "Chaleureux, à l'écoute et profondément humain",
        "description": (
            "Vous ressentez profondément les émotions — les vôtres et celles des autres. "
            "Votre capacité d'écoute et votre chaleur humaine créent des liens forts "
            "et authentiques. Vous êtes souvent la personne vers qui les autres "
            "se tournent dans les moments difficiles."
        ),
        "profile": {"O": 56, "C": 44, "E": 58, "A": 82, "N": 68},
    },
    {
        "name": "L'Explorateur",
        "emoji": "◻",
        "tagline": "Libre, spontané et toujours en mouvement",
        "description": (
            "Vous vivez dans l'instant présent et vous adaptez à toutes les situations "
            "avec une aisance naturelle. Votre ouverture d'esprit et votre soif "
            "de nouvelles expériences vous poussent constamment à sortir des sentiers battus."
        ),
        "profile": {"O": 76, "C": 28, "E": 72, "A": 62, "N": 44},
    },
]


def determine_archetype(scores: Dict[str, float]) -> Archetype:
    """
    Retourne l'archétype dont le profil Big Five est le plus proche
    des scores de l'utilisateur (distance euclidienne pondérée).
    """
    best = None
    best_dist = float("inf")

    for arch in ARCHETYPES:
        dist = math.sqrt(
            sum((scores.get(t, 50) - arch["profile"][t]) ** 2 for t in TRAITS)
        )
        if dist < best_dist:
            best_dist = dist
            best = arch

    return Archetype(
        name=best["name"],
        emoji=best["emoji"],
        tagline=best["tagline"],
        description=best["description"],
    )


def build_question(raw: dict) -> Question:
    return Question(
        id=raw["id"],
        text=raw["text"],
        trait=raw["trait"],
        polarity=raw["polarity"],
        options=[AnswerOption(**o) for o in ANSWER_OPTIONS],
    )


def ensure_traits_latent(session: dict) -> None:
    """Initialise traits_latent (moyenne 0–1, variance de la moyenne, n, m2 Welford)."""
    if "traits_latent" in session:
        return
    session["traits_latent"] = {
        t: {"mean": 0.5, "variance": 0.25, "n": 0, "m2": 0.0} for t in TRAITS
    }


def _answer_scale_denom() -> float:
    return float(ANSWER_MAX - ANSWER_MIN)


def _latent_observation(polarity: int, answer: int) -> float:
    """Valeur 0–1 : haut = fort sur le trait (question positive ou inversée)."""
    d = _answer_scale_denom()
    if d <= 0:
        return 0.5
    if polarity == 1:
        return (answer - ANSWER_MIN) / d
    return (ANSWER_MAX - answer) / d


def _welford_update(state: dict, x: float) -> None:
    """
    Updates running mean and variance using Welford's online algorithm.
    Ensures numerical stability for variance calculation.

    Args:
        state: Dict with keys 'n', 'mean', 'm2'
        x: New observation (0-1 range)
    """
    if not (0 <= x <= 1):
        raise ValueError(f"Observation must be in [0, 1], got {x}")

    n = state["n"] + 1
    delta = x - state["mean"]
    mean = state["mean"] + delta / n
    delta2 = x - mean
    m2 = state.get("m2", 0.0) + delta * delta2
    state["n"] = n
    state["mean"] = mean
    state["m2"] = m2

    if n < 2:
        state["variance"] = 0.25
    else:
        sample_var = m2 / (n - 1)
        state["variance"] = max(0.0, sample_var / n)


def select_next_question(session: dict) -> Tuple[Optional[Question], str]:
    """
    Selects the next question using adaptive strategy.

    Strategy:
    1. Identifies trait with highest variance of mean (most uncertain)
    2. Selects difficulty based on variance threshold:
       - variance > 0.08: difficulty 1 (direct questions)
       - variance > 0.03: difficulty 2 (moderate)
       - variance ≤ 0.03: difficulty 3 (nuanced)
    3. Randomly selects from candidates matching target difficulty

    Args:
        session: Current session with traits_latent and used_question_ids

    Returns:
        Tuple of (Question or None, selection_reason string)

    Raises:
        None - returns (None, reason_string) on failure
    """
    ensure_traits_latent(session)
    used_ids = set(session.get("used_question_ids", []))

    available = [q for q in QUESTIONS if q["id"] not in used_ids]
    if not available:
        return None, "no_available_questions"

    available_by_trait: Dict[str, List[dict]] = {t: [] for t in TRAITS}
    for q in available:
        available_by_trait[q["trait"]].append(q)

    traits_with_questions = [t for t in TRAITS if available_by_trait[t]]
    if not traits_with_questions:
        return None, "no_trait_slot"

    latent = session["traits_latent"]

    def trait_sort_key(t: str):
        st = latent[t]
        return (st["variance"], -st["n"])

    target_trait = max(traits_with_questions, key=trait_sort_key)
    st = latent[target_trait]
    n_trait = int(st["n"])
    var_trait = float(st["variance"])

    if n_trait < 2 or var_trait > 0.08:
        target_diff = 1
    elif var_trait > 0.03:
        target_diff = 2
    else:
        target_diff = 3

    candidates = available_by_trait[target_trait]
    dists = [abs(int(q.get("difficulty", 2)) - target_diff) for q in candidates]
    best_d = min(dists)
    pool = [q for q, d in zip(candidates, dists) if d == best_d]
    chosen_raw = random.choice(pool)
    diff = int(chosen_raw.get("difficulty", 2))
    reason = (
        f"trait={target_trait} var_mean={var_trait:.4f} n={n_trait} "
        f"difficulty_pick={diff} (target={target_diff}) qid={chosen_raw['id']}"
    )
    return build_question(chosen_raw), reason


def update_scores(session: dict, question_id: str, answer: int) -> dict:
    """
    Met à jour les scores de la session après une réponse.
    Le score contribué = answer * polarity (échelle ANSWER_MIN–ANSWER_MAX → contribution par item bornée).
    """
    # Trouver la question dans la banque
    raw = next((q for q in QUESTIONS if q["id"] == question_id), None)
    if raw is None:
        return session

    trait = raw["trait"]
    polarity = raw["polarity"]
    contribution = answer * polarity

    scores = session.setdefault("scores", {})
    if trait not in scores:
        scores[trait] = {"total": 0, "count": 0}

    scores[trait]["total"] += contribution
    scores[trait]["count"] += 1

    ensure_traits_latent(session)
    x = _latent_observation(polarity, answer)
    _welford_update(session["traits_latent"][trait], x)

    return session


def compute_final_scores(session: dict) -> Dict[str, float]:
    """
    Convertit les scores bruts en pourcentages 0–100.
    Moyenne des contributions answer×polarity ∈ [−ANSWER_MAX, ANSWER_MAX] → [0, 100].
    """
    span = float(ANSWER_MAX)
    scores = session.get("scores", {})
    result = {}
    for trait in TRAITS:
        data = scores.get(trait, {})
        count = data.get("count", 0)
        if count == 0:
            result[trait] = 50.0  # valeur neutre par défaut
        else:
            raw_avg = data["total"] / count
            normalized = (raw_avg + span) / (2.0 * span) * 100.0
            result[trait] = round(max(0.0, min(100.0, normalized)), 1)
    return result


def get_trait_interpretation(trait: str, score: float) -> str:
    """Retourne une interprétation courte selon le score."""
    interpretations = {
        "O": {
            "low": "Vous appréciez la stabilité et les approches éprouvées.",
            "mid": "Vous équilibrez curiosité et pragmatisme.",
            "high": "Vous êtes naturellement curieux(se) et ouvert(e) aux nouvelles idées.",
        },
        "C": {
            "low": "Vous êtes flexible et spontané(e) dans votre approche.",
            "mid": "Vous combinez organisation et adaptabilité.",
            "high": "Vous êtes organisé(e), fiable et orienté(e) vers les objectifs.",
        },
        "E": {
            "low": "Vous êtes introverti(e) et retirez de l'énergie de la solitude.",
            "mid": "Vous vous épanouissez aussi bien en solo qu'en groupe.",
            "high": "Vous êtes énergisé(e) par les interactions sociales et l'entourage.",
        },
        "A": {
            "low": "Vous êtes direct(e) et défendez fermement vos opinions.",
            "mid": "Vous savez coopérer tout en affirmant vos besoins.",
            "high": "Vous êtes chaleureux(se), empathique et attentif(ve) aux autres.",
        },
        "N": {
            "low": "Vous êtes émotionnellement stable et résistant(e) au stress.",
            "mid": "Vous ressentez les émotions de manière équilibrée.",
            "high": "Vous êtes sensible et réactif(ve) aux situations de stress.",
        },
    }
    level = "low" if score < 35 else "high" if score > 65 else "mid"
    return interpretations.get(trait, {}).get(level, "")
