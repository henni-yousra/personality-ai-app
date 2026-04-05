"""
Tests d'intégration HTTP de l'API FastAPI (sessions, réponses, rapport).
Routes réelles : POST /api/sessions, POST /api/sessions/{id}/responses,
GET /api/sessions/{id}, GET /api/sessions/{id}/report (pas GET /api/report/{id}).
"""

import json
import uuid
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

import storage as storage_mod


@pytest.fixture(autouse=True)
def isolate_storage(tmp_path, monkeypatch):
    """Chaque test utilise un répertoire de sessions vide et indépendant."""
    d = tmp_path / "sessions"
    d.mkdir(parents=True)
    monkeypatch.setattr(storage_mod, "DATA_DIR", d)


def _trait_block():
    interp = (
        "Première phrase détaillée pour décrire ce trait et son niveau. "
        "Deuxième phrase pour nuancer et proposer une lecture constructive du profil."
    )
    traits = {}
    for key, label, emoji in [
        ("O", "Ouverture", "🔭"),
        ("C", "Conscienciosité", "📋"),
        ("E", "Extraversion", "👥"),
        ("A", "Agréabilité", "💚"),
        ("N", "Névrosisme", "📊"),
    ]:
        traits[key] = {
            "score": 55.0,
            "label": label,
            "emoji": emoji,
            "interpretation": interp,
        }
    return traits


MOCK_LLM_REPORT_JSON = json.dumps(
    {
        "overall_summary": "Profil équilibré avec des nuances intéressantes pour la démonstration.",
        "traits": _trait_block(),
        "strengths": ["Curiosité", "Régularité", "Empathie"],
        "areas_of_attention": ["Gestion du stress", "Priorisation"],
        "recommendations": [
            "Prévoir des pauses régulières.",
            "Structurer les tâches par blocs de temps.",
            "Communiquer ses limites avec clarté.",
        ],
        "disclaimer": (
            "Ce rapport est informatif et non médical. Il ne constitue pas un diagnostic "
            "psychologique. Consultez un professionnel pour tout accompagnement spécialisé."
        ),
    },
    ensure_ascii=False,
)


@pytest.fixture
async def api_client():
    """Client HTTP async branché sur l'application ASGI."""
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_session_valid(api_client: AsyncClient):
    """Création de session avec e-mail et consentement valides → 200 et première question."""
    r = await api_client.post(
        "/api/sessions",
        json={"email": "user@example.com", "consent": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert data.get("question", {}).get("id")
    assert data.get("progress", {}).get("total") >= 1
    assert "reformulated" in data
    assert isinstance(data["reformulated"], bool)


@pytest.mark.asyncio
async def test_create_session_missing_email_422(api_client: AsyncClient):
    """Corps sans e-mail → erreur de validation FastAPI (422)."""
    r = await api_client.post(
        "/api/sessions",
        json={"consent": True},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_session_consent_refused_400(api_client: AsyncClient):
    """Consentement explicite refusé → 400 métier."""
    r = await api_client.post(
        "/api/sessions",
        json={"email": "refus@example.com", "consent": False},
    )
    assert r.status_code == 400
    assert "consentement" in r.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_submit_answer_updates_progress(api_client: AsyncClient):
    """Soumission d'une réponse valide : progression incrémentée et question suivante ou fin."""
    start = await api_client.post(
        "/api/sessions",
        json={"email": "quiz@example.com", "consent": True},
    )
    assert start.status_code == 200
    body = start.json()
    sid = body["session_id"]
    qid = body["question"]["id"]
    first_current = body["progress"]["current"]

    ans = await api_client.post(
        f"/api/sessions/{sid}/responses",
        json={"question_id": qid, "answer": 1},
    )
    assert ans.status_code == 200
    data = ans.json()
    assert data["completed"] is False or data.get("question") is None
    if not data["completed"]:
        assert data["progress"]["current"] == first_current + 1
        assert "reformulated" in data
    # Score partiel : les agrégats sont en session ; l'API expose au minimum la progression.
    assert data["progress"]["total"] >= 1


@pytest.mark.asyncio
async def test_submit_answer_unknown_session_404(api_client: AsyncClient):
    """Soumission pour une session inexistante → 404."""
    fake = str(uuid.uuid4())
    r = await api_client.post(
        f"/api/sessions/{fake}/responses",
        json={"question_id": "O1", "answer": 1},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_report_after_full_session_mock_groq(
    api_client: AsyncClient, monkeypatch
):
    """Après N réponses complètes, GET rapport avec appel Groq mocké (pas de token)."""
    monkeypatch.setenv("GROQ_API_KEY", "test-key-for-mock")
    import main as main_mod
    import question_bank as qb_mod

    monkeypatch.setattr(qb_mod, "TOTAL_QUESTIONS", 1)
    monkeypatch.setattr(main_mod, "TOTAL_QUESTIONS", 1)

    start = await api_client.post(
        "/api/sessions",
        json={"email": "report@example.com", "consent": True},
    )
    assert start.status_code == 200
    sid = start.json()["session_id"]
    qid = start.json()["question"]["id"]

    with patch("report_generator._groq_once", return_value=MOCK_LLM_REPORT_JSON):
        sub = await api_client.post(
            f"/api/sessions/{sid}/responses",
            json={"question_id": qid, "answer": 1},
        )
        assert sub.status_code == 200
        assert sub.json()["completed"] is True

        rep = await api_client.get(f"/api/sessions/{sid}/report")
        assert rep.status_code == 200
        payload = rep.json()
        assert "report" in payload
        assert payload["report"]["overall_summary"]
        assert set(payload["report"]["traits"].keys()) == {"O", "C", "E", "A", "N"}
