/**
 * Maps API-provided emoji (or legacy geometric markers) to PrimeIcons classes.
 * Use as: [class]="primeIconClassFromEmoji(x)" or class="{{ primeIconClassFromEmoji(x) }}"
 */
const EMOJI_TO_PI: Record<string, string> = {
  '✨': 'pi-sparkles',
  '📩': 'pi-envelope',
  '🌧': 'pi-cloud',
  '⏱': 'pi-clock',
  '⏱️': 'pi-clock',
  '✓': 'pi-check',
  '✔': 'pi-check',
  '✔️': 'pi-check',
  '✦': 'pi-star',
  '🌱': 'pi-chart-line',
  '🧭': 'pi-compass',
  '⚡': 'pi-bolt',
  '🎯': 'pi-bullseye',
  '☀': 'pi-sun',
  '☀️': 'pi-sun',
  '💛': 'pi-heart-fill',
  '🌊': 'pi-wave-pulse',
  '🔮': 'pi-eye',
  '🌿': 'pi-sun',
  '◉': 'pi-circle-on',
  '■': 'pi-stop',
  '▲': 'pi-caret-up',
  '◆': 'pi-star',
  '●': 'pi-circle-fill',
};

export function primeIconClassFromEmoji(emoji: string | null | undefined): string {
  if (!emoji) return 'pi pi-sparkles';
  const t = emoji.trim();
  const suffix = EMOJI_TO_PI[t] ?? (EMOJI_TO_PI[[...t][0] ?? ''] ?? 'pi-sparkles');
  return `pi ${suffix}`;
}
