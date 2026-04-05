import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { Button } from 'primeng/button';
import { Message } from 'primeng/message';
import { QuizService } from '../../services/quiz.service';
import { Report, TraitScore } from '../../models/quiz.models';
import { primeIconClassFromEmoji } from '../../utils/prime-icon-from-emoji';

@Component({
  selector: 'app-results',
  imports: [DecimalPipe, RouterLink, Button, Message],
  templateUrl: './results.component.html',
  styleUrl: './results.component.css',
})
export class ResultsComponent implements OnInit {
  sessionId = signal('');
  report = signal<Report | null>(null);
  email = signal('');
  loading = signal(true);
  error = signal('');
  resendLoading = signal(false);
  resendSuccess = signal('');
  resendError = signal('');

  readonly traitOrder = ['O', 'C', 'E', 'A', 'N'];

  readonly primeIconClassFromEmoji = primeIconClassFromEmoji;

  /** Icônes PrimeNG fixes par dimension Big Five (évite l’affichage d’emojis dans l’UI). */
  traitPrimeIconClass(traitKey: string): string {
    const map: Record<string, string> = {
      O: 'pi pi-lightbulb',
      C: 'pi pi-list-check',
      E: 'pi pi-users',
      A: 'pi pi-heart',
      N: 'pi pi-chart-line',
    };
    return map[traitKey] ?? 'pi pi-circle';
  }

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private quizService: QuizService
  ) {}

  ngOnInit(): void {
    this.sessionId.set(this.route.snapshot.paramMap.get('sessionId') ?? '');
    this.loadReport();
  }

  private loadReport(): void {
    this.quizService.getReport(this.sessionId()).subscribe({
      next: (res) => {
        this.report.set(res.report);
        this.email.set(res.email);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(
          err?.error?.detail || 'Erreur lors du chargement du rapport.'
        );
      },
    });
  }

  resendReport(): void {
    if (this.resendLoading()) return;
    this.resendLoading.set(true);
    this.resendSuccess.set('');
    this.resendError.set('');

    this.quizService.resendReport(this.sessionId()).subscribe({
      next: (res) => {
        this.resendLoading.set(false);
        this.resendSuccess.set(res.message);
        setTimeout(() => this.resendSuccess.set(''), 4000);
      },
      error: (err) => {
        this.resendLoading.set(false);
        this.resendError.set(
          err?.error?.detail || 'Erreur lors du renvoi du rapport.'
        );
        setTimeout(() => this.resendError.set(''), 4000);
      },
    });
  }

  startAgain(): void {
    this.router.navigate(['/']);
  }

  getTraitScore(key: string): TraitScore | undefined {
    return this.report()?.traits?.[key];
  }

  /** Couleur du texte du score (lisible sur fond clair). */
  getTraitScoreColor(traitKey: string): string {
    const c = this.traitPalette[traitKey];
    return c?.solid ?? '#454545';
  }

  /** Dégradé pour la barre de score selon le trait Big Five. */
  getTraitBarGradient(traitKey: string): string {
    const c = this.traitPalette[traitKey];
    return c?.gradient ?? 'linear-gradient(90deg, #4a6741, #6b8c3a)';
  }

  private readonly traitPalette: Record<
    string,
    { solid: string; gradient: string }
  > = {
    O: { solid: '#87aabf', gradient: 'linear-gradient(90deg, #6e8fa5, #a8c4d4)' },
    C: { solid: '#8b6a3a', gradient: 'linear-gradient(90deg, #6b4f2a, #a08255)' },
    E: { solid: '#d4a843', gradient: 'linear-gradient(90deg, #c49a2e, #e8c84a)' },
    A: { solid: '#6b8c3a', gradient: 'linear-gradient(90deg, #4a6741, #a3c45a)' },
    N: { solid: '#c47a5a', gradient: 'linear-gradient(90deg, #a85f42, #d4947a)' },
  };

  orderedTraits(): Array<[string, TraitScore]> {
    const r = this.report();
    if (!r) return [];
    return this.traitOrder
      .filter((k) => r.traits[k])
      .map((k) => [k, r.traits[k]]);
  }
}
