# personAI · Test de personnalité IA

Application web de test de personnalité adaptatif (modèle Big Five / OCEAN) avec rapport généré par intelligence artificielle.

- **Frontend** : Angular 21 (standalone components)
- **Backend** : FastAPI + Python
- **IA** : Groq (Llama 3.3) — génération du rapport personnalisé + reformulation des questions (optionnelle)
- **Email** : SMTP (ex. Gmail) — envoi automatique du rapport si configuré

Réalisé par **Yousra Yasmine Henni Mansour** et **Samira Fawaz** — UE TPALT, Sorbonne Sciences.

---

## Lancer l'application en local

### Prérequis

- Python **3.10+** (3.11+ recommandé)
- Node.js **18+** et npm

### 1. Backend (FastAPI)

```bash
# Se placer dans le dossier backend
cd backend

# Installer les dépendances Python
pip3 install -r requirements.txt

# Copier le fichier de configuration et le remplir
cp .env.example .env
# → ouvrir backend/.env et renseigner les clés (voir section "Clés & tokens" ci-dessous)

# Lancer le serveur
python3 -m uvicorn main:app --reload
```

Le backend tourne sur **http://localhost:8000**

> Si le port 8000 est déjà utilisé : `kill $(lsof -ti:8000)` puis relancer.

### 2. Frontend (Angular)

Dans un **second terminal** :

```bash
cd frontend

# Installer les dépendances npm (première fois)
npm install

# Lancer le serveur de développement
npm start
```

L'application est accessible sur **http://localhost:4200**

Le proxy Angular redirige automatiquement les appels `/api/...` vers `http://localhost:8000`.

---

## Clés & tokens — où les modifier

Toute la configuration sensible se trouve dans **`backend/.env`** (fichier à créer à partir de `.env.example`, jamais versionné).

```env
# ── IA (obligatoire pour générer un rapport) ─────────────────────────────────
GROQ_API_KEY=gsk_...           # Clé API Groq → https://console.groq.com

# ── Email (optionnel) ─────────────────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com       # Serveur SMTP de votre fournisseur
SMTP_PORT=465                  # 465 (SSL) ou 587 (STARTTLS)
SMTP_USER=votre@gmail.com      # Adresse d'envoi
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Mot de passe d'application Gmail

# ── Options avancées ──────────────────────────────────────────────────────────
LLM_QUESTION_REFORMULATION=false   # Mettre à true pour activer la reformulation IA des questions
```

### Obtenir les clés

| Clé | Où la trouver |
|-----|---------------|
| `GROQ_API_KEY` | Créer un compte sur [console.groq.com](https://console.groq.com) → API Keys → Create API Key |
| `SMTP_PASSWORD` (Gmail) | Compte Google → Sécurité → Validation en 2 étapes → Mots de passe des applications |

> Sans `GROQ_API_KEY`, le rapport IA ne sera pas généré. Sans SMTP, le rapport s'affiche dans l'app mais n'est pas envoyé par e-mail.

---

## Comment l'IA est utilisée

L'IA intervient à **deux niveaux** dans l'application :

### 1. Sélection adaptative des questions (moteur à règles)

Après chaque réponse, `backend/adaptive_engine.py` :
- calcule les scores partiels par trait (O, C, E, A, N)
- identifie le trait avec la **plus grande incertitude** (variance maximale)
- sélectionne une question de difficulté adaptée depuis la banque (`question_bank.py`)

Ce moteur ne fait **pas appel à une API externe** — il est entièrement local.

### 2. Génération du rapport (LLM Groq)

À la fin des 15 questions, `backend/report_generator.py` appelle **Groq** (`llama-3.3-70b-versatile`) avec :
- les scores Big Five calculés (0–100 par trait)
- l'archétype de personnalité identifié (distance euclidienne)
- un prompt structuré imposant un format JSON strict

Le modèle génère en retour : résumé du profil, interprétation par trait, points forts, axes de développement, recommandations personnalisées, et disclaimer.

Le rapport est **mis en cache** dans le fichier de session JSON (`backend/data/sessions/<id>.json`) pour éviter un double appel.

### 3. Reformulation des questions (optionnel)

Si `LLM_QUESTION_REFORMULATION=true` dans `.env`, Groq peut reformuler l'énoncé de chaque question pour le rendre plus naturel. Activable/désactivable sans modifier le code.

---

## Déploiement

### Build du frontend

```bash
cd frontend
npm run build -- --configuration production
```

Les fichiers statiques sont générés dans `frontend/dist/frontend/browser/`.
À servir avec nginx, Vercel, Netlify, Azure Static Web Apps, etc.

### Lancement du backend en production

```bash
cd backend
pip3 install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Adapter `--workers` au nombre de cœurs disponibles. En production, placer un reverse proxy HTTPS (nginx, Caddy) devant uvicorn.

### Variables d'environnement en production

Sur votre hébergeur (Render, Railway, Heroku, etc.), définir les mêmes variables que dans `.env` :

| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `GROQ_API_KEY` | **Oui** | Clé API Groq |
| `SMTP_HOST` | Non | Serveur SMTP |
| `SMTP_PORT` | Non | Port SMTP |
| `SMTP_USER` | Non | Adresse d'envoi |
| `SMTP_PASSWORD` | Non | Mot de passe SMTP |
| `LLM_QUESTION_REFORMULATION` | Non | `true` pour activer la reformulation |
| `CORS_ORIGINS` | Non | URL du frontend en prod (ex. `https://monapp.vercel.app`) |

---

## Architecture

```
personality-ai-app/
├── backend/
│   ├── main.py              — API FastAPI (tous les endpoints)
│   ├── models.py            — Modèles Pydantic
│   ├── question_bank.py     — 30 questions Big Five (15 posées par session)
│   ├── adaptive_engine.py   — Moteur adaptatif + scoring Big Five
│   ├── report_generator.py  — Génération du rapport via Groq (LLM)
│   ├── email_service.py     — Envoi du rapport par e-mail (SMTP)
│   ├── storage.py           — Stockage des sessions (fichiers JSON)
│   ├── data/sessions/       — Sessions utilisateurs
│   ├── .env.example         — Modèle de configuration
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/
        │   ├── pages/home/          — Page d'accueil
        │   ├── pages/questionnaire/ — Quiz adaptatif
        │   ├── pages/loading/       — Écran de génération du rapport
        │   └── pages/results/       — Résultats Big Five
        └── styles.css               — Design system
```
