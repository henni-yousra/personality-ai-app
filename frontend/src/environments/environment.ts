/**
 * Chaîne vide : en `ng serve`, les appels passent par proxy.conf.json → backend :8000
 * (évite les erreurs CORS si vous utilisez 127.0.0.1, un autre port, etc.)
 */
export const environment = {
  production: false,
  apiBaseUrl: '',
};
