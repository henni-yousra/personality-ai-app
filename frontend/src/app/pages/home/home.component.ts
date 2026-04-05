import { Component, computed, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { InputText } from 'primeng/inputtext';
import { Checkbox } from 'primeng/checkbox';
import { Button } from 'primeng/button';
import { Message } from 'primeng/message';
import { QuizService } from '../../services/quiz.service';

@Component({
  selector: 'app-home',
  imports: [FormsModule, RouterLink, InputText, Checkbox, Button, Message],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
})
export class HomeComponent {
  email = signal('');
  consent = signal(false);
  loading = signal(false);
  error = signal('');

  /** Signal dérivé : le template doit lire ceci (et non un getter) pour mettre à jour [disabled]. */
  canStart = computed(() => {
    const e = this.email().trim();
    return e.includes('@') && this.consent() === true && !this.loading();
  });

  constructor(
    private quizService: QuizService,
    private router: Router
  ) {}

  startTest(): void {
    if (!this.canStart()) return;

    this.loading.set(true);
    this.error.set('');

    const email = this.email().trim();
    this.quizService
      .startSession({ email, consent: this.consent() })
      .subscribe({
        next: (res) => {
          this.loading.set(false);
          try {
            localStorage.setItem('quiz_session_id', res.session_id);
          } catch {
            /* ignore */
          }
          void this.router
            .navigate(['/questionnaire', res.session_id], {
              state: { question: res.question, progress: res.progress },
            })
            .then((ok) => {
              if (!ok) {
                this.error.set(
                  'Navigation impossible. Vérifiez la configuration du routeur.'
                );
              }
            });
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(this.formatStartError(err));
        },
      });
  }

  private formatStartError(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      if (err.status === 0) {
        return (
          'Impossible de joindre l’API. Démarrez le backend (port 8000) et utilisez `ng serve` ' +
          '(proxy vers le backend). Si vous ouvrez un build statique sans proxy, configurez environment.apiBaseUrl.'
        );
      }
      const d = err.error?.detail;
      if (typeof d === 'string') {
        return d;
      }
      if (Array.isArray(d)) {
        return d
          .map((e: { msg?: string }) => e.msg || JSON.stringify(e))
          .join(' ');
      }
      if (err.status === 404) {
        return 'Route introuvable sur le serveur — vérifiez que FastAPI est bien démarré et à jour.';
      }
    }
    return 'Une erreur est survenue. Veuillez réessayer.';
  }
}
