import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ProgressBar } from 'primeng/progressbar';
import { Button } from 'primeng/button';
import { Message } from 'primeng/message';
import { QuizService } from '../../services/quiz.service';
import { Question, Progress } from '../../models/quiz.models';

@Component({
  selector: 'app-questionnaire',
  imports: [RouterLink, ProgressBar, Button, Message],
  templateUrl: './questionnaire.component.html',
  styleUrl: './questionnaire.component.css',
})
export class QuestionnaireComponent implements OnInit {
  sessionId = signal('');
  question = signal<Question | null>(null);
  progress = signal<Progress>({ current: 0, total: 10, percent: 0 });
  selectedAnswer = signal<number | null>(null);
  loading = signal(false);
  resuming = signal(false);
  animating = signal(false);
  error = signal('');
  /** True si l’énoncé affiché a été reformulé par le LLM (réponse API). */
  questionReformulated = signal(false);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private quizService: QuizService
  ) {}

  ngOnInit(): void {
    let id = this.route.snapshot.paramMap.get('sessionId') ?? '';
    if (!id && typeof localStorage !== 'undefined') {
      const stored = localStorage.getItem('quiz_session_id');
      if (stored) {
        this.router.navigate(['/questionnaire', stored], { replaceUrl: true });
        return;
      }
    }
    this.sessionId.set(id);
    if (!id) {
      this.router.navigate(['/']);
      return;
    }

    const state = history.state as {
      question?: Question;
      progress?: Progress;
      reformulated?: boolean;
    };
    if (state?.question && state?.progress) {
      this.question.set(state.question);
      this.progress.set(state.progress);
      this.questionReformulated.set(state.reformulated === true);
      return;
    }

    this.resuming.set(true);
    this.quizService.getSessionState(id).subscribe({
      next: (s) => {
        this.resuming.set(false);
        if (s.completed) {
          this.router.navigate(['/results', id]);
          return;
        }
        if (!s.current_question) {
          this.router.navigate(['/']);
          return;
        }
        this.question.set(s.current_question);
        this.questionReformulated.set(false);
        const t = s.progress.total;
        const idx = s.current_question_index;
        const percent = t > 0 ? Math.round((idx / t) * 1000) / 10 : 0;
        this.progress.set({
          current: idx,
          total: t,
          percent,
        });
      },
      error: () => {
        this.resuming.set(false);
        this.router.navigate(['/']);
      },
    });
  }

  selectAnswer(value: number): void {
    if (this.loading()) return;
    this.selectedAnswer.set(value);
  }

  submitAnswer(): void {
    const answer = this.selectedAnswer();
    const q = this.question();
    if (answer === null || q === null || this.loading()) return;

    this.loading.set(true);
    this.error.set('');

    this.quizService
      .submitAnswer(this.sessionId(), { question_id: q.id, answer })
      .subscribe({
        next: (res) => {
          this.progress.set(res.progress);

          if (res.completed) {
            // Test terminé → page de chargement du rapport
            this.router.navigate(['/loading', this.sessionId()]);
            return;
          }

          // Animer la transition vers la prochaine question
          this.animating.set(true);
          setTimeout(() => {
            this.question.set(res.question);
            this.questionReformulated.set(res.reformulated === true);
            this.selectedAnswer.set(null);
            this.loading.set(false);
            this.animating.set(false);
          }, 350);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(
            err?.error?.detail || 'Erreur lors de l\'enregistrement. Réessayez.'
          );
        },
      });
  }

  get progressPercent(): number {
    return this.progress().percent;
  }

  primaryActionLabel(): string {
    if (this.loading()) return 'Traitement…';
    if (this.progress().current >= this.progress().total) return 'Terminer le test';
    return 'Suivant';
  }

  primaryActionIcon(): string | undefined {
    if (this.loading()) return undefined;
    if (this.progress().current >= this.progress().total) return 'pi pi-check';
    return 'pi pi-arrow-right';
  }
}
