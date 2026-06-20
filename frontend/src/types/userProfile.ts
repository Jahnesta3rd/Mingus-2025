export interface UserProfileModules {
  vehicle_module?: boolean;
  housing_module?: boolean;
  career_pro?: boolean;
  family_addon?: boolean;
}

export interface UserProfile {
  id?: string;
  email?: string;
  name?: string;
  first_name?: string;
  last_name?: string;
  zip_code?: string;
  tier?: string;
  modules?: UserProfileModules;
  db_user_id?: number;
  current_balance?: number | null;
  balance_last_updated?: string | null;
  important_dates?: Record<string, unknown>;
  relationship_status?: string | null;
}
