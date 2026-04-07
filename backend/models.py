from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
from datetime import datetime


class StartSessionRequest(BaseModel):
    email: str
    consent: bool


class AnswerRequest(BaseModel):
    question_id: str
    answer: int  # valeur de l’option choisie (voir `options` de la question)


class CdcSubmitResponseBody(BaseModel):
    """Corps POST /responses (contrat CDC §4)."""

    session_id: str
    question_id: str
    answer_value: int


class AnswerOption(BaseModel):
    value: int
    label: str


class Question(BaseModel):
    id: str
    text: str
    trait: str
    polarity: int  # 1 ou -1
    options: List[AnswerOption]


class Progress(BaseModel):
    current: int
    total: int
    percent: float


class SessionStartResponse(BaseModel):
    session_id: str
    question: Question
    progress: Progress
    selection_reason: Optional[str] = None
    reformulated: bool = False
    generated: bool = False


class AnswerResponse(BaseModel):
    question: Optional[Question] = None
    completed: bool
    progress: Progress
    selection_reason: Optional[str] = None
    reformulated: bool = False
    generated: bool = False


class TraitScore(BaseModel):
    score: float        # 0–100
    label: str
    emoji: str
    interpretation: str


class Archetype(BaseModel):
    name: str
    emoji: str
    tagline: str
    description: str


class Report(BaseModel):
    archetype: Archetype
    overall_summary: str
    traits: Dict[str, TraitScore]
    strengths: List[str]
    areas_of_attention: List[str]
    recommendations: List[str]
    disclaimer: str


class ReportResponse(BaseModel):
    report: Report
    email: str


class ResendEmailResponse(BaseModel):
    success: bool
    message: str


class SessionResumeProgress(BaseModel):
    """Progression pour reprise de session (réponses déjà enregistrées)."""

    answered: int
    total: int


class SessionStateResponse(BaseModel):
    """État courant d'une session (reprise après rechargement)."""

    completed: bool
    current_question_index: int
    current_question: Optional[Question] = None
    progress: SessionResumeProgress
