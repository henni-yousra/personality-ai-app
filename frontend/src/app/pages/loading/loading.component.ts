import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { QuizService } from '../../services/quiz.service';

const MESSAGES = [
  'Analyse de vos réponses en cours…',
  'Identification de vos traits de personnalité…',
  'Génération de votre profil unique…',
  'Rédaction de votre rapport personnalisé…',
  'Finalisation de votre rapport…',
];

@Component({
  selector: 'app-loading',
  imports: [],
  templateUrl: './loading.component.html',
  styleUrl: './loading.component.css',
})
export class LoadingComponent implements OnInit {
  sessionId = signal('');
  currentMessage = signal(MESSAGES[0]);
  error = signal('');

  private messageIndex = 0;
  private interval: ReturnType<typeof setInterval> | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private quizService: QuizService
  ) {}

  ngOnInit(): void {
    this.sessionId.set(this.route.snapshot.paramMap.get('sessionId') ?? '');

    // Rotation des messages
    this.interval = setInterval(() => {
      this.messageIndex = (this.messageIndex + 1) % MESSAGES.length;
      this.currentMessage.set(MESSAGES[this.messageIndex]);
    }, 2800);

    // Déclencher la génération du rapport après un court délai (UX)
    setTimeout(() => this.fetchReport(), 800);
  }

  private fetchReport(): void {
    this.quizService.getReport(this.sessionId()).subscribe({
      next: () => {
        if (this.interval) clearInterval(this.interval);
        this.router.navigate(['/results', this.sessionId()]);
      },
      error: (err) => {
        if (this.interval) clearInterval(this.interval);
        this.error.set(
          err?.error?.detail ||
            'Une erreur est survenue lors de la génération du rapport.'
        );
      },
    });
  }

  retry(): void {
    this.error.set('');
    this.messageIndex = 0;
    this.currentMessage.set(MESSAGES[0]);
    this.interval = setInterval(() => {
      this.messageIndex = (this.messageIndex + 1) % MESSAGES.length;
      this.currentMessage.set(MESSAGES[this.messageIndex]);
    }, 2800);
    this.fetchReport();
  }
}
