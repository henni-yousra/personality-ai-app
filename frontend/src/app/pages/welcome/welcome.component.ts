import { Component, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

const STORAGE_FIRST = 'quiz_profile_first_name';
const STORAGE_INTERESTS = 'quiz_profile_interests';

@Component({
  selector: 'app-welcome',
  imports: [RouterLink],
  templateUrl: './welcome.component.html',
  styleUrl: './welcome.component.css',
})
export class WelcomeComponent {
  firstName = signal('');
  readonly chips = ['Sport', 'Créativité', 'Tech', 'Nature', 'Social', 'Lecture'];
  selected = signal<Set<string>>(new Set());

  constructor(private router: Router) {}

  toggleChip(label: string): void {
    const next = new Set(this.selected());
    if (next.has(label)) {
      next.delete(label);
    } else {
      next.add(label);
    }
    this.selected.set(next);
  }

  isSelected(label: string): boolean {
    return this.selected().has(label);
  }

  continue(): void {
    try {
      localStorage.setItem(STORAGE_FIRST, this.firstName().trim());
      localStorage.setItem(STORAGE_INTERESTS, JSON.stringify([...this.selected()]));
    } catch {
      /* ignore */
    }
    this.router.navigate(['/commencer']);
  }

  get canContinue(): boolean {
    return this.firstName().trim().length >= 1;
  }
}
