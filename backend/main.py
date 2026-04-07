"""
API FastAPI — Test de personnalité adaptatif par IA
Endpoints (CDC §4) :
  GET  /questions/start?email=&consent=   — Démarrer (équivalent POST /api/sessions)
  POST /responses                        — Réponse (équivalent POST /api/sessions/{id}/responses)
Endpoints hérités :
  POST /api/sessions, POST /api/sessions/{id}/responses, GET /api/sessions/{id}, …
"""

import os
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
from llm_questions import maybe_prepare_question_text
from question_bank import TOTAL_QUESTIONS, QUESTIONS, question_option_values

app = FastAPI(
    title="personAI API",
    description="API pour le test de personnalité adaptatif Big Five",
    version="1.0.0",
)

def _env_truthy(name: str) -> bool:
    v = os.getenv(name, "")
    return v.strip().lower() in ("1", "true", "yes", "on")


# Local + origines prod (CORS_ORIGINS : URLs séparées par des virgules, sans slash final)
_cors_local = ["http://localhost:4200", "http://127.0.0.1:4200"]
_cors_extra = [
    o.strip().rstrip("/")
    for o in os.getenv("CORS_ORIGINS", "").split(",")
    if o.strip()
]
_cors_allow = list(dict.fromkeys(_cors_local + _cors_extra))

# Localhost (tous ports) ; hébergeurs statiques courants si Render ou CORS_ALLOW_NETLIFY (sauf CORS_STRICT)
_cors_regex_local = r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"

# Sous-domaines typiques des fronts gratuits (démo / TP) — combinés avec CORS_ORIGINS pour domaines perso.
_cors_regex_static_hosts = (
    "((?i)^https://[\\w-]+\\.netlify\\.app$)|"
    "((?i)^https://[\\w-]+\\.vercel\\.app$)|"
    "((?i)^https://[a-z0-9][a-z0-9-]*\\.github\\.io$)|"
    "((?i)^https://[\\w-]+\\.pages\\.dev$)"
)


def _cors_origin_regex_build() -> str:
    if _env_truthy("CORS_STRICT"):
        if _env_truthy("CORS_ALLOW_NETLIFY"):
            return f"({_cors_regex_local})|((?i)^https://[\\w-]+\\.netlify\\.app$)"
        return _cors_regex_local
    if _env_truthy("CORS_ALLOW_NETLIFY"):
        return f"({_cors_regex_local})|((?i)^https://[\\w-]+\\.netlify\\.app$)"
    if os.getenv("RENDER", "").strip().lower() == "true":
        return f"({_cors_regex_local})|({_cors_regex_static_hosts})"
    return _cors_regex_local


_cors_origin_regex = _cors_origin_regex_build()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow,
    allow_origin_regex=_cors_origin_regex,
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


def _question_displays(session: dict) -> dict:
    d = session.setdefault("question_displays", {})
    if not isinstance(d, dict):
        session["question_displays"] = {}
        return session["question_displays"]
    return d


def _remember_question_display(
    session: dict,
    question_id: str,
    text: str,
    reformulated: bool,
    generated: bool,
) -> None:
    _question_displays(session)[question_id] = {
        "text": text,
        "reformulated": bool(reformulated),
        "generated": bool(generated),
    }


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

    q_text, was_reformulated, was_generated = maybe_prepare_question_text(
        question.text,
        question.id,
        [o.label for o in question.options],
    )
    question = question.model_copy(update={"text": q_text})
    _remember_question_display(
        session, question.id, q_text, was_reformulated, was_generated
    )
    session["used_question_ids"].append(question.id)
    save_session(session_id, session)

    return SessionStartResponse(
        session_id=session_id,
        question=question,
        progress=_build_progress(session),
        selection_reason=selection_reason,
        reformulated=was_reformulated,
        generated=was_generated,
    )


def _core_submit_response(session_id: str, body: AnswerRequest) -> AnswerResponse:
    session = _validate_session_for_response(session_id)
    raw_q = next((q for q in QUESTIONS if q["id"] == body.question_id), None)
    if raw_q is None:
        raise HTTPException(status_code=400, detail="Question introuvable.")
    allowed = question_option_values(raw_q)
    if body.answer not in allowed:
        raise HTTPException(
            status_code=400,
            detail="La valeur de réponse ne correspond pas aux options de cette question.",
        )

    answer_label = next(
        (o["label"] for o in raw_q["options"] if o["value"] == body.answer),
        str(body.answer),
    )

    session["responses"].append({
        "question_id": body.question_id,
        "question_text": raw_q["text"],
        "trait": raw_q["trait"],
        "polarity": raw_q["polarity"],
        "answer": body.answer,
        "answer_label": answer_label,
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
            reformulated=False,
            generated=False,
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
            reformulated=False,
            generated=False,
        )

    n_text, n_ref, n_gen = maybe_prepare_question_text(
        next_q.text,
        next_q.id,
        [o.label for o in next_q.options],
    )
    next_q = next_q.model_copy(update={"text": n_text})
    _remember_question_display(session, next_q.id, n_text, n_ref, n_gen)
    session["used_question_ids"].append(next_q.id)
    save_session(session_id, session)

    return AnswerResponse(
        question=next_q,
        completed=False,
        progress=_build_progress(session),
        selection_reason=selection_reason,
        reformulated=n_ref,
        generated=n_gen,
    )


@app.get("/")
def root():
    return {"message": "personAI API — en ligne"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/sessions/{session_id}", response_model=SessionStateResponse)
def get_session_state(session_id: str):
    """Retourne l'état de la session pour reprise après rechargement."""
    session = load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session introuvable.")

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
            reformulated=False,
            generated=False,
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

    disp = _question_displays(session).get(qid)
    was_ref = False
    was_gen = False
    if isinstance(disp, dict) and isinstance(disp.get("text"), str):
        current_question = current_question.model_copy(update={"text": disp["text"]})
        was_ref = bool(disp.get("reformulated"))
        was_gen = bool(disp.get("generated"))
    else:
        # Anciennes sessions sans cache : même pipeline que le démarrage, puis enregistrement.
        t, was_ref, was_gen = maybe_prepare_question_text(
            current_question.text,
            current_question.id,
            [o.label for o in current_question.options],
        )
        current_question = current_question.model_copy(update={"text": t})
        _remember_question_display(session, qid, t, was_ref, was_gen)
        save_session(session_id, session)

    return SessionStateResponse(
        completed=False,
        current_question_index=current_question_index,
        current_question=current_question,
        progress=progress,
        reformulated=was_ref,
        generated=was_gen,
    )


@app.get("/questions/start", response_model=SessionStartResponse)
def questions_start(email: str, consent: bool = False):
    """Démarrage du test (contrat CDC) — query : email, consent."""
    return _core_start_session(StartSessionRequest(email=email, consent=consent))


@app.post("/responses", response_model=AnswerResponse)
def responses_cdc(body: CdcSubmitResponseBody):
    """Soumission d'une réponse (contrat CDC)."""
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
                "Envoi d'e-mail non configuré. Dans le fichier backend/.env (ou les "
                "variables d'environnement du processus uvicorn), définissez SMTP_USER et "
                "SMTP_PASSWORD, ou GMAIL_USER et GMAIL_APP_PASSWORD. Redémarrez le serveur "
                "après modification. Pour Gmail : compte Google → Sécurité → validation en "
                "deux étapes → mots de passe des applications."
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
