import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { QuizService } from '../../services/quiz.service';
import { Report, TraitScore } from '../../models/quiz.models';

@Component({
  selector: 'app-results',
  imports: [DecimalPipe],
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

  getScoreLevel(score: number): 'low' | 'mid' | 'high' {
    if (score < 35) return 'low';
    if (score > 65) return 'high';
    return 'mid';
  }

  getScoreColor(score: number): string {
    const level = this.getScoreLevel(score);
    if (level === 'high') return 'var(--sage)';
    if (level === 'low') return 'var(--lavender)';
    return 'var(--sand)';
  }

  orderedTraits(): Array<[string, TraitScore]> {
    const r = this.report();
    if (!r) return [];
    return this.traitOrder
      .filter((k) => r.traits[k])
      .map((k) => [k, r.traits[k]]);
  }
}
