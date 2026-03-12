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

export interface SessionStartResponse {
  session_id: string;
  question: Question;
  progress: Progress;
}

export interface AnswerResponse {
  question: Question | null;
  completed: boolean;
  progress: Progress;
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
