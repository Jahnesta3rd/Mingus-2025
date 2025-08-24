# Recharts Analytics Dashboard Guide

## Overview

The Recharts Analytics Dashboard provides a beautiful, interactive data visualization interface for the Mingus article library analytics system. Built with React, TypeScript, Recharts, and Tailwind CSS, it offers comprehensive insights into user engagement, content performance, and cultural impact metrics.

## Features

### 🎨 Visual Design
- **Modern UI**: Clean, professional design with Tailwind CSS
- **Responsive Layout**: Mobile-friendly interface
- **Interactive Charts**: Hover effects, tooltips, and animations
- **Color-coded Metrics**: Intuitive color scheme for different data types

### 📊 Data Visualization
- **Bar Charts**: Phase performance and content comparison
- **Pie Charts**: User assessment distribution
- **Composed Charts**: Combined bar and line charts for complex metrics
- **Progress Indicators**: Visual representation of completion rates
- **Metric Cards**: Key performance indicators at a glance

### 🔄 Real-time Features
- **Auto-refresh**: Automatic data updates every 5 minutes
- **Manual Refresh**: One-click data refresh
- **Loading States**: Smooth loading animations
- **Error Handling**: Graceful error display and retry functionality

## Installation & Setup

### Prerequisites
- Node.js 16+ and npm/yarn
- React 18+
- TypeScript 5+
- Tailwind CSS 3+

### Dependencies Installation

```bash
# Install Recharts and related packages
npm install recharts lucide-react

# Install development dependencies
npm install -D @types/react typescript tailwindcss @tailwindcss/forms
```

### Tailwind CSS Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        purple: {
          50: '#faf5ff',
          600: '#7c3aed',
          700: '#6d28d9'
        }
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms')
  ]
}
```

## Component Structure

### Main Dashboard Component
```tsx
// frontend/components/RechartsAnalyticsDashboard/index.tsx
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, 
         XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Users, BookOpen, Target, Search, Award } from 'lucide-react';

const AnalyticsDashboard: React.FC = () => {
  // Component implementation
};
```

### Data Interfaces
```typescript
interface DashboardData {
  period_days: number;
  user_engagement: {
    active_users: number;
    avg_session_time_minutes: number;
    total_article_views: number;
    total_completions: number;
    avg_search_success_rate: number;
  };
  top_articles: Array<{
    title: string;
    phase: string;
    views: number;
    completion_rate: number;
    cultural_engagement: number;
  }>;
  phase_performance: Array<{
    phase: string;
    article_count: number;
    total_views: number;
    avg_completion_rate: number;
  }>;
}
```

## API Integration

### Authentication
```typescript
const loadAnalyticsData = async () => {
  const headers = {
    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
    'Content-Type': 'application/json'
  };
  
  const response = await fetch('/api/analytics/dashboard', {
    headers,
    credentials: 'include'
  });
};
```

### Data Fetching
```typescript
const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
const [userJourneyData, setUserJourneyData] = useState<UserJourneyData | null>(null);
const [culturalImpactData, setCulturalImpactData] = useState<CulturalImpactData | null>(null);

useEffect(() => {
  loadAnalyticsData();
}, [timeRange]);
```

## Chart Components

### 1. Be-Do-Have Phase Performance Chart
```tsx
<ResponsiveContainer width="100%" height={300}>
  <ComposedChart data={dashboardData?.phase_performance || []}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="phase" />
    <YAxis yAxisId="left" />
    <YAxis yAxisId="right" orientation="right" />
    <Tooltip 
      formatter={(value, name) => [
        name === 'total_views' ? formatNumber(value as number) : `${value}%`,
        name === 'total_views' ? 'Total Views' : 'Completion Rate'
      ]}
    />
    <Bar 
      yAxisId="left"
      dataKey="total_views" 
      fill="#7C3AED" 
      name="total_views"
      radius={[4, 4, 0, 0]}
    />
    <Line 
      yAxisId="right"
      type="monotone" 
      dataKey="avg_completion_rate" 
      stroke="#059669" 
      strokeWidth={3}
      name="avg_completion_rate"
      dot={{ fill: '#059669', strokeWidth: 2, r: 4 }}
    />
  </ComposedChart>
</ResponsiveContainer>
```

### 2. Cultural Content Performance Chart
```tsx
<ResponsiveContainer width="100%" height={300}>
  <BarChart data={culturalImpactData?.content_performance_comparison || []}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="content_type" />
    <YAxis />
    <Tooltip formatter={(value) => [`${value}%`, 'Rate']} />
    <Legend />
    <Bar 
      dataKey="avg_completion_rate" 
      fill="#7C3AED" 
      name="Completion Rate %"
      radius={[4, 4, 0, 0]}
    />
    <Bar 
      dataKey="avg_bookmark_rate" 
      fill="#D97706" 
      name="Bookmark Rate %"
      radius={[4, 4, 0, 0]}
    />
  </BarChart>
</ResponsiveContainer>
```

### 3. User Assessment Distribution Pie Chart
```tsx
<ResponsiveContainer width="100%" height={300}>
  <PieChart>
    <Pie
      data={userJourneyData?.assessment_distribution || []}
      dataKey="user_count"
      nameKey="level"
      cx="50%"
      cy="50%"
      outerRadius={100}
      label={({ level, user_count }) => `${level}: ${user_count}`}
    >
      {(userJourneyData?.assessment_distribution || []).map((entry, index) => (
        <Cell key={`cell-${index}`} fill={Object.values(COLORS)[index % Object.keys(COLORS).length]} />
      ))}
    </Pie>
    <Tooltip formatter={(value) => [value, 'Users']} />
  </PieChart>
</ResponsiveContainer>
```

## Utility Functions

### Number Formatting
```typescript
const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

const formatPercentage = (num: number) => {
  return `${num.toFixed(1)}%`;
};
```

### Color Scheme
```typescript
const COLORS = {
  BE: '#1E3A8A',    // Deep Blue
  DO: '#059669',    // Emerald Green  
  HAVE: '#D97706',  // Golden Yellow
  cultural: '#7C3AED', // Purple
  general: '#6B7280',   // Gray
  high: '#DC2626',  // Red for high cultural relevance
  standard: '#6B7280'   // Gray for standard content
};
```

## Metric Cards Component

```tsx
interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ComponentType<any>;
  color: 'blue' | 'green' | 'purple' | 'yellow';
  subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon: Icon, color, subtitle }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    yellow: 'bg-yellow-50 text-yellow-600'
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};
```

## Usage Examples

### Basic Implementation
```tsx
import AnalyticsDashboard from './components/RechartsAnalyticsDashboard';

function AdminPanel() {
  return (
    <div className="min-h-screen bg-gray-50">
      <AnalyticsDashboard />
    </div>
  );
}
```

### Custom Time Range
```tsx
const [timeRange, setTimeRange] = useState(30);

// The dashboard automatically fetches data when timeRange changes
<select
  value={timeRange}
  onChange={(e) => setTimeRange(parseInt(e.target.value))}
  className="border rounded-lg px-3 py-2 bg-white"
>
  <option value={7}>Last 7 days</option>
  <option value={30}>Last 30 days</option>
  <option value={90}>Last 90 days</option>
</select>
```

### Custom Styling
```tsx
// Custom color scheme
const customColors = {
  BE: '#1E40AF',
  DO: '#047857',
  HAVE: '#B45309',
  cultural: '#6D28D9'
};

// Custom chart styling
<BarChart 
  data={data} 
  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
>
  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
  <XAxis dataKey="phase" stroke="#6B7280" />
  <YAxis stroke="#6B7280" />
  <Tooltip 
    contentStyle={{ 
      backgroundColor: '#FFFFFF', 
      border: '1px solid #E5E7EB',
      borderRadius: '8px'
    }}
  />
</BarChart>
```

## Performance Optimization

### Lazy Loading
```tsx
import React, { lazy, Suspense } from 'react';

const AnalyticsDashboard = lazy(() => import('./components/RechartsAnalyticsDashboard'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AnalyticsDashboard />
    </Suspense>
  );
}
```

### Memoization
```tsx
import React, { useMemo } from 'react';

const AnalyticsDashboard: React.FC = () => {
  const formattedData = useMemo(() => {
    return dashboardData?.phase_performance?.map(item => ({
      ...item,
      formattedViews: formatNumber(item.total_views)
    }));
  }, [dashboardData]);

  return (
    // Use formattedData in charts
  );
};
```

## Error Handling

### Loading States
```tsx
if (loading && !dashboardData) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
    </div>
  );
}
```

### Error Display
```tsx
if (error) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-800">Error loading analytics</h3>
          <p className="text-sm text-red-700 mt-1">{error}</p>
          <button 
            onClick={loadAnalyticsData}
            className="mt-2 text-sm text-red-800 hover:text-red-900 underline"
          >
            Try again
          </button>
        </div>
      </div>
    </div>
  );
}
```

## Customization

### Custom Chart Themes
```tsx
const chartTheme = {
  colors: ['#7C3AED', '#059669', '#D97706', '#DC2626'],
  backgroundColor: '#FFFFFF',
  textColor: '#374151',
  fontSize: 12,
  fontFamily: 'Inter, system-ui, sans-serif'
};
```

### Responsive Design
```tsx
// Custom breakpoints for different screen sizes
const getChartHeight = () => {
  if (window.innerWidth < 768) return 250; // Mobile
  if (window.innerWidth < 1024) return 300; // Tablet
  return 350; // Desktop
};
```

## Testing

### Unit Tests
```tsx
import { render, screen } from '@testing-library/react';
import AnalyticsDashboard from './AnalyticsDashboard';

test('renders analytics dashboard', () => {
  render(<AnalyticsDashboard />);
  expect(screen.getByText('Article Library Analytics')).toBeInTheDocument();
});

test('displays loading state', () => {
  render(<AnalyticsDashboard />);
  expect(screen.getByRole('status')).toBeInTheDocument();
});
```

### Integration Tests
```tsx
import { render, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/analytics/dashboard', (req, res, ctx) => {
    return res(ctx.json(mockDashboardData));
  })
);

test('loads and displays analytics data', async () => {
  render(<AnalyticsDashboard />);
  
  await waitFor(() => {
    expect(screen.getByText('Active Users')).toBeInTheDocument();
  });
});
```

## Deployment

### Build Configuration
```json
{
  "scripts": {
    "build": "tsc && tailwindcss -i ./src/input.css -o ./dist/output.css --minify",
    "dev": "tsc --watch & tailwindcss -i ./src/input.css -o ./dist/output.css --watch"
  }
}
```

### Environment Variables
```bash
# .env.local
REACT_APP_API_BASE_URL=http://localhost:5000
REACT_APP_ANALYTICS_ENABLED=true
REACT_APP_AUTO_REFRESH_INTERVAL=300000
```

## Troubleshooting

### Common Issues

1. **Charts not rendering**
   - Check if data is properly formatted
   - Verify ResponsiveContainer has proper dimensions
   - Ensure all required props are passed

2. **Performance issues**
   - Implement data memoization
   - Use React.memo for chart components
   - Optimize re-renders with useCallback

3. **Styling conflicts**
   - Check Tailwind CSS configuration
   - Ensure proper CSS specificity
   - Verify class name conflicts

### Debug Mode
```typescript
const DEBUG = process.env.NODE_ENV === 'development';

if (DEBUG) {
  console.log('Dashboard data:', dashboardData);
  console.log('User journey data:', userJourneyData);
  console.log('Cultural impact data:', culturalImpactData);
}
```

---

This Recharts Analytics Dashboard provides a powerful, interactive visualization interface for the Mingus article library analytics system, enabling data-driven insights for African American professional content optimization.
