"""
API FastAPI — Test de personnalité adaptatif par IA
Endpoints (CDC §4) :
  GET  /questions/start?email=&consent=   — Démarrer (équivalent POST /api/sessions)
  POST /responses                        — Réponse (équivalent POST /api/sessions/{id}/responses)
Endpoints hérités :
  POST /api/sessions, POST /api/sessions/{id}/responses, GET /api/sessions/{id}, …
"""

import uuid
from pathlib import Path

from dotenv import load_dotenv

# Charge backend/.env même si uvicorn est lancé depuis la racine du dépôt
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir.parent / ".env")

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    StartSessionRequest,
    AnswerRequest,
    CdcSubmitResponseBody,
    SessionStartResponse,
    AnswerResponse,
    ReportResponse,
    ResendEmailResponse,
    Progress,
    SessionStateResponse,
    SessionResumeProgress,
)
from storage import create_session, load_session, save_session
from adaptive_engine import select_next_question, update_scores, build_question
from report_generator import generate_report
from email_service import send_report_email
from llm_questions import maybe_reformulate_question_text
from question_bank import TOTAL_QUESTIONS

app = FastAPI(
    title="Personality AI API",
    description="API pour le test de personnalité adaptatif Big Five",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_progress(session: dict) -> Progress:
    """current = index 1-based de la question affichée (ou N si terminé)."""
    total = TOTAL_QUESTIONS
    n = len(session.get("responses", []))
    completed = bool(session.get("completed"))
    if completed or n >= total:
        current = total
    else:
        current = n + 1
    return Progress(
        current=current,
        total=total,
        percent=round(min(current, total) / total * 100, 1),
    )


def _reconstruct_report_from_cache(report_dict) -> "Report":
    """Reconstructs Report object from cached session data."""
    from models import Report, TraitScore, Archetype

    traits = {k: TraitScore(**v) for k, v in report_dict["traits"].items()}
    return Report(
        archetype=Archetype(**report_dict["archetype"]),
        overall_summary=report_dict["overall_summary"],
        traits=traits,
        strengths=report_dict["strengths"],
        areas_of_attention=report_dict["areas_of_attention"],
        recommendations=report_dict["recommendations"],
        disclaimer=report_dict["disclaimer"],
    )


def _validate_session_for_response(session_id: str) -> dict:
    """Validates session exists and that the test is still in progress."""
    session = load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    if session.get("completed"):
        raise HTTPException(status_code=400, detail="Ce test est déjà terminé.")
    return session


def _core_start_session(body: StartSessionRequest) -> SessionStartResponse:
    if not body.consent:
        raise HTTPException(status_code=400, detail="Le consentement est requis.")
    if not body.email or "@" not in body.email:
        raise HTTPException(status_code=400, detail="Adresse e-mail invalide.")

    session_id = str(uuid.uuid4())
    session = create_session(session_id, body.email)

    question, selection_reason = select_next_question(session)
    if question is None:
        raise HTTPException(status_code=500, detail="Impossible de charger les questions.")

    question = question.model_copy(
        update={"text": maybe_reformulate_question_text(question.text)}
    )
    session["used_question_ids"].append(question.id)
    save_session(session_id, session)

    return SessionStartResponse(
        session_id=session_id,
        question=question,
        progress=_build_progress(session),
        selection_reason=selection_reason,
    )


def _core_submit_response(session_id: str, body: AnswerRequest) -> AnswerResponse:
    session = _validate_session_for_response(session_id)
    if body.answer not in range(1, 6):
        raise HTTPException(status_code=400, detail="La réponse doit être comprise entre 1 et 5.")

    from question_bank import QUESTIONS
    raw_q = next((q for q in QUESTIONS if q["id"] == body.question_id), None)
    if raw_q is None:
        raise HTTPException(status_code=400, detail="Question introuvable.")

    session["responses"].append({
        "question_id": body.question_id,
        "question_text": raw_q["text"],
        "trait": raw_q["trait"],
        "polarity": raw_q["polarity"],
        "answer": body.answer,
        "answered_at": datetime.utcnow().isoformat(),
    })

    session = update_scores(session, body.question_id, body.answer)

    answered_count = len(session["responses"])
    if answered_count >= TOTAL_QUESTIONS:
        session["completed"] = True
        save_session(session_id, session)
        return AnswerResponse(
            question=None,
            completed=True,
            progress=_build_progress(session),
            selection_reason=None,
        )

    next_q, selection_reason = select_next_question(session)
    if next_q is None:
        session["completed"] = True
        save_session(session_id, session)
        return AnswerResponse(
            question=None,
            completed=True,
            progress=_build_progress(session),
            selection_reason=None,
        )

    next_q = next_q.model_copy(
        update={"text": maybe_reformulate_question_text(next_q.text)}
    )
    session["used_question_ids"].append(next_q.id)
    save_session(session_id, session)

    return AnswerResponse(
        question=next_q,
        completed=False,
        progress=_build_progress(session),
        selection_reason=selection_reason,
    )


@app.get("/")
def root():
    return {"message": "Personality AI API — en ligne"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/sessions/{session_id}", response_model=SessionStateResponse)
def get_session_state(session_id: str):
    """Retourne l'état de la session pour reprise après rechargement."""
    session = load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session introuvable.")

    from question_bank import QUESTIONS

    completed = bool(session.get("completed"))
    responses = session.get("responses", [])
    used_ids = session.get("used_question_ids", [])
    answered = len(responses)

    progress = SessionResumeProgress(answered=answered, total=TOTAL_QUESTIONS)

    if completed or answered >= TOTAL_QUESTIONS:
        return SessionStateResponse(
            completed=True,
            current_question_index=TOTAL_QUESTIONS,
            current_question=None,
            progress=progress,
        )

    if answered >= len(used_ids):
        raise HTTPException(
            status_code=500,
            detail="État de session incohérent (question courante introuvable).",
        )

    qid = used_ids[answered]
    raw_q = next((q for q in QUESTIONS if q["id"] == qid), None)
    if raw_q is None:
        raise HTTPException(status_code=500, detail="Question en cours introuvable dans la banque.")

    current_question = build_question(raw_q)
    current_question_index = answered + 1

    return SessionStateResponse(
        completed=False,
        current_question_index=current_question_index,
        current_question=current_question,
        progress=progress,
    )


@app.get("/questions/start", response_model=SessionStartResponse)
def questions_start(email: str, consent: bool = False):
    """Démarrage du test (contrat CDC) — query : email, consent."""
    return _core_start_session(StartSessionRequest(email=email, consent=consent))


@app.post("/responses", response_model=AnswerResponse)
def responses_cdc(body: CdcSubmitResponseBody):
    """Soumission d'une réponse (contrat CDC)."""
    if body.answer_value not in range(1, 6):
        raise HTTPException(status_code=400, detail="La réponse doit être comprise entre 1 et 5.")
    return _core_submit_response(
        body.session_id,
        AnswerRequest(question_id=body.question_id, answer=body.answer_value),
    )


@app.post("/api/sessions", response_model=SessionStartResponse)
def start_session(body: StartSessionRequest):
    """Crée une nouvelle session et retourne la première question (rétrocompat)."""
    return _core_start_session(body)


@app.post("/api/sessions/{session_id}/responses", response_model=AnswerResponse)
def submit_response(session_id: str, body: AnswerRequest):
    """Enregistre une réponse (rétrocompat)."""
    return _core_submit_response(session_id, body)


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
        report = _reconstruct_report_from_cache(session["report"])
        return ReportResponse(report=report, email=session["email"])

    # Générer le rapport via Claude
    try:
        report = await generate_report(session)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Mettre en cache dans la session
    session["report"] = report.model_dump()
    save_session(session_id, session)

    # Envoyer le rapport par e-mail (le rapport reste disponible même si l'envoi échoue)
    ok, mail_reason = send_report_email(session["email"], report)
    if not ok:
        if mail_reason == "missing_credentials":
            print(
                "[WARN] Rapport généré mais e-mail non envoyé : "
                "SMTP_USER/SMTP_PASSWORD (ou GMAIL_USER/GMAIL_APP_PASSWORD) non définis."
            )
        else:
            print("[WARN] Rapport généré mais e-mail non envoyé (échec SMTP — voir logs).")

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

    report = _reconstruct_report_from_cache(session["report"])
    success, mail_reason = send_report_email(session["email"], report)

    if not success:
        if mail_reason == "missing_credentials":
            detail = (
                "Envoi d'e-mail non configuré. Définissez SMTP_USER et SMTP_PASSWORD "
                "dans l'environnement du backend (ou GMAIL_USER et GMAIL_APP_PASSWORD). "
                "Pour Gmail : compte Google → Sécurité → validation en deux étapes → "
                "mots de passe des applications."
            )
        else:
            detail = (
                "L'envoi SMTP a échoué (réseau, port, identifiants ou blocage du fournisseur). "
                "Vérifiez SMTP_HOST, SMTP_PORT (465 SSL ou 587 STARTTLS), le compte et le mot de passe ; "
                "consultez les logs du serveur pour le détail."
            )
        raise HTTPException(status_code=503, detail=detail)

    session["resend_count"] = resend_count + 1
    session["last_resend"] = datetime.utcnow().isoformat()
    save_session(session_id, session)

    return ResendEmailResponse(
        success=True,
        message=f"Rapport renvoyé à {session['email']}",
    )
