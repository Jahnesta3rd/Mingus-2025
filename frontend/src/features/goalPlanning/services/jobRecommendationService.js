import { callClaudeApi, CLAUDE_MODEL } from './claudeClient.js';

/**
 * @typedef {Object} JobCompany
 * @property {string} name
 * @property {boolean} hiringNow
 * @property {number} avgSalary
 * @property {string} [location]
 * @property {string} [hiringStatus]
 * @property {string[]} [benefits]
 * @property {string} [careersUrl]
 */

/**
 * @typedef {Object} JobResource
 * @property {string} title
 * @property {string} url
 * @property {'course' | 'book' | 'article' | 'job_board'} type
 */

/**
 * @typedef {Object} JobSuggestion
 * @property {string} jobId
 * @property {string} title
 * @property {JobCompany[]} companies
 * @property {number} expectedSalary
 * @property {{ min: number, max: number }} salaryRange
 * @property {number} incomeIncrease
 * @property {number} yearsToReach
 * @property {number} fiveYearEarnings
 * @property {string[]} requiredSkills
 * @property {string[]} skillsToLearn
 * @property {string[]} interviewTopics
 * @property {string} typicalPath
 * @property {string} timeline
 * @property {'Low' | 'Medium' | 'High'} difficulty
 * @property {JobResource[]} resources
 * @property {string} [why]
 * @property {string} [source]
 */

const DIFFICULTY_LEVELS = new Set(['Low', 'Medium', 'High']);

/**
 * Career progression knowledge base keyed by normalized role family.
 * Salaries are approximate total compensation (base + bonus) for US metros, 2024–2025.
 */
const CAREER_PROGRESSION_KB = {
  software_engineer: {
    industry: 'Technology',
    progressions: [
      {
        title: 'Senior Software Engineer',
        difficulty: 'Medium',
        salaryMultiplier: 1.28,
        baseSalary: 165000,
        requiredSkills: ['System design', 'Code review leadership', 'Cross-team collaboration'],
        skillsToLearn: ['Distributed systems', 'Technical mentorship', 'Architecture documentation'],
        interviewTopics: ['System design', 'Data structures', 'Behavioral leadership stories'],
        typicalPath: 'Software Engineer → Senior Software Engineer → Staff Engineer',
        timeline: '3-6 months',
        yearsToReach: 0.5,
        companies: [
          { name: 'Stripe', location: 'San Francisco / Remote', hiringNow: true, avgSalary: 185000, benefits: ['Equity', 'Health', '401k'] },
          { name: 'Datadog', location: 'New York / Remote', hiringNow: true, avgSalary: 175000, benefits: ['RSU', 'Health', 'Parental leave'] },
          { name: 'HubSpot', location: 'Boston / Remote', hiringNow: true, avgSalary: 160000, benefits: ['Bonus', 'Health', 'Learning stipend'] },
          { name: 'Capital One', location: 'Multiple US hubs', hiringNow: true, avgSalary: 155000, benefits: ['Bonus', 'Health', 'Tuition assistance'] },
        ],
        resources: [
          { title: 'Grokking the System Design Interview', url: 'https://www.educative.io/courses/grokking-the-system-design-interview', type: 'course' },
          { title: 'Senior SWE roles on LinkedIn', url: 'https://www.linkedin.com/jobs/search/?keywords=Senior%20Software%20Engineer', type: 'job_board' },
        ],
      },
      {
        title: 'Staff Software Engineer',
        difficulty: 'High',
        salaryMultiplier: 1.55,
        baseSalary: 210000,
        requiredSkills: ['Org-wide technical strategy', 'Mentorship at scale', 'Roadmap influence'],
        skillsToLearn: ['Executive communication', 'Multi-team architecture', 'Technical RFC writing'],
        interviewTopics: ['Large-scale design', 'Influence without authority', 'Past technical bets'],
        typicalPath: 'Senior Software Engineer → Staff Engineer → Principal Engineer',
        timeline: '6-12 months',
        yearsToReach: 0.75,
        companies: [
          { name: 'Google', location: 'Mountain View / Remote', hiringNow: true, avgSalary: 230000, benefits: ['RSU', 'Health', 'Onsite perks'] },
          { name: 'Microsoft', location: 'Redmond / Remote', hiringNow: true, avgSalary: 215000, benefits: ['Stock', 'Health', 'ESPP'] },
          { name: 'Airbnb', location: 'San Francisco / Remote', hiringNow: true, avgSalary: 205000, benefits: ['Equity', 'Travel credit', 'Health'] },
        ],
        resources: [
          { title: 'StaffEng Book', url: 'https://staffeng.com/book', type: 'book' },
          { title: 'Staff Engineer jobs', url: 'https://www.linkedin.com/jobs/search/?keywords=Staff%20Software%20Engineer', type: 'job_board' },
        ],
      },
    ],
    roleMatchers: ['software engineer', 'developer', 'programmer', 'swe'],
  },
  accountant: {
    industry: 'Finance',
    progressions: [
      {
        title: 'Senior Accountant',
        difficulty: 'Medium',
        salaryMultiplier: 1.22,
        baseSalary: 92000,
        requiredSkills: ['Month-end close', 'GAAP reporting', 'Variance analysis'],
        skillsToLearn: ['CPA exam prep', 'ERP optimization', 'Cross-functional forecasting'],
        interviewTopics: ['Close process', 'Audit support', 'Process improvement examples'],
        typicalPath: 'Staff Accountant → Senior Accountant → Accounting Manager',
        timeline: '3-6 months',
        yearsToReach: 0.5,
        companies: [
          { name: 'Deloitte', location: 'Nationwide', hiringNow: true, avgSalary: 95000, benefits: ['Bonus', 'Health', 'CPA support'] },
          { name: 'PwC', location: 'Nationwide', hiringNow: true, avgSalary: 93000, benefits: ['Bonus', 'Health', 'Learning'] },
          { name: 'Amazon', location: 'Seattle / Remote', hiringNow: true, avgSalary: 105000, benefits: ['RSU', 'Health', '401k'] },
          { name: 'Johnson & Johnson', location: 'Multiple US hubs', hiringNow: true, avgSalary: 90000, benefits: ['Pension', 'Health', 'Bonus'] },
        ],
        resources: [
          { title: 'CPA review courses', url: 'https://www.becker.com/cpa-review', type: 'course' },
          { title: 'Senior Accountant roles', url: 'https://www.linkedin.com/jobs/search/?keywords=Senior%20Accountant', type: 'job_board' },
        ],
      },
      {
        title: 'Accounting Manager',
        difficulty: 'Medium',
        salaryMultiplier: 1.4,
        baseSalary: 115000,
        requiredSkills: ['Team leadership', 'Budget ownership', 'SOX controls'],
        skillsToLearn: ['People management', 'Executive reporting', 'ERP implementation'],
        interviewTopics: ['Team building', 'Control environment', 'Process automation'],
        typicalPath: 'Senior Accountant → Accounting Manager → Controller',
        timeline: '6-9 months',
        yearsToReach: 0.65,
        companies: [
          { name: 'Salesforce', location: 'San Francisco / Remote', hiringNow: true, avgSalary: 125000, benefits: ['Equity', 'Health', 'Volunteer time'] },
          { name: 'Intuit', location: 'Mountain View / Remote', hiringNow: true, avgSalary: 120000, benefits: ['RSU', 'Health', 'Bonus'] },
          { name: 'Target', location: 'Minneapolis', hiringNow: true, avgSalary: 110000, benefits: ['Discount', 'Health', '401k'] },
        ],
        resources: [
          { title: 'Accounting Manager interview guide', url: 'https://www.roberthalf.com/us/en/insights/career-development', type: 'article' },
        ],
      },
    ],
    roleMatchers: ['accountant', 'staff accountant', 'bookkeeper'],
  },
  marketer: {
    industry: 'Marketing',
    progressions: [
      {
        title: 'Marketing Manager',
        difficulty: 'Medium',
        salaryMultiplier: 1.25,
        baseSalary: 95000,
        requiredSkills: ['Campaign strategy', 'Budget management', 'Cross-channel analytics'],
        skillsToLearn: ['Marketing automation', 'Attribution modeling', 'Stakeholder reporting'],
        interviewTopics: ['Campaign ROI', 'Team coordination', 'Growth experiments'],
        typicalPath: 'Marketing Coordinator → Marketing Manager → Senior Marketing Manager',
        timeline: '3-6 months',
        yearsToReach: 0.5,
        companies: [
          { name: 'HubSpot', location: 'Boston / Remote', hiringNow: true, avgSalary: 105000, benefits: ['Equity', 'Health', 'Learning stipend'] },
          { name: 'Spotify', location: 'New York / Remote', hiringNow: true, avgSalary: 110000, benefits: ['RSU', 'Health', 'Parental leave'] },
          { name: 'Nike', location: 'Portland', hiringNow: true, avgSalary: 98000, benefits: ['Product discount', 'Health', 'Bonus'] },
        ],
        resources: [
          { title: 'Google Analytics certification', url: 'https://skillshop.exceedlms.com/student/path/508845-google-analytics-4-certification', type: 'course' },
          { title: 'Marketing Manager jobs', url: 'https://www.linkedin.com/jobs/search/?keywords=Marketing%20Manager', type: 'job_board' },
        ],
      },
      {
        title: 'Senior Marketing Manager',
        difficulty: 'Medium',
        salaryMultiplier: 1.45,
        baseSalary: 125000,
        requiredSkills: ['Portfolio strategy', 'Team leadership', 'Executive storytelling'],
        skillsToLearn: ['Brand positioning', 'Demand gen forecasting', 'P&L literacy'],
        interviewTopics: ['Multi-quarter planning', 'Team development', 'Budget tradeoffs'],
        typicalPath: 'Marketing Manager → Senior Marketing Manager → Director of Marketing',
        timeline: '4-8 months',
        yearsToReach: 0.6,
        companies: [
          { name: 'Adobe', location: 'San Jose / Remote', hiringNow: true, avgSalary: 135000, benefits: ['RSU', 'Health', 'ESPP'] },
          { name: 'Salesforce', location: 'San Francisco / Remote', hiringNow: true, avgSalary: 140000, benefits: ['Equity', 'Health', 'Volunteer time'] },
          { name: 'Procter & Gamble', location: 'Cincinnati', hiringNow: true, avgSalary: 120000, benefits: ['Bonus', 'Health', 'Pension'] },
        ],
        resources: [
          { title: 'Senior Marketing Manager roles', url: 'https://www.linkedin.com/jobs/search/?keywords=Senior%20Marketing%20Manager', type: 'job_board' },
        ],
      },
    ],
    roleMatchers: ['marketing coordinator', 'marketing specialist', 'junior marketer', 'marketer'],
  },
};

const DEFAULT_PROGRESSION = {
  industry: 'General',
  progressions: [
    {
      title: 'Senior Individual Contributor',
      difficulty: 'Medium',
      salaryMultiplier: 1.2,
      baseSalary: 100000,
      requiredSkills: ['Domain expertise', 'Project ownership', 'Stakeholder communication'],
      skillsToLearn: ['Leadership', 'Strategic planning', 'Cross-functional influence'],
      interviewTopics: ['Impact stories', 'Scope expansion', 'Problem solving'],
      typicalPath: 'Current role → Senior IC → Manager or Principal track',
      timeline: '3-6 months',
      yearsToReach: 0.5,
      companies: [
        { name: 'Fortune 500 employer', location: 'Your metro area', hiringNow: true, avgSalary: 105000, benefits: ['Health', '401k', 'Bonus'] },
        { name: 'Growth-stage company', location: 'Remote', hiringNow: true, avgSalary: 110000, benefits: ['Equity', 'Health', 'Flexible PTO'] },
      ],
      resources: [
        { title: 'LinkedIn job search', url: 'https://www.linkedin.com/jobs/', type: 'job_board' },
      ],
    },
  ],
  roleMatchers: [],
};

/**
 * @param {number} value
 * @returns {number}
 */
function roundCurrency(value) {
  return Math.round(value * 100) / 100;
}

/**
 * @param {unknown} value
 * @param {number} [fallback=0]
 * @returns {number}
 */
function toNumber(value, fallback = 0) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fallback;
  }
  return value;
}

/**
 * Normalizes monthly income to annual unless already flagged as annual.
 * Mingus profiles store monthly income; gap values are annual.
 * @param {Record<string, unknown>} userProfile
 * @returns {number}
 */
function getAnnualIncome(userProfile) {
  const income = toNumber(userProfile?.income, 0);
  if (userProfile?.incomeIsAnnual === true) {
    return income;
  }
  return roundCurrency(income * 12);
}

/**
 * Resolves career KB entry from job title and industry.
 * @param {Record<string, unknown>} userProfile
 * @returns {typeof DEFAULT_PROGRESSION}
 */
function resolveCareerFamily(userProfile) {
  const title = String(userProfile?.jobTitle ?? '').toLowerCase();
  const industry = String(userProfile?.industry ?? '').toLowerCase();

  for (const entry of Object.values(CAREER_PROGRESSION_KB)) {
    if (entry.roleMatchers.some((matcher) => title.includes(matcher))) {
      return entry;
    }
  }

  if (industry.includes('tech') || industry.includes('technology')) {
    return CAREER_PROGRESSION_KB.software_engineer;
  }
  if (industry.includes('finance') || industry.includes('accounting')) {
    return CAREER_PROGRESSION_KB.accountant;
  }
  if (industry.includes('marketing')) {
    return CAREER_PROGRESSION_KB.marketer;
  }

  return DEFAULT_PROGRESSION;
}

/**
 * Builds careers page URL for a company.
 * @param {string} companyName
 * @returns {string}
 */
function buildCareersUrl(companyName) {
  const slug = companyName.toLowerCase().replace(/[^a-z0-9]+/g, '');
  return `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(companyName)}`;
}

/**
 * Builds the Claude prompt for job suggestions.
 * @param {Record<string, unknown>} userProfile
 * @param {number} incomeGapNeeded - Annual income gap
 * @param {string} [goalType]
 * @param {number} [timelineYears]
 * @returns {string}
 */
export function buildJobSuggestionPrompt(
  userProfile,
  incomeGapNeeded,
  goalType = 'general',
  timelineYears = 5,
) {
  const annualIncome = getAnnualIncome(userProfile);
  const gap = Math.max(0, toNumber(incomeGapNeeded, 0));
  const location = userProfile?.location ?? userProfile?.zip_code ?? 'United States';
  const yearsOfExperience = userProfile?.yearsOfExperience ?? 'Not specified';

  return `User's current role: ${userProfile?.jobTitle ?? 'Not specified'}
Current income: $${annualIncome}
Target additional income: $${gap}
Total target: $${annualIncome + gap}
Industry: ${userProfile?.industry ?? 'Not specified'}
Location: ${location}
Years of experience: ${yearsOfExperience}

Goal type: ${goalType}
Timeline to goal: ${timelineYears} years

Generate 5 next-step job titles and specific companies.

For each job:
- Job title (be specific: "Senior Software Engineer" not just "Engineer")
- 3-4 companies actively hiring for this role (real companies, current 2024-2025)
- Expected salary (base + typical bonus)
- Increase from current salary
- Key skills needed
- Interview topics
- Why this role gets them to their goal

Return as JSON array of 5 jobs. Only JSON, no explanation.
[
  {
    "title": "string",
    "companies": [{"name": "string", "avgSalary": number}],
    "expectedSalary": number,
    "requiredSkills": ["string"],
    "interviewTopics": ["string"],
    "why": "string"
  }
]`;
}

/**
 * Parses LLM job suggestion JSON.
 * @param {string} rawResponse
 * @returns {Array<Record<string, unknown>> | null}
 */
export function parseJobSuggestions(rawResponse) {
  if (!rawResponse || typeof rawResponse !== 'string') {
    return null;
  }

  let text = rawResponse.trim();
  const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fenceMatch) {
    text = fenceMatch[1].trim();
  }

  const arrayStart = text.indexOf('[');
  const arrayEnd = text.lastIndexOf(']');
  if (arrayStart === -1 || arrayEnd === -1) {
    return null;
  }

  try {
    const parsed = JSON.parse(text.slice(arrayStart, arrayEnd + 1));
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Enriches companies with hiring status and career links.
 * @param {Array<Record<string, unknown>>} companies
 * @param {string} [defaultLocation]
 * @returns {JobCompany[]}
 */
export function enrichWithCompanyData(companies = [], defaultLocation = 'United States') {
  return (companies ?? []).map((company) => {
    const name = String(company?.name ?? 'Employer');
    return {
      name,
      hiringNow: company?.hiringNow !== false,
      avgSalary: roundCurrency(toNumber(company?.avgSalary, 0)),
      location: String(company?.location ?? defaultLocation),
      hiringStatus: company?.hiringNow === false ? 'Limited openings' : 'Actively hiring',
      benefits: Array.isArray(company?.benefits) ? company.benefits : ['Health insurance', '401(k)'],
      careersUrl: company?.careersUrl ?? buildCareersUrl(name),
    };
  });
}

/**
 * Adds compensation ranges and multi-year earnings projections.
 * @param {Record<string, unknown>} job
 * @param {number} currentAnnualIncome
 * @param {number} [incomeGapNeeded]
 * @returns {Partial<JobSuggestion>}
 */
export function enrichWithSalaryData(job, currentAnnualIncome, incomeGapNeeded = 0) {
  const expectedSalary = roundCurrency(toNumber(job?.expectedSalary, 0));
  const incomeIncrease = roundCurrency(Math.max(0, expectedSalary - currentAnnualIncome));
  const gap = Math.max(0, toNumber(incomeGapNeeded, 0));
  const yearsToCloseGap = incomeIncrease > 0 && gap > 0
    ? roundCurrency(gap / incomeIncrease)
    : toNumber(job?.yearsToReach, 0.5);

  const salaryVariance = 0.08;
  return {
    expectedSalary,
    salaryRange: {
      min: roundCurrency(expectedSalary * (1 - salaryVariance)),
      max: roundCurrency(expectedSalary * (1 + salaryVariance)),
    },
    incomeIncrease,
    yearsToReach: yearsToCloseGap,
    fiveYearEarnings: roundCurrency(expectedSalary * 5),
  };
}

/**
 * Converts a raw job record into a fully enriched suggestion.
 * @param {Record<string, unknown>} job
 * @param {Record<string, unknown>} userProfile
 * @param {number} incomeGapNeeded
 * @param {number} index
 * @param {string} source
 * @returns {JobSuggestion}
 */
function normalizeJobSuggestion(job, userProfile, incomeGapNeeded, index, source) {
  const annualIncome = getAnnualIncome(userProfile);
  const companies = enrichWithCompanyData(
    Array.isArray(job.companies) ? job.companies : [],
    String(userProfile?.location ?? 'United States'),
  );
  const salaryData = enrichWithSalaryData(job, annualIncome, incomeGapNeeded);
  const title = String(job.title ?? `Role option ${index + 1}`);
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40);

  return {
    jobId: `job-${slug}-${index + 1}`,
    title,
    companies,
    expectedSalary: salaryData.expectedSalary ?? 0,
    salaryRange: salaryData.salaryRange ?? { min: 0, max: 0 },
    incomeIncrease: salaryData.incomeIncrease ?? 0,
    yearsToReach: salaryData.yearsToReach ?? 0.5,
    fiveYearEarnings: salaryData.fiveYearEarnings ?? 0,
    requiredSkills: Array.isArray(job.requiredSkills) ? job.requiredSkills.map(String) : [],
    skillsToLearn: Array.isArray(job.skillsToLearn) ? job.skillsToLearn.map(String) : [],
    interviewTopics: Array.isArray(job.interviewTopics) ? job.interviewTopics.map(String) : [],
    typicalPath: String(job.typicalPath ?? 'Progress through increasing scope and compensation'),
    timeline: String(job.timeline ?? '3-6 months'),
    difficulty: DIFFICULTY_LEVELS.has(job.difficulty) ? job.difficulty : 'Medium',
    resources: Array.isArray(job.resources) ? job.resources : [
      {
        title: `${title} openings on LinkedIn`,
        url: `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(title)}`,
        type: 'job_board',
      },
    ],
    why: String(job.why ?? `Closes income gap with realistic ${title} compensation.`),
    source,
  };
}

/**
 * Returns knowledge-base job suggestions (sync MVP fallback).
 * @param {Record<string, unknown>} userProfile
 * @param {number} incomeGapNeeded - Annual income gap
 * @param {string} [goalType]
 * @returns {JobSuggestion[]}
 */
export function getKnowledgeBaseSuggestions(userProfile, incomeGapNeeded, goalType = 'general') {
  const family = resolveCareerFamily(userProfile ?? {});
  const annualIncome = getAnnualIncome(userProfile ?? {});
  const gap = Math.max(0, toNumber(incomeGapNeeded, 0));
  const targetIncome = annualIncome + (gap > 0 ? gap : annualIncome * 0.15);

  const ranked = [...family.progressions]
    .map((progression) => {
      const expectedSalary = roundCurrency(
        Math.max(progression.baseSalary, annualIncome * progression.salaryMultiplier),
      );
      return {
        ...progression,
        expectedSalary,
        incomeIncrease: roundCurrency(expectedSalary - annualIncome),
      };
    })
    .filter((job) => job.incomeIncrease > 0)
    .sort((a, b) => {
      const aDistance = Math.abs(a.expectedSalary - targetIncome);
      const bDistance = Math.abs(b.expectedSalary - targetIncome);
      return aDistance - bDistance;
    });

  const selected = ranked.length > 0 ? ranked : family.progressions;
  const suggestions = selected.slice(0, 5).map((job, index) => normalizeJobSuggestion({
    ...job,
    why: `A ${job.title} role in ${family.industry} provides a realistic step toward your ${goalType.replace(/_/g, ' ')} goal with approximately $${job.incomeIncrease.toLocaleString()} more per year.`,
  }, userProfile ?? {}, gap, index, 'knowledge_base'));

  while (suggestions.length < 3 && family.progressions.length > suggestions.length) {
    const next = family.progressions[suggestions.length];
    suggestions.push(normalizeJobSuggestion(next, userProfile ?? {}, gap, suggestions.length, 'knowledge_base'));
  }

  return suggestions;
}

/**
 * Suggests next-step jobs to close an annual income gap.
 * @param {Record<string, unknown>} userProfile
 * @param {number} incomeGapNeeded - Annual additional income required
 * @param {string} [goalType]
 * @param {Object} [options]
 * @param {(prompt: string, opts?: object) => Promise<string | null>} [options.llmClient]
 * @param {string} [options.apiKey]
 * @param {number} [options.timelineYears]
 * @returns {Promise<{ jobs: JobSuggestion[], source: 'llm' | 'knowledge_base' }>}
 */
export async function suggestJobsForIncomeGoal(
  userProfile,
  incomeGapNeeded,
  goalType = 'general',
  options = {},
) {
  if (!userProfile || typeof userProfile !== 'object') {
    return { jobs: [], source: 'knowledge_base' };
  }

  const gap = Math.max(0, toNumber(incomeGapNeeded, 0));
  const timelineYears = toNumber(options.timelineYears, toNumber(userProfile?.goalTimeline, 5));
  const prompt = buildJobSuggestionPrompt(userProfile, gap, goalType, timelineYears);

  const llmClient = options.llmClient
    ?? ((text) => callClaudeApi(text, { apiKey: options.apiKey, fetchFn: options.fetchFn }));

  const rawResponse = await llmClient(prompt, options);
  const parsed = rawResponse ? parseJobSuggestions(rawResponse) : null;

  if (parsed && parsed.length > 0) {
    const jobs = parsed
      .slice(0, 5)
      .map((job, index) => normalizeJobSuggestion(job, userProfile, gap, index, 'llm'));

    return { jobs, source: 'llm' };
  }

  return {
    jobs: getKnowledgeBaseSuggestions(userProfile, gap, goalType),
    source: 'knowledge_base',
  };
}

export { CLAUDE_MODEL };
export default suggestJobsForIncomeGoal;
