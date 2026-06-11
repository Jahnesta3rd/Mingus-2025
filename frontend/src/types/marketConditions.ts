export interface MarketConditionsNational {
  layoff_rate: number;
  layoff_rate_label: string;
  mortgage_rate: number;
  mortgage_rate_label: string;
  cpi_yoy: number;
  cpi_label: string;
  data_date: string;
}

export interface MarketConditionsRegional {
  msa_name: string;
  unemployment_rate: number | null;
  housing_price_index: number | null;
  data_date: string;
}

export interface MarketConditionsPersonal {
  percentile: number;
  current_salary: number;
  pct_10: number;
  pct_25: number;
  pct_50: number;
  pct_75: number;
  pct_90: number;
  field_label: string;
  msa_name: string;
  wage_growth_yoy: number;
  source_year: number;
  above_median: boolean;
}

export interface MarketConditionsMeta {
  national_stale: boolean;
  regional_stale: boolean;
  personal_note: string | null;
}

export interface MarketConditionsResponse {
  national: MarketConditionsNational;
  regional: MarketConditionsRegional | null;
  personal: MarketConditionsPersonal | null;
  meta: MarketConditionsMeta;
}
