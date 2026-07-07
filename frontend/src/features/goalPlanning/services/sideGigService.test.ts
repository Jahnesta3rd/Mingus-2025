import {
  buildSideGigPrompt,
  estimateEarningsTrajectory,
  getFirstClientTips,
  getKnowledgeBaseSideGigs,
  parseSideGigSuggestions,
  suggestSideGigs,
} from './sideGigService';

const engineerProfile = {
  jobTitle: 'Software Engineer',
  industry: 'Technology',
  income: 8000,
  skills: ['JavaScript', 'React', 'Node.js'],
  availableHours: 5,
};

const marketerProfile = {
  jobTitle: 'Marketing Coordinator',
  industry: 'Marketing',
  income: 4500,
  skills: ['SEO', 'Copywriting', 'Social media'],
  availableHours: 10,
};

const designerProfile = {
  jobTitle: 'UI Designer',
  industry: 'Design',
  income: 5500,
  skills: ['Figma', 'UI design', 'Prototyping'],
  availableHours: 15,
};

const mockLlmGigs = [
  {
    type: 'freelance',
    title: 'React Freelance Development',
    platforms: [{ name: 'Upwork', monthlyEarnings: 1200 }],
    hoursPerWeek: 5,
    startupTime: '1-2 weeks',
    steps: ['Create Upwork profile', 'Add portfolio', 'Send proposals'],
    pros: ['Flexible hours'],
    cons: ['Client acquisition'],
  },
];

describe('buildSideGigPrompt', () => {
  it('includes skills, hours, and income target', () => {
    const prompt = buildSideGigPrompt(engineerProfile, 1000, 5);
    expect(prompt).toContain('JavaScript, React, Node.js');
    expect(prompt).toContain('Available hours/week: 5');
    expect(prompt).toContain('Target monthly income: $1000');
    expect(prompt).toContain('Software Engineer');
  });
});

describe('parseSideGigSuggestions', () => {
  it('parses JSON arrays from raw and fenced responses', () => {
    expect(parseSideGigSuggestions(JSON.stringify(mockLlmGigs))).toHaveLength(1);
    const fenced = `\`\`\`json\n${JSON.stringify(mockLlmGigs)}\n\`\`\``;
    expect(parseSideGigSuggestions(fenced)?.[0]?.title).toBe('React Freelance Development');
  });

  it('returns null for invalid responses', () => {
    expect(parseSideGigSuggestions('not json')).toBeNull();
  });
});

describe('estimateEarningsTrajectory', () => {
  it('ramps earnings over six months with learning curve', () => {
    const projection = estimateEarningsTrajectory({
      hourlyRate: 50,
      hoursPerWeek: 10,
      months: 6,
    });

    expect(projection).toHaveLength(6);
    expect(projection[0]?.earnings).toBeLessThan(projection[5]?.earnings ?? 0);
    expect(projection[0]?.effort).toBe('High setup');
    expect(projection[5]?.effort).toBe('Optimized');
  });

  it('subtracts initial investment from month one', () => {
    const projection = estimateEarningsTrajectory({
      hourlyRate: 40,
      hoursPerWeek: 5,
      months: 3,
      initialInvestment: 200,
    });
    expect(projection[0]?.earnings).toBeLessThan(projection[1]?.earnings ?? 0);
  });
});

describe('getFirstClientTips', () => {
  it('returns type-specific tips and platform guidance', () => {
    const tips = getFirstClientTips('freelance', 'Upwork');
    expect(tips.length).toBeGreaterThanOrEqual(3);
    expect(tips.some((tip) => tip.includes('Upwork'))).toBe(true);
  });
});

describe('getKnowledgeBaseSideGigs', () => {
  it('suggests developer gigs for engineer with 5 hrs/week', () => {
    const gigs = getKnowledgeBaseSideGigs(engineerProfile, 1000, 5);
    expect(gigs.length).toBeGreaterThanOrEqual(3);
    expect(gigs[0]?.hoursPerWeek).toBeLessThanOrEqual(5);
    expect(gigs.some((gig) => gig.type === 'freelance')).toBe(true);
    expect(gigs[0]?.monthlyProjection).toHaveLength(6);
    expect(gigs[0]?.platforms[0]?.url).toContain('http');
    expect(gigs[0]?.firstClientTips.length).toBeGreaterThan(0);
  });

  it('suggests marketing gigs for marketer with 10 hrs/week', () => {
    const gigs = getKnowledgeBaseSideGigs(marketerProfile, 1500, 10);
    const titles = gigs.map((gig) => gig.title.toLowerCase());
    expect(titles.some((title) => title.includes('social') || title.includes('copy'))).toBe(true);
    expect(gigs[0]?.estimatedMonthly.max).toBeGreaterThan(0);
  });

  it('suggests design gigs for designer with 15 hrs/week', () => {
    const gigs = getKnowledgeBaseSideGigs(designerProfile, 2000, 15);
    expect(gigs.some((gig) => gig.title.toLowerCase().includes('design'))).toBe(true);
    expect(gigs[0]?.hoursPerWeek).toBeLessThanOrEqual(15);
    expect(gigs[0]?.scalability).toBeTruthy();
  });

  it('adapts to different target income levels', () => {
    const lowTarget = getKnowledgeBaseSideGigs(engineerProfile, 400, 5);
    const highTarget = getKnowledgeBaseSideGigs(engineerProfile, 2500, 5);
    expect(lowTarget[0]?.estimatedMonthly.max).toBeLessThan(highTarget[0]?.estimatedMonthly.max);
  });

  it('returns empty array when no hours are available', () => {
    expect(getKnowledgeBaseSideGigs(engineerProfile, 1000, 0)).toEqual([]);
  });
});

describe('suggestSideGigs', () => {
  it('uses mocked LLM responses when available', async () => {
    const mockLlmClient = jest.fn().mockResolvedValue(JSON.stringify(mockLlmGigs));
    const result = await suggestSideGigs(engineerProfile, 1000, 5, { llmClient: mockLlmClient });

    expect(mockLlmClient).toHaveBeenCalled();
    expect(result.source).toBe('llm');
    expect(result.gigs[0]?.title).toBe('React Freelance Development');
    expect(result.gigs[0]?.signupSteps.length).toBeGreaterThan(0);
  });

  it('falls back to knowledge base when LLM is unavailable', async () => {
    const result = await suggestSideGigs(marketerProfile, 1200, 10, { llmClient: async () => null });
    expect(result.source).toBe('knowledge_base');
    expect(result.gigs.length).toBeGreaterThanOrEqual(3);
  });

  it('falls back when LLM returns invalid JSON', async () => {
    const result = await suggestSideGigs(designerProfile, 1800, 15, {
      llmClient: async () => 'Cannot parse this.',
    });
    expect(result.source).toBe('knowledge_base');
    expect(result.gigs[0]?.monthlyProjection).toHaveLength(6);
  });

  it('returns empty gigs for invalid profile', async () => {
    const result = await suggestSideGigs(null, 1000, 5);
    expect(result.gigs).toEqual([]);
  });
});
