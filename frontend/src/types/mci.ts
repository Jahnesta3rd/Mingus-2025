export type MCISeverity = "green" | "amber" | "red";
export type MCIDirection = "up" | "down" | "flat";
export type MCICompositeDirection = "improving" | "stable" | "deteriorating";

export interface MCIConstituent {
  name: string;
  slug: string;
  current_value: number;
  previous_value: number;
  direction: MCIDirection;
  severity: MCISeverity;
  headline: string;
  source: string;
  as_of: string;
  weight: number;
  raw: Record<string, unknown>;
}

export interface MCISnapshot {
  composite_score: number;
  composite_direction: MCICompositeDirection;
  composite_severity: MCISeverity;
  composite_headline: string;
  constituents: MCIConstituent[];
  snapshot_date: string;
  next_refresh: string;
}

export interface MCIContextValue {
  snapshot: MCISnapshot | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

