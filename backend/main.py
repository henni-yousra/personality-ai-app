"""
API FastAPI — Test de personnalité adaptatif par IA
Endpoints:
  POST /api/sessions              — Démarrer une session
  POST /api/sessions/{id}/responses — Soumettre une réponse
  GET  /api/sessions/{id}/report  — Obtenir le rapport final
  POST /api/sessions/{id}/resend  — Renvoyer le rapport par e-mail
"""

import uuid
import asyncio
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    StartSessionRequest,
    AnswerRequest,
    SessionStartResponse,
    AnswerResponse,
    ReportResponse,
    ResendEmailResponse,
    Progress,
)
from storage import create_session, load_session, save_session
from adaptive_engine import select_next_question, update_scores
from report_generator import generate_report
from email_service import send_report_email
from question_bank import TOTAL_QUESTIONS

app = FastAPI(
    title="Personality AI API",
    description="API pour le test de personnalité adaptatif Big Five",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_progress(session: dict) -> Progress:
    current = len(session.get("responses", []))
    total = TOTAL_QUESTIONS
    return Progress(
        current=current,
        total=total,
        percent=round(current / total * 100, 1),
    )


@app.get("/")
def root():
    return {"message": "Personality AI API — en ligne"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/sessions", response_model=SessionStartResponse)
def start_session(body: StartSessionRequest):
    """Crée une nouvelle session et retourne la première question."""
    if not body.consent:
        raise HTTPException(status_code=400, detail="Le consentement est requis.")
    if not body.email or "@" not in body.email:
        raise HTTPException(status_code=400, detail="Adresse e-mail invalide.")

    session_id = str(uuid.uuid4())
    session = create_session(session_id, body.email)

    question = select_next_question(session)
    if question is None:
        raise HTTPException(status_code=500, detail="Impossible de charger les questions.")

    # Enregistrer la première question utilisée
    session["used_question_ids"].append(question.id)
    save_session(session_id, session)

    return SessionStartResponse(
        session_id=session_id,
        question=question,
        progress=_build_progress(session),
    )


@app.post("/api/sessions/{session_id}/responses", response_model=AnswerResponse)
def submit_response(session_id: str, body: AnswerRequest):
    """Enregistre une réponse et retourne la prochaine question (ou signale la fin)."""
    session = load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    if session.get("completed"):
        raise HTTPException(status_code=400, detail="Ce test est déjà terminé.")
    if body.answer not in range(1, 6):
        raise HTTPException(status_code=400, detail="La réponse doit être comprise entre 1 et 5.")

    # Trouver la question correspondante dans la banque
    from question_bank import QUESTIONS
    raw_q = next((q for q in QUESTIONS if q["id"] == body.question_id), None)
    if raw_q is None:
        raise HTTPException(status_code=400, detail="Question introuvable.")

    # Enregistrer la réponse
    session["responses"].append({
        "question_id": body.question_id,
        "question_text": raw_q["text"],
        "trait": raw_q["trait"],
        "polarity": raw_q["polarity"],
        "answer": body.answer,
        "answered_at": datetime.utcnow().isoformat(),
    })

    # Mettre à jour les scores
    session = update_scores(session, body.question_id, body.answer)

    # Vérifier si le test est terminé
    answered_count = len(session["responses"])
    if answered_count >= TOTAL_QUESTIONS:
        session["completed"] = True
        save_session(session_id, session)
        return AnswerResponse(
            question=None,
            completed=True,
            progress=_build_progress(session),
        )

    # Sélectionner la prochaine question
    next_q = select_next_question(session)
    if next_q is None:
        session["completed"] = True
        save_session(session_id, session)
        return AnswerResponse(
            question=None,
            completed=True,
            progress=_build_progress(session),
        )

    session["used_question_ids"].append(next_q.id)
    save_session(session_id, session)

    return AnswerResponse(
        question=next_q,
        completed=False,
        progress=_build_progress(session),
    )


@app.get("/api/sessions/{session_id}/report", response_model=ReportResponse)
async def get_report(session_id: str):
    """Génère (ou récupère) le rapport de personnalité."""
    session = load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    if not session.get("completed"):
        raise HTTPException(status_code=400, detail="Le test n'est pas encore terminé.")

    # Retourner le rapport en cache si déjà généré
    if session.get("report"):
        from models import Report, TraitScore, Archetype
        report_data = session["report"]
        traits = {
            k: TraitScore(**v) for k, v in report_data["traits"].items()
        }
        report = Report(
            archetype=Archetype(**report_data["archetype"]),
            overall_summary=report_data["overall_summary"],
            traits=traits,
            strengths=report_data["strengths"],
            areas_of_attention=report_data["areas_of_attention"],
            recommendations=report_data["recommendations"],
            disclaimer=report_data["disclaimer"],
        )
        return ReportResponse(report=report, email=session["email"])

    # Générer le rapport via Claude
    try:
        report = await generate_report(session)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Mettre en cache dans la session
    session["report"] = report.model_dump()
    save_session(session_id, session)

    # Envoyer le rapport par e-mail
    send_report_email(session["email"], report)

    return ReportResponse(report=report, email=session["email"])


@app.post("/api/sessions/{session_id}/resend", response_model=ResendEmailResponse)
def resend_report(session_id: str):
    """Renvoie le rapport par e-mail (avec limite anti-spam : 3 max)."""
    session = load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    if not session.get("report"):
        raise HTTPException(status_code=400, detail="Le rapport n'a pas encore été généré.")

    resend_count = session.get("resend_count", 0)
    if resend_count >= 3:
        raise HTTPException(
            status_code=429,
            detail="Limite de renvoi atteinte (3 maximum).",
        )

    # Reconstruire l'objet Report depuis le cache
    from models import Report, TraitScore, Archetype
    report_data = session["report"]
    traits = {k: TraitScore(**v) for k, v in report_data["traits"].items()}
    report = Report(
        archetype=Archetype(**report_data["archetype"]),
        overall_summary=report_data["overall_summary"],
        traits=traits,
        strengths=report_data["strengths"],
        areas_of_attention=report_data["areas_of_attention"],
        recommendations=report_data["recommendations"],
        disclaimer=report_data["disclaimer"],
    )

    success = send_report_email(session["email"], report)

    session["resend_count"] = resend_count + 1
    session["last_resend"] = datetime.utcnow().isoformat()
    save_session(session_id, session)

    if not success:
        raise HTTPException(
            status_code=503,
            detail="Impossible d'envoyer l'e-mail. Vérifiez la configuration GMAIL_USER et GMAIL_APP_PASSWORD.",
        )

    return ResendEmailResponse(
        success=True,
        message=f"Rapport renvoyé à {session['email']}",
    )
