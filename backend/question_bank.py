"""
Banque de questions Big Five (OCEAN).
Chaque question a ses propres libellés de réponse (3 ou 4 choix) ; les valeurs sont
des entiers consécutifs à partir de 1 pour l’API.

polarité  1 = option « forte » → score haut sur le trait
polarité -1 = question inversée (option « forte » sur l’énoncé → score bas sur le trait)
"""

from typing import Set, Tuple

QUESTIONS = [
    {
        "id": "O1",
        "text": "Quand on vous parle d’un sujet que vous ne connaissez pas, que faites-vous en général ?",
        "trait": "O",
        "polarity": 1,
        "difficulty": 1,
        "options": [
            {"value": 1, "label": "Je change vite de sujet"},
            {"value": 2, "label": "J’écoute sans creuser"},
            {"value": 3, "label": "Je pose des questions pour comprendre"},
            {"value": 4, "label": "Je creuse tout de suite (articles, vidéos…)"},
        ],
    },
    {
        "id": "O2",
        "text": "Les week-ends, vous préférez plutôt…",
        "trait": "O",
        "polarity": -1,
        "difficulty": 2,
        "options": [
            {"value": 1, "label": "Reproduire la même routine rassurante"},
            {"value": 2, "label": "Un mix habitudes et petites nouveautés"},
            {"value": 3, "label": "Souvent sortir de la routine"},
            {"value": 4, "label": "Improviser et tester du nouveau"},
        ],
    },
    {
        "id": "C1",
        "text": "Vous avez une échéance dans deux semaines. Comment vous y prenez-vous ?",
        "trait": "C",
        "polarity": 1,
        "difficulty": 1,
        "options": [
            {"value": 1, "label": "Je m’y mets la veille si je peux"},
            {"value": 2, "label": "J’avance par à-coups"},
            {"value": 3, "label": "Je découpe en étapes avec des jalons"},
            {"value": 4, "label": "Plan + marge dès le début, suivi régulier"},
        ],
    },
    {
        "id": "C2",
        "text": "Votre bureau ou espace de travail ressemble le plus souvent à…",
        "trait": "C",
        "polarity": 1,
        "difficulty": 2,
        "options": [
            {"value": 1, "label": "Un champ de bataille créatif"},
            {"value": 2, "label": "Des piles que je connais par cœur"},
            {"value": 3, "label": "Plutôt rangé avec quelques zones floues"},
            {"value": 4, "label": "Tout a sa place, facile à retrouver"},
        ],
    },
    {
        "id": "E1",
        "text": "Dans une soirée où vous ne connaissez presque personne, vous vous sentez…",
        "trait": "E",
        "polarity": 1,
        "difficulty": 1,
        "options": [
            {"value": 1, "label": "À l’étroit, j’attends de pouvoir partir"},
            {"value": 2, "label": "Un peu tendu(e), je reste en retrait"},
            {"value": 3, "label": "Ça va après un temps d’adaptation"},
            {"value": 4, "label": "Énergisé(e), j’aime faire connaissance"},
        ],
    },
    {
        "id": "E2",
        "text": "Après une longue journée bien remplie, idéal pour vous :",
        "trait": "E",
        "polarity": -1,
        "difficulty": 2,
        "options": [
            {"value": 1, "label": "Dîner entre amis ou appel à plusieurs"},
            {"value": 2, "label": "Un peu de social puis calme"},
            {"value": 3, "label": "Surtout calme, éventuellement une personne"},
            {"value": 4, "label": "Silence total, solo rechargé"},
        ],
    },
    {
        "id": "A1",
        "text": "Un collègue prend du retard sur une tâche commune et vous impacte. Votre premier réflexe :",
        "trait": "A",
        "polarity": 1,
        "difficulty": 2,
        "options": [
            {"value": 1, "label": "Je montre mon mécontentement clairement"},
            {"value": 2, "label": "Je fais remarquer les faits, sans détour"},
            {"value": 3, "label": "J’explique l’impact et on cherche une solution"},
            {"value": 4, "label": "Je privilégie l’écoute avant de réagir"},
        ],
    },
    {
        "id": "A2",
        "text": "On vous coupe la parole en réunion. Vous…",
        "trait": "A",
        "polarity": 1,
        "difficulty": 3,
        "options": [
            {"value": 1, "label": "Je reprends la parole tout de suite"},
            {"value": 2, "label": "J’attends une pause puis je complète calmement"},
            {"value": 3, "label": "Je m’efface pour la fluidité du groupe"},
        ],
    },
    {
        "id": "N1",
        "text": "La veille d’un entretien ou d’un examen important, vous…",
        "trait": "N",
        "polarity": 1,
        "difficulty": 1,
        "options": [
            {"value": 1, "label": "Dormez aussi bien que d’habitude"},
            {"value": 2, "label": "Une petite tension, vite passée"},
            {"value": 3, "label": "Des pensées qui tournent un moment"},
            {"value": 4, "label": "Peu dormi, scénarios qui tournent en boucle"},
        ],
    },
    {
        "id": "N2",
        "text": "Face à une décision importante, vous…",
        "trait": "N",
        "polarity": 1,
        "difficulty": 2,
        "options": [
            {"value": 1, "label": "Tranchez vite et assumez"},
            {"value": 2, "label": "Doutez un peu puis vous avancez"},
            {"value": 3, "label": "Comparez les options plusieurs fois"},
            {"value": 4, "label": "Hésitez longtemps, redoutez le mauvais choix"},
        ],
    },
]

TOTAL_QUESTIONS = 10

TRAIT_LABELS = {
    "O": "Ouverture",
    "C": "Conscienciosité",
    "E": "Extraversion",
    "A": "Agréabilité",
    "N": "Névrosisme",
}

TRAIT_EMOJIS = {
    "O": "◉",
    "C": "■",
    "E": "▲",
    "A": "◆",
    "N": "●",
}


def question_option_values(raw: dict) -> Set[int]:
    """Valeurs d’option valides pour une question."""
    return {o["value"] for o in raw["options"]}


def question_value_bounds(raw: dict) -> Tuple[int, int]:
    """Min et max des valeurs d’options (pour normaliser le score)."""
    vals = [o["value"] for o in raw["options"]]
    return min(vals), max(vals)
