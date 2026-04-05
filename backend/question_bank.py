"""
Banque de questions Big Five (OCEAN)
Chaque question est taguée par trait et polarité :
  polarité  1 = réponse haute → score haut
  polarité -1 = réponse haute → score bas (question inversée)
"""

QUESTIONS = [
    # ─── Ouverture (Openness) ─────────────────────────────────────────────────
    {
        "id": "O1",
        "text": "J'aime explorer de nouvelles idées et de nouveaux sujets.",
        "trait": "O",
        "polarity": 1,
    },
    {
        "id": "O2",
        "text": "Je suis attiré(e) par l'art, la musique ou la littérature.",
        "trait": "O",
        "polarity": 1,
    },
    {
        "id": "O3",
        "text": "Je préfère les routines connues plutôt que les nouvelles expériences.",
        "trait": "O",
        "polarity": -1,
    },
    {
        "id": "O4",
        "text": "J'aime imaginer des scénarios alternatifs et des mondes fictifs.",
        "trait": "O",
        "polarity": 1,
    },
    {
        "id": "O5",
        "text": "J'ai tendance à aborder les problèmes de façon créative et originale.",
        "trait": "O",
        "polarity": 1,
    },
    {
        "id": "O6",
        "text": "Les sujets abstraits ou philosophiques m'ennuient rapidement.",
        "trait": "O",
        "polarity": -1,
    },

    # ─── Conscienciosité (Conscientiousness) ──────────────────────────────────
    {
        "id": "C1",
        "text": "J'aime planifier mes tâches et suivre un planning précis.",
        "trait": "C",
        "polarity": 1,
    },
    {
        "id": "C2",
        "text": "Je termine toujours ce que j'ai commencé.",
        "trait": "C",
        "polarity": 1,
    },
    {
        "id": "C3",
        "text": "Je remets souvent les tâches importantes au lendemain.",
        "trait": "C",
        "polarity": -1,
    },
    {
        "id": "C4",
        "text": "Je fais attention aux détails et vérifie mon travail.",
        "trait": "C",
        "polarity": 1,
    },
    {
        "id": "C5",
        "text": "Je maintiens mes espaces (bureau, chambre) propres et organisés.",
        "trait": "C",
        "polarity": 1,
    },
    {
        "id": "C6",
        "text": "Il m'arrive fréquemment d'oublier des engagements ou des rendez-vous.",
        "trait": "C",
        "polarity": -1,
    },

    # ─── Extraversion ─────────────────────────────────────────────────────────
    {
        "id": "E1",
        "text": "Je me sens à l'aise pour engager la conversation avec des inconnus.",
        "trait": "E",
        "polarity": 1,
    },
    {
        "id": "E2",
        "text": "Je préfère passer du temps seul(e) plutôt qu'en groupe.",
        "trait": "E",
        "polarity": -1,
    },
    {
        "id": "E3",
        "text": "Les interactions sociales me donnent de l'énergie.",
        "trait": "E",
        "polarity": 1,
    },
    {
        "id": "E4",
        "text": "J'aime être au centre de l'attention lors de rassemblements.",
        "trait": "E",
        "polarity": 1,
    },
    {
        "id": "E5",
        "text": "Je parle facilement de moi-même et de mes expériences.",
        "trait": "E",
        "polarity": 1,
    },
    {
        "id": "E6",
        "text": "Je trouve les soirées et les événements sociaux épuisants.",
        "trait": "E",
        "polarity": -1,
    },

    # ─── Agréabilité (Agreeableness) ──────────────────────────────────────────
    {
        "id": "A1",
        "text": "Je ressens de l'empathie pour les personnes en difficulté.",
        "trait": "A",
        "polarity": 1,
    },
    {
        "id": "A2",
        "text": "J'évite les conflits et préfère trouver des compromis.",
        "trait": "A",
        "polarity": 1,
    },
    {
        "id": "A3",
        "text": "J'ai tendance à être critique envers les autres.",
        "trait": "A",
        "polarity": -1,
    },
    {
        "id": "A4",
        "text": "Je trouve facilement quelque chose de positif chez chaque personne.",
        "trait": "A",
        "polarity": 1,
    },
    {
        "id": "A5",
        "text": "Je prends soin des autres et j'aime les aider.",
        "trait": "A",
        "polarity": 1,
    },
    {
        "id": "A6",
        "text": "Dans une négociation, je cherche avant tout à gagner.",
        "trait": "A",
        "polarity": -1,
    },

    # ─── Névrosisme (Neuroticism) ──────────────────────────────────────────────
    {
        "id": "N1",
        "text": "Je m'inquiète facilement pour des choses qui pourraient mal tourner.",
        "trait": "N",
        "polarity": 1,
    },
    {
        "id": "N2",
        "text": "Mes humeurs sont stables et je change rarement d'état émotionnel.",
        "trait": "N",
        "polarity": -1,
    },
    {
        "id": "N3",
        "text": "Je me sens souvent stressé(e) ou sous pression.",
        "trait": "N",
        "polarity": 1,
    },
    {
        "id": "N4",
        "text": "Je récupère rapidement après un événement négatif.",
        "trait": "N",
        "polarity": -1,
    },
    {
        "id": "N5",
        "text": "Je peux facilement être envahi(e) par des émotions intenses.",
        "trait": "N",
        "polarity": 1,
    },
    {
        "id": "N6",
        "text": "Je reste calme dans des situations de pression ou d'urgence.",
        "trait": "N",
        "polarity": -1,
    },
]

# Difficulté (1 = la plus directe, 3 = la plus nuancée) — sélection adaptative
for _i, _q in enumerate(QUESTIONS):
    _q.setdefault("difficulty", (_i % 3) + 1)

TOTAL_QUESTIONS = 15  # Nombre de questions posées par session

# 4 choix de réponse (plus de grille 1–5) — valeurs 1..4 conservées pour l’API et le scoring
ANSWER_OPTIONS = [
    {"value": 1, "label": "Pas du tout"},
    {"value": 2, "label": "Plutôt non"},
    {"value": 3, "label": "Plutôt oui"},
    {"value": 4, "label": "Tout à fait"},
]

ANSWER_MIN = 1
ANSWER_MAX = 4

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
