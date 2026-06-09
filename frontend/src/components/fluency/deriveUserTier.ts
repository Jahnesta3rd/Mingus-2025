import type { UserTier } from './types';

type AuthUserLike = {
  tier?: string | null;
  is_beta?: boolean | null;
} | null | undefined;

/** Matches LifeLedgerWidget tier derivation. */
export function deriveUserTier(user: AuthUserLike): UserTier {
  if (user?.is_beta === true || user?.tier === 'professional') {
    return 'professional';
  }
  if (user?.tier === 'mid_tier') {
    return 'mid_tier';
  }
  return 'budget';
}
