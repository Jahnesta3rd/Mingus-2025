# Income Comparison Dashboard

## Overview

The Income Comparison Dashboard is an interactive, mobile-optimized interface designed to maximize lead conversion for African American professionals. It provides data-driven insights for salary benchmarking, career advancement planning, and cultural context awareness.

## Features

### 1. Real-time Salary Benchmarking Widget

**Location**: `src/components/dashboard/SalaryBenchmarkWidget.tsx`

**Features**:
- Shows user's salary vs peers in same MSA, industry, experience level
- Includes confidence intervals and sample sizes
- Interactive drill-down options for detailed comparisons
- Real-time filtering by location, industry, experience, and company size
- Visual salary range distribution with percentile markers

**Key Components**:
- Salary comparison visualization with percentile positioning
- Confidence interval display
- Sample size indicators
- Customizable filters for precise benchmarking
- Action buttons for detailed reports and sharing

### 2. Career Advancement Simulator

**Location**: `src/components/dashboard/CareerAdvancementSimulator.tsx`

**Features**:
- Interactive sliders for education, skills, location changes
- Real-time prediction updates as user adjusts parameters
- "Path to $100K" visualization for target demographic
- ROI calculations for career investments
- Step-by-step career development recommendations

**Key Components**:
- Progress bar showing current vs target salary
- Interactive parameter controls (education, experience, networking)
- Career step recommendations with costs and timelines
- Investment summary with ROI calculations
- Priority-based action planning

### 3. Cultural Context Integration

**Location**: `src/components/dashboard/CulturalContextIntegration.tsx`

**Features**:
- Highlights salary gaps and systemic barriers
- Shows "representation premium" for companies with diverse leadership
- Community wealth-building context and resources
- Tabbed interface for different aspects of equity insights

**Key Components**:
- Salary gap analysis with actionable insights
- Company recommendations based on diversity metrics
- Community resource directory
- Wealth-building strategies
- Professional organization listings

## Technical Implementation

### TypeScript Types

**Location**: `src/types/salary.ts`

Defines interfaces for:
- `SalaryData`: Salary benchmarking data structure
- `CareerPath`: Career advancement planning data
- `CulturalContext`: Cultural and equity insights
- `SalaryBenchmarkFilters`: Filtering options
- `CareerSimulatorParams`: Simulator parameters

### Main Dashboard Component

**Location**: `src/components/dashboard/IncomeComparisonDashboard.tsx`

**Features**:
- Responsive design with mobile-first approach
- Dynamic layout switching based on screen size
- Integrated component orchestration
- Call-to-action sections for lead conversion
- Trust indicators and privacy notices

### Integration

**Location**: `src/components/dashboard/IncomeComparisonTab.tsx`

Integrates the dashboard into the existing application structure.

## Usage

### Accessing the Dashboard

1. **Via Main App**: Navigate to the "Income Comparison" tab in the main dashboard
2. **Standalone Demo**: Access `/income-comparison-demo` for a standalone view

### Mobile Optimization

The dashboard automatically adapts to mobile screens with:
- Tabbed navigation for mobile devices
- Single-column layout on small screens
- Touch-friendly interactive elements
- Optimized spacing and typography

## Data Sources

Currently uses mock data that can be replaced with:
- Real salary data APIs (Glassdoor, Payscale, etc.)
- Company diversity metrics
- Professional organization databases
- User profile and preference data

## Customization

### Styling
- Uses Tailwind CSS for consistent styling
- Color-coded sections for different data types
- Responsive design patterns
- Accessibility considerations

### Content
- Configurable industry options
- Customizable location data
- Adjustable salary ranges
- Editable cultural context information

## Lead Conversion Features

### Engagement Elements
- Interactive sliders and controls
- Real-time data updates
- Personalized recommendations
- Social sharing capabilities

### Call-to-Action Buttons
- "Get Detailed Report" - Premium content access
- "Join Community" - Newsletter signup
- "Save Career Plan" - Account creation
- "Get Mentorship" - Service upsell

### Trust Indicators
- Professional organization partnerships
- Data privacy assurances
- Sample size transparency
- Research-backed insights

## Future Enhancements

### Planned Features
- Integration with real salary APIs
- Advanced filtering and comparison tools
- Personalized career coaching recommendations
- Community networking features
- Mobile app version

### Analytics Integration
- User engagement tracking
- Conversion funnel analysis
- A/B testing capabilities
- Performance metrics

## Development

### Prerequisites
- React 18+
- TypeScript
- Tailwind CSS
- Zustand for state management

### Installation
```bash
npm install
npm run dev
```

### Building
```bash
npm run build
```

## Contributing

1. Follow the existing code structure and patterns
2. Add TypeScript types for new features
3. Ensure mobile responsiveness
4. Include loading states and error handling
5. Add appropriate documentation

## Support

For questions or issues related to the Income Comparison Dashboard, please refer to the main project documentation or contact the development team. 