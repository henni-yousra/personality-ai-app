import { DOCUMENT } from '@angular/common';
import { Injectable, inject, signal } from '@angular/core';

const STORAGE_KEY = 'personai-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly doc = inject(DOCUMENT);

  /** True when `data-theme="dark"` is applied on the document element. */
  readonly dark = signal(this.readDomIsDark());

  private readDomIsDark(): boolean {
    return this.doc.documentElement.getAttribute('data-theme') === 'dark';
  }

  setDark(value: boolean): void {
    this.dark.set(value);
    this.doc.documentElement.setAttribute('data-theme', value ? 'dark' : 'light');
    try {
      localStorage.setItem(STORAGE_KEY, value ? 'dark' : 'light');
    } catch {
      /* ignore quota / private mode */
    }
  }

  toggle(): void {
    this.setDark(!this.dark());
  }
}
