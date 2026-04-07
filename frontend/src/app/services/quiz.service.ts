import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  StartSessionRequest,
  SessionStartResponse,
  AnswerRequest,
  AnswerResponse,
  ReportResponse,
  SessionStateResponse,
} from '../models/quiz.models';

@Injectable({ providedIn: 'root' })
export class QuizService {
  private readonly api = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getSessionState(sessionId: string): Observable<SessionStateResponse> {
    return this.http.get<SessionStateResponse>(`${this.api}/api/sessions/${sessionId}`);
  }

  /** Contrat CDC §4 : GET /questions/start */
  startSession(body: StartSessionRequest): Observable<SessionStartResponse> {
    const params = new HttpParams()
      .set('email', body.email)
      .set('consent', String(body.consent));
    return this.http.get<SessionStartResponse>(`${this.api}/questions/start`, { params });
  }

  /** Contrat CDC §4 : POST /responses */
  submitAnswer(sessionId: string, body: AnswerRequest): Observable<AnswerResponse> {
    return this.http.post<AnswerResponse>(`${this.api}/responses`, {
      session_id: sessionId,
      question_id: body.question_id,
      answer_value: body.answer,
    });
  }

  getReport(sessionId: string): Observable<ReportResponse> {
    return this.http.get<ReportResponse>(`${this.api}/api/sessions/${sessionId}/report`);
  }

  resendReport(sessionId: string): Observable<{ success: boolean; message: string }> {
    return this.http.post<{ success: boolean; message: string }>(
      `${this.api}/api/sessions/${sessionId}/resend`,
      {}
    );
  }
}
