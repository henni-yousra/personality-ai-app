import { Component } from '@angular/core';
import { Location } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { Button } from 'primeng/button';

export interface BigFiveTraitInfo {
  key: string;
  name: string;
  icon: string;
  summary: string;
  lowPole: string;
  highPole: string;
}

@Component({
  selector: 'app-big-five-traits',
  imports: [RouterLink, Button],
  templateUrl: './big-five-traits.component.html',
  styleUrl: './big-five-traits.component.css',
})
export class BigFiveTraitsComponent {
  readonly traits: BigFiveTraitInfo[] = [
    {
      key: 'O',
      name: 'Ouverture à l’expérience',
      icon: 'pi pi-lightbulb',
      summary:
        'Mesure la curiosité intellectuelle, l’imaginatif et l’intérêt pour les idées nouvelles, l’art et l’inconnu.',
      lowPole: 'Préférence pour le concret, les habitudes et les solutions éprouvées.',
      highPole: 'Curiosité, créativité et aisance face à la nouveauté et à l’abstraction.',
    },
    {
      key: 'C',
      name: 'Conscienciosité',
      icon: 'pi pi-list-check',
      summary:
        'Reflet de l’organisation, de la persévérance et du souci du détail dans les objectifs et les engagements.',
      lowPole: 'Souplesse parfois désorganisée, spontanéité, moindre planification.',
      highPole: 'Rigueur, fiabilité, discipline et sens des responsabilités.',
    },
    {
      key: 'E',
      name: 'Extraversion',
      icon: 'pi pi-users',
      summary:
        'Indique le besoin de stimulation sociale, l’énergie dans les interactions et l’expression en groupe.',
      lowPole: 'Réserve, besoin de calme ; l’énergie se recharge souvent en solitaire.',
      highPole: 'Sociabilité, enthousiasme et confort dans les situations animées.',
    },
    {
      key: 'A',
      name: 'Agréabilité',
      icon: 'pi pi-heart',
      summary:
        'Décrit la tendance à la coopération, à l’empathie et à la recherche de l’entente plutôt qu’au conflit.',
      lowPole: 'Franchise directe, esprit critique ou compétitif plus marqué.',
      highPole: 'Bienveillance, confiance et souci de l’harmonie avec autrui.',
    },
    {
      key: 'N',
      name: 'Névrosisme (stabilité émotionnelle inverse)',
      icon: 'pi pi-chart-line',
      summary:
        'Estime la sensibilité au stress, aux inquiétudes et aux variations d’humeur (un score plus haut = plus de vulnérabilité émotionnelle).',
      lowPole: 'Calme relatif, résilience face aux imprévus.',
      highPole: 'Réactivité émotionnelle plus forte, anxiété ou irritabilité plus fréquentes.',
    },
  ];

  constructor(
    readonly location: Location,
    private readonly router: Router
  ) {}

  goBack(): void {
    this.location.back();
  }

  goHome(): void {
    void this.router.navigate(['/']);
  }
}
