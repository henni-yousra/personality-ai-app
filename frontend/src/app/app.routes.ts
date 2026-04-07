import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/home/home.component').then((m) => m.HomeComponent),
  },
  {
    path: 'commencer',
    redirectTo: '',
    pathMatch: 'full',
  },
  {
    path: 'questionnaire/:sessionId',
    loadComponent: () =>
      import('./pages/questionnaire/questionnaire.component').then(
        (m) => m.QuestionnaireComponent
      ),
  },
  {
    path: 'loading/:sessionId',
    loadComponent: () =>
      import('./pages/loading/loading.component').then((m) => m.LoadingComponent),
  },
  {
    path: 'results/:sessionId',
    loadComponent: () =>
      import('./pages/results/results.component').then((m) => m.ResultsComponent),
  },
  {
    path: 'big-five',
    loadComponent: () =>
      import('./pages/big-five-traits/big-five-traits.component').then(
        (m) => m.BigFiveTraitsComponent
      ),
  },
  {
    path: '**',
    redirectTo: '',
  },
];
