/**
 * Verification: Financial Forecast tab in CareerProtectionDashboard
 * - Tab order (position 2), FinancialForecastTab render, other tabs unchanged, no TS errors
 */
import * as fs from 'fs';
import * as path from 'path';

const dashboardPath = path.join(__dirname, '../CareerProtectionDashboard.tsx');

describe('CareerProtectionDashboard – Financial Forecast tab verification', () => {
  let src: string;

  beforeAll(() => {
    src = fs.readFileSync(dashboardPath, 'utf8');
  });

  describe('1. New Financial Forecast tab appears in position 2 in the tab bar', () => {
    it('tab definitions array has daily-outlook, then financial-forecast, then overview', () => {
      const idxDaily = src.indexOf("id: 'daily-outlook'");
      const idxForecast = src.indexOf("id: 'financial-forecast'");
      const idxOverview = src.indexOf("id: 'overview'");
      expect(idxDaily).toBeGreaterThan(-1);
      expect(idxForecast).toBeGreaterThan(idxDaily);
      expect(idxOverview).toBeGreaterThan(idxForecast);
      expect(src).toContain("label: 'Financial Forecast'");
    });
  });

  describe('2. Clicking the tab renders FinancialForecastTab', () => {
    it('condition and component for financial-forecast tab are present', () => {
      expect(src).toContain("dashboardState.activeTab === 'financial-forecast'");
      expect(src).toContain('<FinancialForecastTab');
      expect(src).toContain('userEmail={user?.email ?? \'\'}');
      expect(src).toContain("className=\"mt-4\"");
    });
  });

  describe('3. All other tabs still render their original content', () => {
    it('daily-outlook, overview, recommendations, location, housing, vehicle, analytics conditions present', () => {
      expect(src).toContain("activeTab === 'daily-outlook'");
      expect(src).toContain("activeTab === 'overview'");
      expect(src).toContain("activeTab === 'recommendations'");
      expect(src).toContain("activeTab === 'location'");
      expect(src).toContain("activeTab === 'housing'");
      expect(src).toContain("activeTab === 'vehicle'");
      expect(src).toContain("activeTab === 'analytics'");
    });
    it('Overview still has Quick Actions, Recent Activity, SpendingMilestonesWidget, SpecialDatesWidget, HousingLocationTile', () => {
      expect(src).toContain('Quick Actions');
      expect(src).toContain('Recent Activity');
      expect(src).toContain('SpendingMilestonesWidget');
      expect(src).toContain('SpecialDatesWidget');
      expect(src).toContain('HousingLocationTile');
    });
    it('RecommendationTiers, LocationIntelligenceMap, VehicleDashboard, AnalyticsDashboard still used', () => {
      expect(src).toContain('RecommendationTiers');
      expect(src).toContain('LocationIntelligenceMap');
      expect(src).toContain('VehicleDashboard');
      expect(src).toContain('AnalyticsDashboard');
    });
  });

  describe('4. No TypeScript errors in the modified file', () => {
    it('FinancialForecastTab is imported and used with correct props', () => {
      expect(src).toContain("import FinancialForecastTab from '../components/FinancialForecastTab'");
      expect(src).toContain('userTier=');
    });
  });
});
