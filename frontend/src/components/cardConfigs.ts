export interface CardConfig {
  id: string;
  label: string;
  eyebrow: string;
  backgroundColor: string;
  accentColor: string;
  iconPath: string;
  drillRoute: string;
  placeholder: string;
}

export const CARD_CONFIGS: CardConfig[] = [
  {
    id: 'daily-outlook',
    label: 'DAILY OUTLOOK',
    eyebrow: 'CARD 1 OF 7',
    backgroundColor:
      'linear-gradient(160deg, #3b1f6e 0%, #5B2D8E 55%, #3b1f6e 100%)',
    accentColor: '#c4b5fd',
    iconPath:
      'M12 2v2 M12 20v2 M4.22 4.22l1.42 1.42 M18.36 18.36l1.42 1.42 M2 12h2 M20 12h2 M4.22 19.78l1.42-1.42 M18.36 5.64l1.42-1.42 M12 6a6 6 0 1 0 0 12 6 6 0 0 0 0-12z',
    drillRoute: '/dashboard/tools?tab=daily-outlook',
    placeholder: '',
  },
  {
    id: 'vibe-roster',
    label: 'VIBE & ROSTER',
    eyebrow: 'CARD 2 OF 7',
    backgroundColor:
      'linear-gradient(160deg, #2a1a3a 0%, #5b3a7e 55%, #2a1a3a 100%)',
    accentColor: '#e9d5ff',
    iconPath:
      'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
    drillRoute: '/dashboard/tools?tab=vibe-checkups',
    placeholder: '',
  },
  {
    id: 'cash-snapshot',
    label: 'CASH SNAPSHOT',
    eyebrow: 'CARD 3 OF 7',
    backgroundColor:
      'linear-gradient(160deg, #1a3a2a 0%, #1e5c3a 55%, #1a3a2a 100%)',
    accentColor: '#6ee7b7',
    iconPath: 'M12 2v20 M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6',
    drillRoute: '/dashboard/forecast',
    placeholder: '',
  },
  {
    id: 'career',
    label: 'CAREER CHECK-IN',
    eyebrow: 'CARD 4 OF 7',
    backgroundColor:
      'linear-gradient(160deg, #1a1a3a 0%, #2d2d6e 55%, #1a1a3a 100%)',
    accentColor: '#a5b4fc',
    iconPath:
      'M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2',
    drillRoute: '/dashboard/tools?tab=recommendations',
    placeholder: '',
  },
  {
    id: 'vehicle',
    label: 'VEHICLE CHECK-IN',
    eyebrow: 'CARD 5 OF 7',
    backgroundColor:
      'linear-gradient(160deg, #1a2a3a 0%, #1e4a6e 55%, #1a2a3a 100%)',
    accentColor: '#7dd3fc',
    iconPath:
      'M5 17H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v9a2 2 0 0 1-2 2h-2 M7 17a2 2 0 1 0 4 0 2 2 0 0 0-4 0 M17 17a2 2 0 1 0 4 0 2 2 0 0 0-4 0',
    drillRoute: '/dashboard/tools?tab=vehicle',
    placeholder: '',
  },
  {
    id: 'housing',
    label: 'HOUSING CHECK-IN',
    eyebrow: 'CARD 6 OF 7',
    backgroundColor:
      'linear-gradient(160deg, #2a1a1a 0%, #6e2d2d 40%, #3b1f6e 100%)',
    accentColor: '#fbbf24',
    iconPath: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10',
    drillRoute: '/dashboard/tools?tab=housing',
    placeholder: '',
  },
  {
    id: 'wellness',
    label: 'WELLNESS CHECK-IN',
    eyebrow: 'CARD 7 OF 7',
    backgroundColor:
      'linear-gradient(160deg, #1a2a1a 0%, #2d6e3a 55%, #1a2a1a 100%)',
    accentColor: '#86efac',
    iconPath:
      'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z',
    drillRoute: '/dashboard/tools?tab=wellness',
    placeholder: 'Wellness data — wired in D11',
  },
];
