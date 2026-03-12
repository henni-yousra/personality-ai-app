import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { QuizService } from '../../services/quiz.service';
import { Question, Progress } from '../../models/quiz.models';

@Component({
  selector: 'app-questionnaire',
  imports: [],
  templateUrl: './questionnaire.component.html',
  styleUrl: './questionnaire.component.css',
})
export class QuestionnaireComponent implements OnInit {
  sessionId = signal('');
  question = signal<Question | null>(null);
  progress = signal<Progress>({ current: 0, total: 10, percent: 0 });
  selectedAnswer = signal<number | null>(null);
  loading = signal(false);
  animating = signal(false);
  error = signal('');

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private quizService: QuizService
  ) {}

  ngOnInit(): void {
    this.sessionId.set(this.route.snapshot.paramMap.get('sessionId') ?? '');

    const state = history.state as { question?: Question; progress?: Progress };
    if (state?.question && state?.progress) {
      this.question.set(state.question);
      this.progress.set(state.progress);
    } else {
      // Session perdue — retourner à l'accueil
      this.router.navigate(['/']);
    }
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

  getOptionLabel(value: number): string {
    const labels: Record<number, string> = {
      1: 'Pas du tout',
      2: 'Peu',
      3: 'Neutre',
      4: 'Plutôt',
      5: 'Tout à fait',
    };
    return labels[value] ?? '';
  }
}
