# personAI · Test de personnalité IA

Application web de test de personnalité adaptatif (modèle Big Five / OCEAN) avec rapport généré par intelligence artificielle.

- **Frontend** : Angular 21 (standalone components)
- **Backend** : FastAPI + Python
- **IA** : Claude API (claude-opus-4-6) — génération de rapport personnalisé
- **Email** : SMTP Gmail — rapport envoyé automatiquement

Projet réalisé dans le cadre de l'UE TPALT — Sorbonne Sciences.

---

## Lancer l'application

### 1. Backend (FastAPI)

**Prérequis** : Python 3.10+

```bash
# Aller dans le dossier backend
cd backend

# Installer les dépendances (première fois)
pip3 install -r requirements.txt

# Créer le fichier .env à partir de l'exemple
cp .env.example .env
# Puis renseigner ANTHROPIC_API_KEY, SMTP_USER, SMTP_PASSWORD dans .env

# Lancer le serveur
python3 -m uvicorn main:app --reload
```

Le backend tourne sur **http://localhost:8000**

> Si le port est déjà occupé : `kill $(lsof -ti:8000)` puis relancer.

---

### 2. Frontend (Angular)

**Prérequis** : Node.js 18+ et npm

```bash
# Aller dans le dossier frontend
cd frontend

# Installer les dépendances (première fois)
npm install

# Lancer le serveur de développement
npm start
```

L'application est accessible sur **http://localhost:4200**

---

## Variables d'environnement

Créer un fichier `backend/.env` :

```env
ANTHROPIC_API_KEY=sk-ant-...

SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=votre.adresse@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # mot de passe d'application Gmail
```

---

## Architecture

```
personality-ai-app/
├── backend/
│   ├── main.py              — API FastAPI (tous les endpoints)
│   ├── models.py            — Modèles Pydantic
│   ├── question_bank.py     — 30 questions Big Five (15 posées par session)
│   ├── adaptive_engine.py   — Scoring et sélection adaptative
│   ├── report_generator.py  — Génération du rapport via Claude API
│   ├── email_service.py     — Envoi du rapport par email (SMTP)
│   ├── storage.py           — Stockage des sessions (JSON)
│   ├── data/sessions/       — Fichiers sessions
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/
        │   ├── pages/home/          — Page d'accueil
        │   ├── pages/questionnaire/ — Quiz adaptatif
        │   ├── pages/loading/       — Génération du rapport
        │   └── pages/results/       — Rapport Big Five
        └── styles.css               — Design system
```

---

## Fonctionnalités

- Questionnaire adaptatif (15 questions sur 30, sélectionnées dynamiquement)
- Scoring Big Five (OCEAN) en temps réel
- Rapport personnalisé généré par IA (streaming)
- Envoi automatique du rapport par email
- Design zen responsive
