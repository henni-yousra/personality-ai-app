export interface AnswerOption {
  value: number;
  label: string;
}

export interface Question {
  id: string;
  text: string;
  trait: string;
  polarity: number;
  options: AnswerOption[];
}

export interface Progress {
  current: number;
  total: number;
  percent: number;
}

/** Progression renvoyée par GET /api/sessions/{id} (reprise de session). */
export interface SessionResumeProgress {
  answered: number;
  total: number;
}

export interface SessionStateResponse {
  completed: boolean;
  current_question_index: number;
  current_question: Question | null;
  progress: SessionResumeProgress;
}

export interface SessionStartResponse {
  session_id: string;
  question: Question;
  progress: Progress;
  selection_reason?: string | null;
  reformulated?: boolean;
}

export interface AnswerResponse {
  question: Question | null;
  completed: boolean;
  progress: Progress;
  selection_reason?: string | null;
  reformulated?: boolean;
}

export interface TraitScore {
  score: number;
  label: string;
  emoji: string;
  interpretation: string;
}

export interface Archetype {
  name: string;
  emoji: string;
  tagline: string;
  description: string;
}

export interface Report {
  archetype: Archetype;
  overall_summary: string;
  traits: Record<string, TraitScore>;
  strengths: string[];
  areas_of_attention: string[];
  recommendations: string[];
  disclaimer: string;
}

export interface ReportResponse {
  report: Report;
  email: string;
}

export interface StartSessionRequest {
  email: string;
  consent: boolean;
}

export interface AnswerRequest {
  question_id: string;
  answer: number;
}
