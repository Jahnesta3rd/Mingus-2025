import { getAuthHeadersJson } from '../../hooks/useLifeLedger';
import type { WaterfallContext } from './types';

function csrfHeaders(): Record<string, string> {
  const token =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 'test-token';
  return { 'X-CSRF-Token': token };
}

export async function fetchWaterfallContext(): Promise<WaterfallContext> {
  const res = await fetch('/api/waterfall/context', {
    method: 'GET',
    credentials: 'include',
    headers: {
      ...getAuthHeadersJson(),
      ...csrfHeaders(),
    },
  });
  if (!res.ok) {
    throw new Error(`waterfall context ${res.status}`);
  }
  return (await res.json()) as WaterfallContext;
}
