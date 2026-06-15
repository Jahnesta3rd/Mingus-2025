export interface LifeReadyScoreComponent {
  score: number;
  weight: number;
  active?: boolean;
}

export interface LifeAlert {
  domain: string;
  severity: 'high' | 'moderate' | 'watch';
  headline: string;
  detail: string;
  action_label: string;
  action_target: string;
}

export interface LifeReadyScoreApiResponse {
  life_ready_score: number | null;
  /** When omitted (legacy), treat as sufficient if ``life_ready_score`` is a number. */
  has_sufficient_data?: boolean;
  pillars_complete?: number;
  pillars_total?: number;
  components: {
    vibe: LifeReadyScoreComponent;
    body: LifeReadyScoreComponent;
    wellness: LifeReadyScoreComponent;
    financial: LifeReadyScoreComponent;
    stability: LifeReadyScoreComponent;
    roof?: LifeReadyScoreComponent;
    career?: LifeReadyScoreComponent;
    vehicle?: LifeReadyScoreComponent;
  };
  trend: 'improving' | 'declining' | 'stable' | null;
  headline: string | null;
  /** Always present on current API; may be absent on legacy responses. */
  life_alerts?: LifeAlert[];
}
