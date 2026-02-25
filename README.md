# Personality AI 

Application web de test de personnalité adaptatif utilisant :
- Angular 19 (Frontend)
- FastAPI (Backend Python)
- Scoring adaptatif en temps réel

Projet réalisé dans le cadre de l'UE TPALT — Sorbonne Sciences.

---

## Architecture

personality-ai-app/
│
├── frontend/       → Angular 19 + PrimeNG
├── backend/        → FastAPI + scoring adaptatif
├── backend/data/   → Banque de questions JSON
│
└── README.md

---

## Fonctionnalités 

- Questionnaire adaptatif
- Scoring Big Five (OCEAN)
- API REST FastAPI
- Frontend Angular connecté

---

## 🛠 Installation

### 1️⃣ Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload