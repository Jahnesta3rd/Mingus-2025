export interface CompanyScreenQuestion {
  id: string;
  question_text: string;
  flag_source: string | null;
  display_order: number;
  dismissed_at: string | null;
  copied_at: string | null;
}

export interface Layer2Detail {
  jargon_density_score: number | null;
  role_clarity_score: number | null;
  values_authenticity_score: number | null;
  leadership_transparency_score: number | null;
  top_jargon_phrases: string[];
  scoring_notes: string | null;
  from_cache: boolean;
}

export interface Layer3Detail {
  confidence: 'high' | 'medium' | 'low' | null;
  red_flags: string[];
  positive_signals: string[];
  sentiment_summary: string | null;
  sample_threads: Array<{
    title: string;
    url: string;
    subreddit: string;
    score: number;
  }>;
  post_count: number;
}

export interface CompanyScreen {
  id: string;
  employer_name: string;
  employer_cik: string | null;
  composite_score: number | null;
  composite_band: 'strong' | 'mixed' | 'caution' | 'high_risk' | null;
  layer1_score: number | null;
  layer1_status: 'complete' | 'unavailable' | 'pending';
  layoff_event_detected: boolean;
  layoff_event_date: string | null;
  layer2_score: number | null;
  layer2_status: 'complete' | 'unavailable' | 'insufficient_text' | 'pending';
  layer2_detail: Layer2Detail;
  layer3_band: 'positive' | 'mixed' | 'negative' | 'insufficient_data' | null;
  layer3_status: 'complete' | 'unavailable' | 'insufficient_data' | 'pending';
  layer3_detail: Layer3Detail;
  questions: CompanyScreenQuestion[];
  created_at: string;
  expires_at: string;
  from_cache: boolean;
}

export interface ScreenHistoryItem extends CompanyScreen {}

export type CompositeBand = CompanyScreen['composite_band'];
export type Layer3Band = CompanyScreen['layer3_band'];
