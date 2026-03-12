import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  StartSessionRequest,
  SessionStartResponse,
  AnswerRequest,
  AnswerResponse,
  ReportResponse,
} from '../models/quiz.models';

@Injectable({ providedIn: 'root' })
export class QuizService {
  private readonly apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  startSession(body: StartSessionRequest): Observable<SessionStartResponse> {
    return this.http.post<SessionStartResponse>(`${this.apiUrl}/sessions`, body);
  }

  submitAnswer(sessionId: string, body: AnswerRequest): Observable<AnswerResponse> {
    return this.http.post<AnswerResponse>(
      `${this.apiUrl}/sessions/${sessionId}/responses`,
      body
    );
  }

  getReport(sessionId: string): Observable<ReportResponse> {
    return this.http.get<ReportResponse>(`${this.apiUrl}/sessions/${sessionId}/report`);
  }

  resendReport(sessionId: string): Observable<{ success: boolean; message: string }> {
    return this.http.post<{ success: boolean; message: string }>(
      `${this.apiUrl}/sessions/${sessionId}/resend`,
      {}
    );
  }
}
