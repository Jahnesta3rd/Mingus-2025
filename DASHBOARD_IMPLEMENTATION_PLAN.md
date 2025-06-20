# Mingus Dashboard Implementation Plan

This document outlines the step-by-step process, code snippets, and architectural notes for implementing a modern, tabbed React dashboard with a calendar, scenario modeling, and Supabase integration.

---

## Table of Contents
- [Project Setup](#project-setup)
- [Project Structure](#project-structure)
- [Tailwind CSS Configuration](#tailwind-css-configuration)
- [Type Definitions](#type-definitions)
- [State Management (Zustand)](#state-management-zustand)
- [Main Dashboard Component](#main-dashboard-component)
- [Calendar Component](#calendar-component)
- [Tab Components](#tab-components)
- [Styling](#styling)
- [Supabase Integration](#supabase-integration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Scenario Tabs Overview](#scenario-tabs-overview)

---

## Project Setup

```bash
# Create a new React project with TypeScript
npx create-react-app mingus-dashboard --template typescript

# Install required dependencies
cd mingus-dashboard
npm install @supabase/supabase-js zustand react-calendar react-tooltip react-modal react-icons react-transition-group tailwindcss @headlessui/react
```

---

## Project Structure

```
mingus-dashboard/
├── src/
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── BaseCaseTab.tsx
│   │   │   ├── CareerGrowthTab.tsx
│   │   │   ├── EmergencyExpensesTab.tsx
│   │   │   └── HealthImpactTab.tsx
│   │   ├── common/
│   │   │   ├── TabNavigation.tsx
│   │   │   ├── StatusIndicator.tsx
│   │   │   └── CashFlowTimeline.tsx
│   │   └── calendar/
│   │       └── ImportantDatesCalendar.tsx
│   ├── store/
│   │   └── dashboardStore.ts
│   ├── types/
│   │   └── index.ts
│   └── App.tsx
```

---

## Tailwind CSS Configuration

```bash
# Initialize Tailwind CSS
npx tailwindcss init
```

---

## Type Definitions

```typescript
// src/types/index.ts
export interface ImportantDate {
  id: string;
  title: string;
  date: Date;
  amount: number;
  type: 'birthday' | 'bill_due' | 'trip' | 'other';
  status: 'green' | 'yellow' | 'red';
}

export interface CashFlowData {
  currentBalance: number;
  projectedBalance: number;
  dates: ImportantDate[];
}
```

---

## State Management (Zustand)

```typescript
// src/store/dashboardStore.ts
import create from 'zustand';
import { supabase } from '../lib/supabaseClient';

interface DashboardState {
  importantDates: ImportantDate[];
  currentBalance: number;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  fetchImportantDates: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  importantDates: [],
  currentBalance: 0,
  activeTab: 'base-case',
  setActiveTab: (tab) => set({ activeTab: tab }),
  fetchImportantDates: async () => {
    const { data, error } = await supabase
      .from('user_important_dates')
      .select('*');
    if (data) set({ importantDates: data });
  },
}));
```

---

## Main Dashboard Component

```typescript
// src/App.tsx
import { TabNavigation } from './components/common/TabNavigation';
import { BaseCaseTab } from './components/dashboard/BaseCaseTab';
import { CareerGrowthTab } from './components/dashboard/CareerGrowthTab';
import { EmergencyExpensesTab } from './components/dashboard/EmergencyExpensesTab';
import { HealthImpactTab } from './components/dashboard/HealthImpactTab';
import { useDashboardStore } from './store/dashboardStore';

function App() {
  const activeTab = useDashboardStore((state) => state.activeTab);

  return (
    <div className="min-h-screen bg-gray-100">
      <TabNavigation />
      <main className="container mx-auto px-4 py-8">
        {activeTab === 'base-case' && <BaseCaseTab />}
        {activeTab === 'career-growth' && <CareerGrowthTab />}
        {activeTab === 'emergency-expenses' && <EmergencyExpensesTab />}
        {activeTab === 'health-impact' && <HealthImpactTab />}
      </main>
    </div>
  );
}
```

---

## Calendar Component

```typescript
// src/components/calendar/ImportantDatesCalendar.tsx
import Calendar from 'react-calendar';
import { useDashboardStore } from '../../store/dashboardStore';

export function ImportantDatesCalendar() {
  const importantDates = useDashboardStore((state) => state.importantDates);

  return (
    <div className="calendar-container">
      <Calendar
        tileContent={({ date }) => {
          const dateEvents = importantDates.filter(
            (event) => new Date(event.date).toDateString() === date.toDateString()
          );
          return dateEvents.map((event) => (
            <div
              key={event.id}
              className={`status-dot ${event.status}`}
              title={`${event.title}: $${event.amount}`}
            />
          ));
        }}
      />
    </div>
  );
}
```

---

## Tab Components

```typescript
// src/components/dashboard/BaseCaseTab.tsx
import { ImportantDatesCalendar } from '../calendar/ImportantDatesCalendar';
import { CashFlowTimeline } from '../common/CashFlowTimeline';
import { useDashboardStore } from '../../store/dashboardStore';

export function BaseCaseTab() {
  const { importantDates, currentBalance } = useDashboardStore();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="calendar-section">
        <ImportantDatesCalendar />
      </div>
      <div className="timeline-section">
        <CashFlowTimeline
          dates={importantDates}
          balance={currentBalance}
        />
      </div>
    </div>
  );
}
```

---

## Styling

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

.status-dot {
  @apply w-2 h-2 rounded-full mx-auto mt-1;
}

.status-dot.green {
  @apply bg-green-500;
}

.status-dot.yellow {
  @apply bg-yellow-500;
}

.status-dot.red {
  @apply bg-red-500;
}
```

---

## Supabase Integration

```typescript
// src/lib/supabaseClient.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseKey = process.env.REACT_APP_SUPABASE_KEY;

export const supabase = createClient(supabaseUrl, supabaseKey);
```

---

## Testing

```typescript
// src/components/calendar/__tests__/ImportantDatesCalendar.test.tsx
import { render, screen } from '@testing-library/react';
import { ImportantDatesCalendar } from '../ImportantDatesCalendar';

describe('ImportantDatesCalendar', () => {
  it('renders calendar with events', () => {
    render(<ImportantDatesCalendar />);
    expect(screen.getByRole('application')).toBeInTheDocument();
  });
});
```

---

## Deployment

```bash
# Build the project
npm run build

# Deploy to your hosting service (e.g., Vercel, Netlify)
```

---

## Scenario Tabs Overview

### Base Case Tab
- Calendar view with color-coded status indicators (green/yellow/red)
- Cash flow timeline
- Status summary

### Career Growth Tab
- Side-by-side income comparison
- Impact metrics (monthly surplus, emergency fund, debt payoff)
- Real-time forecast updates

### Emergency Expenses Tab
- Pre-defined and custom emergency scenarios
- Impact visualization (cash flow, recovery timeline)
- Recommendations

### Health Impact Tab
- Health scenarios (short/long-term disability)
- Impact breakdown (medical bills, lost income, insurance)
- Recovery plan

---

## Notes
- All code is modular and can be extended for additional tabs or features.
- Use Zustand or Redux for state management as preferred.
- Integrate with Supabase for persistent data storage and retrieval.
- Tailwind CSS ensures a modern, responsive UI.
- Add more unit tests as you build out features.

---

**You can copy, update, and implement this plan as your project evolves!** 