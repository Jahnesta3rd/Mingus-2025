import {
  expenseCutPrompt,
  fallbackExpenseCutPrompt,
  fallbackJobSuggestionPrompt,
  fallbackRecommendationPrompt,
  fallbackSideGigPrompt,
  getGoalTimelineYears,
  jobSuggestionPrompt,
  multiGoalPrompt,
  parseLlmJsonResponse,
  recommendationPrompt,
  sideGigPrompt,
  validateExpenseCutSuggestions,
  validateJobSuggestions,
  validateMultiGoalResponse,
  validateRecommendationPath,
  validateRecommendationPaths,
  validateSideGigSuggestions,
} from './llmPrompts.js';

const engineerProfile = {
  jobTitle: 'Software Engineer',
  industry: 'Technology',
  income: 8000,
  expenses: 5200,
  savings: 25000,
  availableHours: 10,
  skills: ['JavaScript', 'React', 'System design'],
};

const marketerProfile = {
  jobTitle: 'Marketing Coordinator',
  industry: 'Consumer goods',
  income: 4500,
  expenses: 3800,
  savings: 8000,
  availableHours: 8,
  skills: ['SEO', 'Content strategy', 'Analytics'],
};

const parentProfile = {
  jobTitle: 'Operations Manager',
  industry: 'Healthcare',
  income: 6200,
  expenses: 6100,
  savings: 12000,
  availableHours: 5,
  skills: ['Project management', 'Budgeting'],
};

const homeGoalAnalysis = {
  goalDescription: 'Buy a home in Austin',
  presentState: { income: 8000, monthlyExpenses: 5200, savings: 25000 },
  futureState: { savingsTarget: 97000, timelineYears: 5 },
  gaps: {
    totalNeeded: 97000,
    savingsGap: 72000,
    monthlyToSave: 1200,
    incomeGap: 24000,
    expenseIncrease: 400,
    incomeNeeded: 120000,
    feasible: false,
  },
};

const babyGoalAnalysis = {
  goalDescription: 'Prepare for a new baby',
  presentState: { income: 6200, monthlyExpenses: 6100, savings: 12000 },
  futureState: { savingsTarget: 25000, timelineYears: 2 },
  gaps: {
    savingsGap: 13000,
    monthlyToSave: 542,
    incomeGap: 8000,
    expenseIncrease: 650,
    incomeNeeded: 90000,
  },
};

describe('llmPrompts', () => {
  describe('recommendationPrompt', () => {
    it('includes engineer home-buying context and JSON structure', () => {
      const prompt = recommendationPrompt(
        homeGoalAnalysis,
        engineerProfile,
        { type: 'home_purchase', timeline: 5, description: 'Buy a home in Austin' },
      );

      expect(prompt).toContain('Software Engineer');
      expect(prompt).toContain('$96,000/year');
      expect(prompt).toContain('career_advancement');
      expect(prompt).toContain('Return ONLY valid JSON');
      expect(prompt).toContain('$97,000');
    });

    it('handles missing profile fields gracefully', () => {
      const prompt = recommendationPrompt(
        { gaps: { monthlyToSave: 500, savingsGap: 10000 } },
        {},
        { type: 'car_purchase', timeline: 3 },
      );

      expect(prompt).toContain('Not specified');
      expect(prompt).toContain('None listed');
      expect(getGoalTimelineYears({ timeline: 3 })).toBe(3);
    });
  });

  describe('jobSuggestionPrompt', () => {
    it('describes marketer career change scenario', () => {
      const prompt = jobSuggestionPrompt(marketerProfile, 18000, 4);
      expect(prompt).toContain('Marketing Coordinator');
      expect(prompt).toContain('$54,000/year');
      expect(prompt).toContain('$18,000/year');
      expect(prompt).toContain('Return JSON array only');
    });

    it('fallback prompt stays minimal', () => {
      expect(fallbackJobSuggestionPrompt(engineerProfile, 30000)).toContain('3 higher-paying job titles');
    });
  });

  describe('sideGigPrompt', () => {
    it('includes target and hours for parent profile', () => {
      const prompt = sideGigPrompt(parentProfile, 800, 5);
      expect(prompt).toContain('Operations Manager');
      expect(prompt).toContain('$800/month');
      expect(prompt).toContain('5 hours/week');
    });

    it('fallback side gig prompt includes target', () => {
      expect(fallbackSideGigPrompt(600)).toContain('$600/month');
    });
  });

  describe('expenseCutPrompt', () => {
    it('includes expense baseline and reduction target', () => {
      const prompt = expenseCutPrompt(parentProfile, 350);
      expect(prompt).toContain('$6,100/month expenses');
      expect(prompt).toContain('$350/month');
      expect(prompt).toContain('lifestyle_impact');
    });

    it('fallback expense prompt requests essential fields', () => {
      expect(fallbackExpenseCutPrompt(200)).toContain('potentialSavings');
    });
  });

  describe('multiGoalPrompt', () => {
    it('lists multiple goals for prioritization', () => {
      const prompt = multiGoalPrompt(engineerProfile, [
        { id: 'home', description: 'Buy a home', timeline: 5 },
        { id: 'baby', description: 'Baby fund', parameters: { timeline: 2 } },
      ]);

      expect(prompt).toContain('2 financial goals');
      expect(prompt).toContain('[id: home]');
      expect(prompt).toContain('[id: baby]');
      expect(prompt).toContain('"priority"');
    });
  });

  describe('parseLlmJsonResponse', () => {
    it('parses fenced JSON objects', () => {
      const parsed = parseLlmJsonResponse('```json\n{"paths":[{"pathId":"combined"}]}\n```');
      expect(parsed).toEqual({ paths: [{ pathId: 'combined' }] });
    });

    it('parses raw JSON arrays', () => {
      const parsed = parseLlmJsonResponse('[{"title":"Senior Engineer","expectedSalary":140000,"incomeIncrease":20000,"timeline":"3-6 months"}]');
      expect(Array.isArray(parsed)).toBe(true);
    });
  });

  describe('validation', () => {
    const validPath = {
      pathId: 'career_advancement',
      title: 'Career Advancement',
      description: 'Move to senior role',
      monthlyBoost: 1500,
      timeline: '3-6 months',
      feasibility: 'Medium',
      pros: ['Higher pay'],
      cons: ['Interview prep'],
    };

    it('validates recommendation paths and required ids', () => {
      expect(validateRecommendationPath(validPath)).toBe(true);
      expect(validateRecommendationPaths({
        paths: [
          validPath,
          { ...validPath, pathId: 'side_income', title: 'Side Income' },
          { ...validPath, pathId: 'combined', title: 'Combined', feasibility: 'High' },
          { ...validPath, pathId: 'alternative', title: 'Alternative', feasibility: 'Low' },
        ],
      })).toBe(true);
    });

    it('rejects invalid salary and feasibility values', () => {
      expect(validateRecommendationPath({
        ...validPath,
        monthlyBoost: 999999,
      })).toBe(false);

      expect(validateJobSuggestions([
        { title: 'Engineer', expectedSalary: 50, incomeIncrease: 1000, timeline: 'soon' },
      ])).toBe(false);
    });

    it('validates job, gig, expense, and multi-goal payloads', () => {
      expect(validateJobSuggestions([
        {
          title: 'Senior Engineer',
          expectedSalary: 140000,
          incomeIncrease: 20000,
          timeline: '3-6 months',
        },
      ])).toBe(true);

      expect(validateSideGigSuggestions([
        {
          type: 'Freelance',
          platform: 'Upwork',
          estimatedMonthly: 1200,
          hoursPerWeek: 8,
          difficulty: 'Medium',
        },
      ])).toBe(true);

      expect(validateExpenseCutSuggestions([
        {
          category: 'Dining',
          suggestion: 'Cook twice more per week',
          potentialSavings: 120,
          lifestyle_impact: 'Minor',
        },
      ])).toBe(true);

      expect(validateMultiGoalResponse({
        priority: ['home', 'baby'],
        rationale: 'Secure housing before baby expenses rise.',
        conflicts: ['Competing savings targets'],
        strategy: 'Fund home down payment first, then baby fund.',
      })).toBe(true);
    });
  });

  describe('scenario prompts', () => {
    it('covers baby goal for parent profile', () => {
      const prompt = recommendationPrompt(
        babyGoalAnalysis,
        parentProfile,
        { type: 'baby', timeline: 2, description: 'Prepare for a new baby' },
      );

      expect(prompt).toContain('baby');
      expect(prompt).toContain('Operations Manager');
      expect(fallbackRecommendationPrompt(babyGoalAnalysis, parentProfile, { type: 'baby', timeline: 2 }))
        .toContain('career_advancement');
    });

    it('supports different income levels in marketer prompt', () => {
      const lowIncomePrompt = jobSuggestionPrompt(
        { ...marketerProfile, income: 3000 },
        12000,
        3,
      );
      expect(lowIncomePrompt).toContain('$36,000/year');
    });
  });
});
