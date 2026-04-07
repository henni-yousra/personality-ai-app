import { Component, OnInit, computed, signal } from '@angular/core';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { InputText } from 'primeng/inputtext';
import { Checkbox } from 'primeng/checkbox';
import { Button } from 'primeng/button';
import { Message } from 'primeng/message';
import { QuizService } from '../../services/quiz.service';
import { environment } from '../../../environments/environment';

const STORAGE_FIRST = 'quiz_profile_first_name';
const STORAGE_INTERESTS = 'quiz_profile_interests';

@Component({
  selector: 'app-home',
  imports: [FormsModule, InputText, Checkbox, Button, Message],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
})
export class HomeComponent implements OnInit {
  firstName = signal('');
  readonly chips = ['Sport', 'Créativité', 'Tech', 'Nature', 'Social', 'Lecture'];
  selected = signal<Set<string>>(new Set());

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

  ngOnInit(): void {
    try {
      const fn = localStorage.getItem(STORAGE_FIRST);
      if (fn) this.firstName.set(fn);
      const raw = localStorage.getItem(STORAGE_INTERESTS);
      if (raw) this.selected.set(new Set(JSON.parse(raw) as string[]));
    } catch {
      /* ignore */
    }
  }

  toggleChip(label: string): void {
    const next = new Set(this.selected());
    if (next.has(label)) next.delete(label);
    else next.add(label);
    this.selected.set(next);
  }

  isSelected(label: string): boolean {
    return this.selected().has(label);
  }

  startTest(): void {
    if (!this.canStart()) return;

    this.loading.set(true);
    this.error.set('');

    try {
      localStorage.setItem(STORAGE_FIRST, this.firstName().trim());
      localStorage.setItem(STORAGE_INTERESTS, JSON.stringify([...this.selected()]));
    } catch {
      /* ignore */
    }

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
              state: {
                question: res.question,
                progress: res.progress,
                reformulated:
                  res.reformulated === true || res.generated === true,
              },
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
        if (environment.apiBaseUrl) {
          return (
            'Connexion à l’API impossible. Vérifiez l’URL dans environment.prod.ts (HTTPS, sans slash final), ' +
            'que le déploiement Render utilise la dernière version du backend, et réessayez après ~1 min si l’instance ' +
            'était en veille. Front hors Netlify : définissez CORS_ORIGINS sur Render avec l’URL exacte de ce site.'
          );
        }
        return (
          'Impossible de joindre l’API en local. Démarrez le backend (port 8000) dans le dossier ' +
          '`backend`, puis `npm start` ici (proxy). Pour pointer vers l’API Render sans backend local : ' +
          '`npm run start:remote`.'
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
