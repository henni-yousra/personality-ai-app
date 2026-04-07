import { Component, inject } from '@angular/core';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-theme-toggle',
  imports: [],
  template: `
    <button
      type="button"
      class="theme-toggle"
      (click)="theme.toggle()"
      [attr.aria-pressed]="theme.dark()"
      [attr.aria-label]="
        theme.dark() ? 'Passer en mode clair' : 'Passer en mode sombre'
      "
      [title]="theme.dark() ? 'Mode clair' : 'Mode sombre'"
    >
      <i
        class="pi"
        [class.pi-moon]="!theme.dark()"
        [class.pi-sun]="theme.dark()"
        aria-hidden="true"
      ></i>
    </button>
  `,
  styles: `
    .theme-toggle {
      position: fixed;
      top: 1rem;
      right: 1rem;
      z-index: 1100;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 2.75rem;
      height: 2.75rem;
      padding: 0;
      border-radius: var(--radius-md, 16px);
      border: 1px solid var(--border);
      background: var(--bg-card);
      color: var(--text-primary);
      box-shadow: var(--shadow-sm);
      cursor: pointer;
      transition:
        background var(--transition, 0.35s ease),
        border-color var(--transition, 0.35s ease),
        color var(--transition, 0.35s ease),
        transform 0.2s ease;
    }

    .theme-toggle:hover {
      background: var(--bg-secondary);
      border-color: var(--color-indigo-soft);
      color: var(--color-indigo);
    }

    .theme-toggle:focus-visible {
      outline: 2px solid var(--color-violet);
      outline-offset: 3px;
    }

    .theme-toggle:active {
      transform: scale(0.96);
    }

    .theme-toggle .pi {
      font-size: 1.15rem;
    }

    @media (max-width: 480px) {
      .theme-toggle {
        top: 0.65rem;
        right: 0.65rem;
        width: 2.5rem;
        height: 2.5rem;
      }
    }
  `,
})
export class ThemeToggleComponent {
  readonly theme = inject(ThemeService);
}
