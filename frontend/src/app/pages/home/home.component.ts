import { Component, signal } from '@angular/core';
import { Router } from '@angular/router';
import { QuizService } from '../../services/quiz.service';

@Component({
  selector: 'app-home',
  imports: [],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
})
export class HomeComponent {
  email = signal('');
  consent = signal(false);
  loading = signal(false);
  error = signal('');

  constructor(private quizService: QuizService, private router: Router) {}

  get canStart(): boolean {
    return this.email().includes('@') && this.consent() && !this.loading();
  }

  startTest(): void {
    if (!this.canStart) return;

    this.loading.set(true);
    this.error.set('');

    this.quizService
      .startSession({ email: this.email(), consent: this.consent() })
      .subscribe({
        next: (res) => {
          this.router.navigate(['/questionnaire', res.session_id], {
            state: { question: res.question, progress: res.progress },
          });
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(
            err?.error?.detail ||
              'Une erreur est survenue. Veuillez réessayer.'
          );
        },
      });
  }
}
