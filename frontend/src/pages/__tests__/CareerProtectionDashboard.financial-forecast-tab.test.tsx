/**
 * Verification: CareerProtectionDashboard tab bar, URL tab sync, and key widgets.
 * (Forecast lives at /dashboard/forecast; ?tab=financial-forecast redirects there.)
 */
import * as fs from 'fs';
import * as path from 'path';

const dashboardPath = path.join(__dirname, '../CareerProtectionDashboard.tsx');

describe('CareerProtectionDashboard – tab bar and URL sync verification', () => {
  let src: string;

  beforeAll(() => {
    src = fs.readFileSync(dashboardPath, 'utf8');
  });

  describe('1. Tab definitions order', () => {
    it('has daily-outlook, then life-ledger, then overview in the tools nav array', () => {
      const idxDaily = src.indexOf("id: 'daily-outlook'");
      const idxLedger = src.indexOf("id: 'life-ledger'");
      const idxOverview = src.indexOf("id: 'overview'");
      expect(idxDaily).toBeGreaterThan(-1);
      expect(idxLedger).toBeGreaterThan(idxDaily);
      expect(idxOverview).toBeGreaterThan(idxLedger);
    });
  });

  describe('2. Financial forecast deep link', () => {
    it('redirects ?tab=financial-forecast to /dashboard/forecast', () => {
      expect(src).toContain("tab === 'financial-forecast'");
      expect(src).toContain("navigate('/dashboard/forecast'");
    });
  });

  describe('3. Tab panels and overview widgets', () => {
    it('daily-outlook, overview, recommendations, location, housing, vehicle, analytics conditions present', () => {
      expect(src).toContain("activeTab === 'daily-outlook'");
      expect(src).toContain("activeTab === 'overview'");
      expect(src).toContain("activeTab === 'recommendations'");
      expect(src).toContain("activeTab === 'location'");
      expect(src).toContain("activeTab === 'housing'");
      expect(src).toContain("activeTab === 'vehicle'");
      expect(src).toContain("activeTab === 'analytics'");
    });
    it('Overview includes Recent Activity, SpendingMilestonesWidget, SpecialDatesWidget, HousingLocationTile', () => {
      expect(src).toContain('Recent Activity');
      expect(src).toContain('SpendingMilestonesWidget');
      expect(src).toContain('SpecialDatesWidget');
      expect(src).toContain('HousingLocationTile');
    });
    it('searchParams tab=daily-outlook is handled in tab sync useEffect', () => {
      expect(src).toContain("tab === 'daily-outlook'");
      expect(src).toContain("setActiveTab('daily-outlook')");
    });
    it('RecommendationTiers, LocationIntelligenceMap, VehicleDashboard, AnalyticsDashboard still used', () => {
      expect(src).toContain('RecommendationTiers');
      expect(src).toContain('LocationIntelligenceMap');
      expect(src).toContain('VehicleDashboard');
      expect(src).toContain('AnalyticsDashboard');
    });
  });

  describe('4. Forecast entry from Tools', () => {
    it('nav sidebar links to Forecast route', () => {
      expect(src).toContain('to="/dashboard/forecast"');
    });
  });
});
