import {
  buildJobSuggestionPrompt,
  enrichWithCompanyData,
  enrichWithSalaryData,
  getKnowledgeBaseSuggestions,
  parseJobSuggestions,
  suggestJobsForIncomeGoal,
} from './jobRecommendationService';

const engineerProfile = {
  jobTitle: 'Software Engineer',
  industry: 'Technology',
  income: 8000,
  location: 'Austin, TX',
  yearsOfExperience: 4,
  skills: ['JavaScript', 'React', 'Node.js'],
};

const accountantProfile = {
  jobTitle: 'Staff Accountant',
  industry: 'Finance',
  income: 5200,
  location: 'Chicago, IL',
  yearsOfExperience: 3,
};

const marketerProfile = {
  jobTitle: 'Marketing Coordinator',
  industry: 'Marketing',
  income: 4500,
  location: 'Denver, CO',
  yearsOfExperience: 2,
};

const mockLlmJobs = [
  {
    title: 'Senior Software Engineer',
    companies: [
      { name: 'Stripe', avgSalary: 185000 },
      { name: 'Datadog', avgSalary: 175000 },
    ],
    expectedSalary: 180000,
    requiredSkills: ['System design', 'React'],
    interviewTopics: ['System design', 'Algorithms'],
    why: 'Closes the income gap with a realistic senior engineering step',
  },
];

describe('buildJobSuggestionPrompt', () => {
  it('includes role, income gap, and goal context', () => {
    const prompt = buildJobSuggestionPrompt(engineerProfile, 24000, 'home_purchase', 5);
    expect(prompt).toContain('Software Engineer');
    expect(prompt).toContain('Target additional income: $24000');
    expect(prompt).toContain('Total target: $120000');
    expect(prompt).toContain('home_purchase');
    expect(prompt).toContain('Austin, TX');
  });
});

describe('parseJobSuggestions', () => {
  it('parses JSON arrays from raw and fenced responses', () => {
    expect(parseJobSuggestions(JSON.stringify(mockLlmJobs))).toHaveLength(1);
    const fenced = `\`\`\`json\n${JSON.stringify(mockLlmJobs)}\n\`\`\``;
    expect(parseJobSuggestions(fenced)?.[0]?.title).toBe('Senior Software Engineer');
  });

  it('returns null for invalid responses', () => {
    expect(parseJobSuggestions('not json')).toBeNull();
  });
});

describe('enrichWithCompanyData', () => {
  it('adds hiring status and careers links', () => {
    const companies = enrichWithCompanyData([
      { name: 'Stripe', avgSalary: 185000, location: 'Remote' },
    ]);
    expect(companies[0]?.hiringNow).toBe(true);
    expect(companies[0]?.hiringStatus).toBe('Actively hiring');
    expect(companies[0]?.careersUrl).toContain('linkedin.com');
  });
});

describe('enrichWithSalaryData', () => {
  it('calculates ranges, increase, and five-year earnings', () => {
    const result = enrichWithSalaryData(
      { expectedSalary: 120000, yearsToReach: 0.5 },
      96000,
      24000,
    );
    expect(result.incomeIncrease).toBe(24000);
    expect(result.yearsToReach).toBe(1);
    expect(result.fiveYearEarnings).toBe(600000);
    expect(result.salaryRange?.min).toBeLessThan(120000);
    expect(result.salaryRange?.max).toBeGreaterThan(120000);
  });
});

describe('getKnowledgeBaseSuggestions', () => {
  it('suggests senior engineer progression for mid-level engineers', () => {
    const jobs = getKnowledgeBaseSuggestions(engineerProfile, 24000, 'home_purchase');
    expect(jobs.length).toBeGreaterThanOrEqual(2);
    expect(jobs[0]?.title).toContain('Senior Software Engineer');
    expect(jobs[0]?.incomeIncrease).toBeGreaterThan(0);
    expect(jobs[0]?.companies.length).toBeGreaterThanOrEqual(3);
    expect(jobs[0]?.interviewTopics.length).toBeGreaterThan(0);
    expect(jobs[0]?.resources.length).toBeGreaterThan(0);
  });

  it('suggests senior accountant progression for mid-level accountants', () => {
    const jobs = getKnowledgeBaseSuggestions(accountantProfile, 15000, 'baby');
    expect(jobs[0]?.title).toContain('Senior Accountant');
    expect(jobs[0]?.companies.some((company) => company.name === 'Deloitte')).toBe(true);
    expect(jobs[0]?.difficulty).toBe('Medium');
  });

  it('suggests senior marketing manager progression for junior marketers', () => {
    const jobs = getKnowledgeBaseSuggestions(marketerProfile, 18000, 'business');
    const titles = jobs.map((job) => job.title);
    expect(titles.some((title) => title.includes('Marketing Manager'))).toBe(true);
    expect(jobs[0]?.timeline).toMatch(/months/);
  });

  it('adapts to different locations while keeping realistic salaries', () => {
    const remoteJobs = getKnowledgeBaseSuggestions(
      { ...engineerProfile, location: 'Remote' },
      30000,
      'car_purchase',
    );
    expect(remoteJobs[0]?.companies[0]?.location).toBeTruthy();
    expect(remoteJobs[0]?.expectedSalary).toBeGreaterThan(96000);
  });
});

describe('suggestJobsForIncomeGoal', () => {
  it('uses mocked LLM responses when available', async () => {
    const mockLlmClient = jest.fn().mockResolvedValue(JSON.stringify(mockLlmJobs));
    const result = await suggestJobsForIncomeGoal(
      engineerProfile,
      24000,
      'home_purchase',
      { llmClient: mockLlmClient },
    );

    expect(mockLlmClient).toHaveBeenCalled();
    expect(result.source).toBe('llm');
    expect(result.jobs[0]?.title).toBe('Senior Software Engineer');
    expect(result.jobs[0]?.companies[0]?.hiringStatus).toBeTruthy();
  });

  it('falls back to knowledge base when LLM is unavailable', async () => {
    const result = await suggestJobsForIncomeGoal(
      accountantProfile,
      12000,
      'apartment_move',
      { llmClient: async () => null },
    );

    expect(result.source).toBe('knowledge_base');
    expect(result.jobs.length).toBeGreaterThanOrEqual(2);
    expect(result.jobs[0]?.source).toBe('knowledge_base');
  });

  it('falls back when LLM returns invalid JSON', async () => {
    const result = await suggestJobsForIncomeGoal(
      marketerProfile,
      10000,
      'baby',
      { llmClient: async () => 'Sorry, cannot help.' },
    );

    expect(result.source).toBe('knowledge_base');
    expect(result.jobs[0]?.title).toMatch(/Marketing/);
  });

  it('returns empty jobs for invalid profile input', async () => {
    const result = await suggestJobsForIncomeGoal(null, 10000, 'general');
    expect(result.jobs).toEqual([]);
  });
});
