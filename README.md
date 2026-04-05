# personAI · Test de personnalité IA

Application web de test de personnalité adaptatif (modèle Big Five / OCEAN) avec rapport généré par intelligence artificielle.

- **Frontend** : Angular 21 (standalone components)
- **Backend** : FastAPI + Python
- **IA** : Groq (Llama 3.3) — rapport personnalisé ; reformulation des questions (optionnelle)
- **Email** : SMTP (ex. Gmail) — envoi automatique du rapport si configuré

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
# Puis renseigner GROQ_API_KEY, SMTP_USER, SMTP_PASSWORD dans .env

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
GROQ_API_KEY=gsk_...

SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=votre.adresse@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # mot de passe d'application Gmail
```

---

## Déploiement & configuration

### Variables d'environnement

| Variable | Description | Exemple | Obligatoire |
|----------|-------------|---------|-------------|
| `GROQ_API_KEY` | Clé API Groq pour la génération du rapport JSON (et reformulation si activée) | `gsk_...` | **Oui** pour un rapport IA en prod |
| `SMTP_HOST` | Serveur SMTP pour l’envoi du rapport | `smtp.gmail.com` | Non (sans SMTP, le rapport reste consultable dans l’app) |
| `SMTP_PORT` | Port SMTP (`465` SSL ou `587` STARTTLS) | `465` | Non |
| `SMTP_USER` | Compte d’envoi | `vous@gmail.com` | Non |
| `SMTP_PASSWORD` | Mot de passe ou mot de passe d’application | `abcd efgh ijkl mnop` | Non |
| `LLM_QUESTION_REFORMULATION` | Active la reformulation Groq des énoncés (`true` / `1` / `yes` / `on`) | `true` | Non |
| `SECRET_KEY` | Clé secrète pour signer cookies / sessions (utile derrière un reverse proxy avancé) | `changez-moi-en-prod` | Non (non utilisée par le code actuel ; recommandée pour extensions) |
| `CORS_ORIGINS` | Liste d’origines autorisées pour le front (si vous externalisez la config CORS) | `https://app.example.com` | Non (le CORS est codé dans `main.py` ; à adapter au déploiement) |

Autres variables utiles : `SMTP_FROM_NAME`, `GMAIL_USER` / `GMAIL_APP_PASSWORD` (alias documentés dans le backend).

### Lancement local (développement)

**Prérequis** : Python **3.11+** (3.10+ possible), Node.js **20+** et npm.

**Backend**

```bash
cd backend
python -m venv .venv
# Windows : .venv\Scripts\activate
# Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis éditer GROQ_API_KEY (et SMTP si besoin)
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm start
```

Ouvrir `http://localhost:4200` (proxy Angular vers l’API selon `proxy.conf.json`).

### Build production

**Frontend**

```bash
cd frontend
npm run build -- --configuration production
```

Les fichiers statiques sont générés dans `frontend/dist/frontend/` (servir avec nginx, Azure Static Web Apps, etc.).

**Backend**

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Adapter `--workers` au nombre de cœurs ; derrière un reverse proxy HTTPS, laisser le proxy gérer TLS.

### Démo sans SMTP

Si `SMTP_USER` / `SMTP_PASSWORD` (ou équivalent) ne sont pas définis, l’API génère tout de même le rapport et le renvoie au frontend (`GET /api/sessions/{id}/report`). L’utilisateur voit le rapport à l’écran ; seul l’envoi automatique par e-mail est désactivé (message d’avertissement côté serveur).

### Activation de la reformulation LLM

1. Définir `GROQ_API_KEY` et `LLM_QUESTION_REFORMULATION=true` dans `backend/.env`.
2. Redémarrer uvicorn.
3. Au démarrage du test et à chaque nouvelle question, l’énoncé peut être reformulé par le modèle ; la réponse JSON inclut `reformulated: true` lorsque le texte a effectivement changé (sinon `false`). Un log serveur `INFO` enregistre l’identifiant de question et la durée Groq.

### Tests automatisés (API)

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/test_api.py -v
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
│   ├── report_generator.py  — Génération du rapport via Groq
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
