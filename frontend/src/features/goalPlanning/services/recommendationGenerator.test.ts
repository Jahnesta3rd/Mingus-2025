import { analyzeGoal } from './goalAnalyzer';
import {
  buildRecommendationPrompt,
  enhanceWithDetails,
  fallbackRecommendations,
  generateRecommendations,
  parseRecommendationResponse,
  validateRecommendationPayload,
} from './recommendationGenerator';

const baseProfile = {
  id: 'user-1',
  income: 8000,
  savings: 25000,
  expenses: 5200,
  jobTitle: 'Software Engineer',
  industry: 'Technology',
  skills: ['JavaScript', 'React', 'Node.js'],
  availableHours: 12,
};

const homeGoal = {
  type: 'home_purchase',
  parameters: { homePrice: 400000 },
  timeline: 5,
};

function buildGapAnalysis(goal = homeGoal, profile = baseProfile) {
  return analyzeGoal(profile, goal);
}

const mockLlmPaths = {
  paths: [
    {
      pathId: 'career_advancement',
      title: 'Career Advancement',
      description: 'Move into senior engineering roles in Technology',
      monthlyBoost: 1800,
      timeline: '3-6 months',
      feasibility: 'Medium',
      pros: ['Higher long-term earnings', 'Career momentum'],
      cons: ['Interview process takes time'],
      details: 'Target senior roles with 20% raise',
      topCompanies: ['Google', 'Stripe'],
      requiredSkills: ['System design', 'Leadership'],
      typical5YearEarnings: 650000,
    },
    {
      pathId: 'side_income',
      title: 'Side Income Opportunities',
      description: 'Freelance React development',
      monthlyBoost: 1200,
      hoursPerWeek: 12,
      timeline: 'Immediate',
      feasibility: 'High',
      pros: ['Fast to start'],
      cons: ['Extra hours'],
      platforms: ['Toptal', 'Upwork'],
      realisticMonthlyRange: { min: 800, max: 2000 },
      startupEffort: 'Low',
    },
    {
      pathId: 'combined',
      title: 'RECOMMENDED - Combined Strategy',
      description: 'Career move plus freelance income',
      monthlyBoost: 2500,
      timeline: '6 months + remaining',
      components: [
        { type: 'career', boost: 1500, timeline: '3-6 months' },
        { type: 'side_gigs', boost: 1000, timeline: 'Immediate' },
      ],
      totalTimeline: '6 months + remaining',
      feasibility: 'High',
      pros: ['Balanced approach'],
      cons: ['Requires discipline'],
      whyRecommended: 'Best fit for skills and available hours',
    },
    {
      pathId: 'alternative',
      title: 'Faster Alternative',
      description: 'Extend timeline to reduce monthly pressure',
      monthlyBoost: 0,
      timeline: 'Immediate',
      feasibility: 'Medium',
      pros: ['Lower monthly savings pressure'],
      cons: ['Delays goal achievement'],
      requires: 'Patience and delayed goal',
      details: 'Consider if income growth is uncertain',
    },
  ],
};

describe('buildRecommendationPrompt', () => {
  it('includes goal, profile, and gap analysis details', () => {
    const gapAnalysis = buildGapAnalysis();
    const prompt = buildRecommendationPrompt(gapAnalysis, baseProfile, homeGoal);

    expect(prompt).toContain('GOAL:');
    expect(prompt).toContain('home_purchase');
    expect(prompt).toContain('Software Engineer');
    expect(prompt).toContain('JavaScript, React, Node.js');
    expect(prompt).toContain('Gap to close:');
    expect(prompt).toContain('Return ONLY valid JSON');
    expect(prompt).toContain('$96,000/year');
  });

  it('works for different goal types', () => {
    const carGoal = {
      type: 'car_purchase',
      parameters: { carPrice: 30000 },
      timeline: 2,
    };
    const gapAnalysis = buildGapAnalysis(carGoal);
    const prompt = buildRecommendationPrompt(gapAnalysis, baseProfile, carGoal);

    expect(prompt).toContain('car_purchase');
    expect(prompt).toContain('Timeline: 2 years');
  });
});

describe('parseRecommendationResponse', () => {
  it('parses raw JSON responses', () => {
    const parsed = parseRecommendationResponse(JSON.stringify(mockLlmPaths));
    expect(parsed?.paths).toHaveLength(4);
  });

  it('parses markdown-fenced JSON', () => {
    const fenced = `\`\`\`json\n${JSON.stringify(mockLlmPaths)}\n\`\`\``;
    const parsed = parseRecommendationResponse(fenced);
    expect(validateRecommendationPayload(parsed)).toBe(true);
  });

  it('returns null for invalid responses', () => {
    expect(parseRecommendationResponse('not json')).toBeNull();
    expect(parseRecommendationResponse('{"paths": "bad"}')).toBeNull();
  });
});

describe('validateRecommendationPayload', () => {
  it('requires all four path types with valid fields', () => {
    expect(validateRecommendationPayload(mockLlmPaths)).toBe(true);
    expect(validateRecommendationPayload({ paths: mockLlmPaths.paths.slice(0, 2) })).toBe(false);
  });
});

describe('fallbackRecommendations', () => {
  it('returns four rule-based paths when LLM is unavailable', () => {
    const gapAnalysis = buildGapAnalysis();
    const result = fallbackRecommendations(baseProfile, homeGoal, gapAnalysis);

    expect(result.source).toBe('fallback');
    expect(result.paths).toHaveLength(4);
    expect(result.paths.map((path) => path.pathId)).toEqual(
      expect.arrayContaining(['career_advancement', 'side_income', 'combined', 'alternative']),
    );
  });

  it('works across goal types', () => {
    const goals = [
      { type: 'car_purchase', parameters: { carPrice: 28000 }, timeline: 2 },
      { type: 'apartment_move', parameters: { monthlyRent: 2000, movingCosts: 1000 }, timeline: 1 },
      { type: 'baby', parameters: { preparationCost: 10000 }, timeline: 1.5 },
      { type: 'business', parameters: { initialInvestment: 50000, monthlyCost: 3000 }, timeline: 3 },
    ];

    goals.forEach((goal) => {
      const gapAnalysis = buildGapAnalysis(goal);
      const result = fallbackRecommendations(baseProfile, goal, gapAnalysis);
      expect(result.paths.length).toBe(4);
    });
  });
});

describe('enhanceWithDetails', () => {
  it('adds projections and action suggestions to paths', () => {
    const gapAnalysis = buildGapAnalysis();
    const enhanced = enhanceWithDetails(mockLlmPaths.paths, baseProfile, homeGoal, gapAnalysis);

    expect(enhanced).toHaveLength(4);
    expect(enhanced[0]?.projections).toHaveLength(5);
    expect(enhanced[0]?.jobSuggestions?.length).toBeGreaterThan(0);
    expect(enhanced[1]?.gigSuggestions?.length).toBeGreaterThan(0);
    expect(enhanced[2]?.expenseCutSuggestions?.length).toBeGreaterThan(0);
    expect(enhanced[2]?.mostRealistic).toBe(true);
  });
});

describe('generateRecommendations', () => {
  it('uses mocked LLM response for home purchase goals', async () => {
    const gapAnalysis = buildGapAnalysis();
    const mockLlmClient = jest.fn().mockResolvedValue(JSON.stringify(mockLlmPaths));

    const result = await generateRecommendations(
      gapAnalysis,
      baseProfile,
      homeGoal,
      { llmClient: mockLlmClient },
    );

    expect(mockLlmClient).toHaveBeenCalled();
    expect(result?.source).toBe('llm');
    expect(result?.paths).toHaveLength(4);
    expect(result?.paths[0]?.jobSuggestions?.length).toBeGreaterThan(0);
    expect(result?.paths[1]?.gigSuggestions?.length).toBeGreaterThan(0);
    expect(result?.prompt).toContain('home_purchase');
  });

  it('falls back when LLM is unavailable', async () => {
    const gapAnalysis = buildGapAnalysis();
    const result = await generateRecommendations(
      gapAnalysis,
      baseProfile,
      homeGoal,
      { llmClient: async () => null },
    );

    expect(result?.source).toBe('fallback');
    expect(result?.paths).toHaveLength(4);
    expect(result?.paths.every((path) => path.projections?.length > 0)).toBe(true);
  });

  it('falls back when LLM returns invalid JSON', async () => {
    const gapAnalysis = buildGapAnalysis();
    const result = await generateRecommendations(
      gapAnalysis,
      baseProfile,
      homeGoal,
      { llmClient: async () => 'Sorry, I cannot help with that.' },
    );

    expect(result?.source).toBe('fallback');
    expect(result?.paths.map((path) => path.pathId)).toContain('combined');
  });

  it.each([
    ['car_purchase', { type: 'car_purchase', parameters: { carPrice: 30000 }, timeline: 2 }],
    ['apartment_move', { type: 'apartment_move', parameters: { monthlyRent: 2200 }, timeline: 1 }],
    ['baby', { type: 'baby', parameters: { preparationCost: 12000 }, timeline: 2 }],
    ['business', { type: 'business', parameters: { initialInvestment: 60000, monthlyCost: 4000 }, timeline: 2 }],
  ])('generates recommendations for %s goals with mocked LLM', async (_label, goal) => {
    const gapAnalysis = buildGapAnalysis(goal);
    const result = await generateRecommendations(
      gapAnalysis,
      baseProfile,
      goal,
      { llmClient: async () => JSON.stringify(mockLlmPaths) },
    );

    expect(result?.paths).toHaveLength(4);
    expect(result?.generatedAt).toBeTruthy();
  });

  it('returns null for missing inputs', async () => {
    expect(await generateRecommendations(null, baseProfile, homeGoal)).toBeNull();
  });
});
