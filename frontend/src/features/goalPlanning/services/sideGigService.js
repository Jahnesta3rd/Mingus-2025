import { callClaudeApi, CLAUDE_MODEL } from './claudeClient.js';

/**
 * @typedef {'freelance' | 'consulting' | 'gig_work' | 'passive_income' | 'reselling'} GigType
 */

/**
 * @typedef {Object} SideGigSuggestion
 * @property {string} gigId
 * @property {GigType | string} type
 * @property {string} title
 * @property {string} description
 * @property {Array<{name: string, url: string, signupTime: string}>} platforms
 * @property {{ min: number, max: number }} estimatedMonthly
 * @property {number} hoursPerWeek
 * @property {string} startupTime
 * @property {'Low' | 'Medium' | 'High'} difficulty
 * @property {string[]} pros
 * @property {string[]} cons
 * @property {string[]} requiredSkills
 * @property {number} initialInvestment
 * @property {'Limited' | 'Moderate' | 'High'} scalability
 * @property {Array<{step: number, description: string, timeNeeded: string}>} signupSteps
 * @property {Array<{title: string, url: string}>} resources
 * @property {Array<{month: number, earnings: number, effort: string}>} monthlyProjection
 * @property {string[]} firstClientTips
 * @property {string} [source]
 */

const WEEKS_PER_MONTH = 4.33;
const DIFFICULTY_LEVELS = new Set(['Low', 'Medium', 'High']);
const GIG_TYPES = new Set(['freelance', 'consulting', 'gig_work', 'passive_income', 'reselling']);

const PLATFORM_URLS = {
  Toptal: 'https://www.toptal.com/',
  Upwork: 'https://www.upwork.com/',
  Fiverr: 'https://www.fiverr.com/',
  Contra: 'https://contra.com/',
  Gun: 'https://gun.io/',
  '99designs': 'https://99designs.com/',
  Dribbble: 'https://dribbble.com/jobs',
  Etsy: 'https://www.etsy.com/',
  Preply: 'https://preply.com/',
  Chegg: 'https://www.chegg.com/tutors/',
  WriterAccess: 'https://www.writeraccess.com/',
  Clarity: 'https://clarity.fm/',
  TaskRabbit: 'https://www.taskrabbit.com/',
  Rover: 'https://www.rover.com/',
  DoorDash: 'https://www.doordash.com/dasher/',
  Medium: 'https://medium.com/',
};

/**
 * Side gig knowledge base by profession family.
 */
const SIDE_GIG_KB = {
  software_engineer: {
    matchers: ['software engineer', 'developer', 'programmer', 'swe'],
    gigs: [
      {
        type: 'freelance',
        title: 'Freelance Web Development',
        description: 'Build websites and small apps for startups and local businesses on contract.',
        hourlyRate: 65,
        platforms: ['Upwork', 'Contra', 'Toptal'],
        difficulty: 'Medium',
        startupTime: '1-2 weeks',
        initialInvestment: 0,
        scalability: 'Moderate',
        requiredSkills: ['JavaScript', 'React', 'API integration'],
        pros: ['High hourly rates', 'Remote-friendly', 'Leverages existing skills'],
        cons: ['Client acquisition takes time', 'Income can be lumpy'],
      },
      {
        type: 'consulting',
        title: 'Technical Consulting',
        description: 'Advise teams on architecture, code reviews, and delivery bottlenecks.',
        hourlyRate: 95,
        platforms: ['Toptal', 'Clarity', 'Upwork'],
        difficulty: 'High',
        startupTime: '1 month',
        initialInvestment: 0,
        scalability: 'Limited',
        requiredSkills: ['System design', 'Communication', 'Problem diagnosis'],
        pros: ['Premium rates', 'Flexible engagements'],
        cons: ['Requires credibility and referrals', 'Harder first clients'],
      },
      {
        type: 'passive_income',
        title: 'Developer Content & Tutorials',
        description: 'Publish technical tutorials, templates, or paid newsletters.',
        hourlyRate: 40,
        platforms: ['Medium', 'Gumroad'],
        difficulty: 'Medium',
        startupTime: '1 month',
        initialInvestment: 50,
        scalability: 'High',
        requiredSkills: ['Writing', 'Teaching', 'Topic expertise'],
        pros: ['Compounds over time', 'Low client overhead'],
        cons: ['Slow to monetize', 'Needs consistent publishing'],
      },
    ],
  },
  marketer: {
    matchers: ['marketing', 'marketer', 'growth'],
    gigs: [
      {
        type: 'freelance',
        title: 'Social Media Management',
        description: 'Manage content calendars and analytics for small business accounts.',
        hourlyRate: 45,
        platforms: ['Upwork', 'Fiverr'],
        difficulty: 'Low',
        startupTime: '1-2 weeks',
        initialInvestment: 0,
        scalability: 'Moderate',
        requiredSkills: ['Content planning', 'Canva', 'Analytics'],
        pros: ['Recurring monthly retainers', 'Easy to package services'],
        cons: ['Client churn', 'Weekend posting sometimes required'],
      },
      {
        type: 'freelance',
        title: 'Freelance Copywriting',
        description: 'Write landing pages, email sequences, and ad copy for brands.',
        hourlyRate: 55,
        platforms: ['Upwork', 'WriterAccess'],
        difficulty: 'Medium',
        startupTime: '1-2 weeks',
        initialInvestment: 0,
        scalability: 'Moderate',
        requiredSkills: ['Copywriting', 'SEO basics', 'Client communication'],
        pros: ['Fully remote', 'Portfolio builds quickly'],
        cons: ['Revision cycles', 'Rate pressure on marketplaces'],
      },
      {
        type: 'consulting',
        title: 'Marketing Strategy Consulting',
        description: 'Run audits and 90-day growth plans for early-stage companies.',
        hourlyRate: 75,
        platforms: ['Clarity', 'Upwork'],
        difficulty: 'Medium',
        startupTime: '1 month',
        initialInvestment: 0,
        scalability: 'Limited',
        requiredSkills: ['Funnel analysis', 'Positioning', 'Reporting'],
        pros: ['High-value projects', 'Short engagements'],
        cons: ['Needs case studies', 'Sales effort required'],
      },
    ],
  },
  designer: {
    matchers: ['designer', 'ui', 'ux', 'graphic'],
    gigs: [
      {
        type: 'freelance',
        title: 'UI/UX Design Contracts',
        description: 'Design product screens, prototypes, and design systems for startups.',
        hourlyRate: 60,
        platforms: ['Upwork', 'Contra', 'Dribbble'],
        difficulty: 'Medium',
        startupTime: '1-2 weeks',
        initialInvestment: 0,
        scalability: 'Moderate',
        requiredSkills: ['Figma', 'Prototyping', 'User research basics'],
        pros: ['Strong demand', 'Portfolio-driven sales'],
        cons: ['Scope creep risk', 'Revision-heavy work'],
      },
      {
        type: 'freelance',
        title: 'Logo & Brand Design',
        description: 'Deliver brand kits and logo packages for small businesses.',
        hourlyRate: 50,
        platforms: ['99designs', 'Fiverr'],
        difficulty: 'Low',
        startupTime: 'immediate',
        initialInvestment: 0,
        scalability: 'Moderate',
        requiredSkills: ['Illustrator', 'Branding', 'Client briefs'],
        pros: ['Fast turnaround projects', 'Clear deliverables'],
        cons: ['Competitive pricing on marketplaces', 'Spec work on some platforms'],
      },
      {
        type: 'reselling',
        title: 'Digital Template Shop',
        description: 'Sell Notion, Canva, or presentation templates online.',
        hourlyRate: 35,
        platforms: ['Etsy', 'Gumroad'],
        difficulty: 'Medium',
        startupTime: '1 month',
        initialInvestment: 30,
        scalability: 'High',
        requiredSkills: ['Template design', 'Product listing', 'Basic marketing'],
        pros: ['Passive income potential', 'No client calls'],
        cons: ['Upfront creation time', 'Marketplace fees'],
      },
    ],
  },
  accountant: {
    matchers: ['accountant', 'bookkeeper', 'cpa'],
    gigs: [
      {
        type: 'freelance',
        title: 'Bookkeeping for Small Businesses',
        description: 'Monthly bookkeeping and reconciliations for freelancers and shops.',
        hourlyRate: 45,
        platforms: ['Upwork', 'Fiverr'],
        difficulty: 'Low',
        startupTime: '1-2 weeks',
        initialInvestment: 0,
        scalability: 'Moderate',
        requiredSkills: ['QuickBooks', 'Reconciliation', 'Reporting'],
        pros: ['Recurring retainers', 'Predictable hours'],
        cons: ['Tax season crunch', 'Client data security responsibility'],
      },
      {
        type: 'consulting',
        title: 'Tax Prep Side Practice',
        description: 'Prepare individual and sole-prop returns during tax season.',
        hourlyRate: 55,
        platforms: ['Upwork', 'Local referrals'],
        difficulty: 'Medium',
        startupTime: '1 month',
        initialInvestment: 200,
        scalability: 'Limited',
        requiredSkills: ['Tax software', 'IRS rules', 'Client intake'],
        pros: ['Seasonal income spikes', 'High trust value'],
        cons: ['Liability considerations', 'Seasonal demand curve'],
      },
    ],
  },
  writer: {
    matchers: ['writer', 'copywriter', 'content'],
    gigs: [
      {
        type: 'freelance',
        title: 'Content Writing',
        description: 'Blog posts, newsletters, and website copy for B2B companies.',
        hourlyRate: 40,
        platforms: ['Upwork', 'WriterAccess'],
        difficulty: 'Low',
        startupTime: '1-2 weeks',
        initialInvestment: 0,
        scalability: 'Moderate',
        requiredSkills: ['Writing', 'Research', 'SEO'],
        pros: ['Low startup cost', 'Flexible deadlines'],
        cons: ['Per-word rate pressure', 'Editing overhead'],
      },
    ],
  },
  teacher: {
    matchers: ['teacher', 'tutor', 'educator'],
    gigs: [
      {
        type: 'consulting',
        title: 'Online Tutoring',
        description: 'Tutor students in math, science, or test prep online.',
        hourlyRate: 35,
        platforms: ['Preply', 'Chegg'],
        difficulty: 'Low',
        startupTime: 'immediate',
        initialInvestment: 0,
        scalability: 'Limited',
        requiredSkills: ['Subject expertise', 'Patience', 'Lesson planning'],
        pros: ['Immediate signup', 'Steady hourly work'],
        cons: ['Hour cap limits income', 'Platform commission'],
      },
    ],
  },
  general: {
    matchers: [],
    gigs: [
      {
        type: 'gig_work',
        title: 'Task-Based Gig Work',
        description: 'Flexible local tasks and errands through gig platforms.',
        hourlyRate: 22,
        platforms: ['TaskRabbit', 'DoorDash'],
        difficulty: 'Low',
        startupTime: 'immediate',
        initialInvestment: 0,
        scalability: 'Limited',
        requiredSkills: ['Reliability', 'Time management'],
        pros: ['Start same day', 'No special credentials'],
        cons: ['Physically demanding', 'Low scalability'],
      },
      {
        type: 'gig_work',
        title: 'Pet Sitting & Dog Walking',
        description: 'Walk dogs or house-sit pets on evenings and weekends.',
        hourlyRate: 20,
        platforms: ['Rover'],
        difficulty: 'Low',
        startupTime: '1-2 weeks',
        initialInvestment: 0,
        scalability: 'Limited',
        requiredSkills: ['Animal care', 'Reliability'],
        pros: ['Enjoyable side work', 'Repeat clients'],
        cons: ['Weather dependent', 'Income ceiling'],
      },
    ],
  },
};

const FIRST_CLIENT_TIPS = {
  freelance: [
    'Start with a narrow niche offer and a fixed-scope starter package.',
    'Send 10 tailored proposals per week instead of mass templates.',
    'Ask for a testimonial after the first successful delivery.',
  ],
  consulting: [
    'Offer a paid 60-minute diagnostic session before larger engagements.',
    'Lead with a clear outcome statement in your profile headline.',
    'Share one relevant case study, even from volunteer or internal work.',
  ],
  gig_work: [
    'Complete profile verification and background checks immediately.',
    'Work peak demand windows first to build ratings quickly.',
    'Track mileage and expenses for tax deductions.',
  ],
  passive_income: [
    'Publish consistently for 8–12 weeks before judging revenue.',
    'Bundle small products into a higher-value package.',
    'Repurpose one core idea across multiple formats.',
  ],
  reselling: [
    'Launch with 3–5 listings to test demand before scaling inventory.',
    'Use high-quality mockups and keyword-rich titles.',
    'Reinvest first month profits into best-selling SKUs only.',
  ],
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
 * Resolves profession family from profile.
 * @param {Record<string, unknown>} userProfile
 * @returns {typeof SIDE_GIG_KB.general}
 */
function resolveGigFamily(userProfile) {
  const title = String(userProfile?.jobTitle ?? '').toLowerCase();
  const industry = String(userProfile?.industry ?? '').toLowerCase();
  const skills = (userProfile?.skills ?? []).map((s) => String(s).toLowerCase());

  for (const [key, family] of Object.entries(SIDE_GIG_KB)) {
    if (key === 'general') continue;
    if (family.matchers.some((matcher) => title.includes(matcher) || industry.includes(matcher))) {
      return family;
    }
  }

  if (skills.some((s) => ['react', 'javascript', 'node', 'python'].some((k) => s.includes(k)))) {
    return SIDE_GIG_KB.software_engineer;
  }
  if (skills.some((s) => ['design', 'figma', 'ui', 'ux'].some((k) => s.includes(k)))) {
    return SIDE_GIG_KB.designer;
  }
  if (skills.some((s) => ['marketing', 'seo', 'copy'].some((k) => s.includes(k)))) {
    return SIDE_GIG_KB.marketer;
  }

  return SIDE_GIG_KB.general;
}

/**
 * Builds platform objects with signup URLs.
 * @param {string[]} platformNames
 * @returns {Array<{name: string, url: string, signupTime: string}>}
 */
function buildPlatforms(platformNames) {
  return platformNames.map((name) => ({
    name,
    url: PLATFORM_URLS[name] ?? `https://www.google.com/search?q=${encodeURIComponent(name)}+signup`,
    signupTime: name === 'Toptal' ? '1-2 weeks screening' : 'immediate',
  }));
}

/**
 * Returns first-client tips for a gig type.
 * @param {string} type
 * @param {string} [platformName]
 * @returns {string[]}
 */
export function getFirstClientTips(type, platformName) {
  const base = FIRST_CLIENT_TIPS[type] ?? FIRST_CLIENT_TIPS.freelance;
  if (platformName) {
    return [
      ...base,
      `Optimize your ${platformName} profile with a specific niche headline and 3 portfolio samples.`,
    ];
  }
  return [...base];
}

/**
 * Estimates month-by-month earnings with a learning curve.
 * @param {Object} params
 * @param {number} params.hourlyRate
 * @param {number} params.hoursPerWeek
 * @param {number} [params.months=6]
 * @param {number} [params.initialInvestment=0]
 * @returns {Array<{month: number, earnings: number, effort: string}>}
 */
export function estimateEarningsTrajectory({
  hourlyRate,
  hoursPerWeek,
  months = 6,
  initialInvestment = 0,
}) {
  const steadyMonthly = hourlyRate * hoursPerWeek * WEEKS_PER_MONTH;
  const ramp = [0.3, 0.5, 0.7, 0.85, 0.95, 1.0];
  const projection = [];

  for (let month = 1; month <= months; month += 1) {
    const factor = ramp[Math.min(month - 1, ramp.length - 1)];
    let earnings = roundCurrency(steadyMonthly * factor);
    if (month === 1 && initialInvestment > 0) {
      earnings = roundCurrency(Math.max(0, earnings - initialInvestment));
    }

    let effort = 'Steady';
    if (factor < 0.5) effort = 'High setup';
    else if (factor < 0.8) effort = 'Moderate';
    else effort = 'Optimized';

    projection.push({ month, earnings, effort });
  }

  return projection;
}

/**
 * Builds the Claude prompt for side gig suggestions.
 * @param {Record<string, unknown>} userProfile
 * @param {number} monthlyTargetIncome
 * @param {number} availableHoursPerWeek
 * @returns {string}
 */
export function buildSideGigPrompt(userProfile, monthlyTargetIncome, availableHoursPerWeek) {
  const skills = Array.isArray(userProfile?.skills) ? userProfile.skills : [];
  const monthlyIncome = toNumber(userProfile?.income, 0);

  return `User profile for side gigs:
- Skills: ${skills.length > 0 ? skills.join(', ') : 'Not specified'}
- Current job: ${userProfile?.jobTitle ?? 'Not specified'} (${userProfile?.industry ?? 'Not specified'})
- Available hours/week: ${availableHoursPerWeek}
- Target monthly income: $${monthlyTargetIncome}
- Current income: $${monthlyIncome}

Generate 5 side gig opportunities realistic for this person.

For each:
- Type of gig (freelancing, consulting, gig work, etc)
- Platform(s) to use (Toptal, Upwork, Fiverr, Rover, etc)
- Realistic monthly income potential
- Hours per week needed
- How to get started (steps, timeline)
- Common pitfalls
- Why this suits them

Return only JSON:
[
  {
    "type": "string",
    "title": "string",
    "platforms": [{"name": "string", "monthlyEarnings": number}],
    "hoursPerWeek": number,
    "startupTime": "string",
    "steps": ["string"],
    "pros": ["string"],
    "cons": ["string"]
  }
]`;
}

/**
 * Parses LLM side gig JSON response.
 * @param {string} rawResponse
 * @returns {Array<Record<string, unknown>> | null}
 */
export function parseSideGigSuggestions(rawResponse) {
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
 * Normalizes a gig record into the full suggestion shape.
 * @param {Record<string, unknown>} gig
 * @param {Record<string, unknown>} userProfile
 * @param {number} availableHoursPerWeek
 * @param {number} monthlyTargetIncome
 * @param {number} index
 * @param {string} source
 * @returns {SideGigSuggestion}
 */
function normalizeGigSuggestion(
  gig,
  userProfile,
  availableHoursPerWeek,
  monthlyTargetIncome,
  index,
  source,
) {
  const hoursPerWeek = Math.min(
    availableHoursPerWeek,
    Math.max(1, toNumber(gig.hoursPerWeek, Math.ceil(availableHoursPerWeek * 0.8))),
  );

  const platformNames = Array.isArray(gig.platforms)
    ? gig.platforms.map((p) => (typeof p === 'string' ? p : p?.name)).filter(Boolean)
    : [];

  const hourlyRate = toNumber(gig.hourlyRate, 0);
  const platformEarnings = Array.isArray(gig.platforms)
    ? gig.platforms.map((p) => toNumber(p?.monthlyEarnings, 0)).filter((v) => v > 0)
    : [];

  const steadyMonthly = hourlyRate > 0
    ? hourlyRate * hoursPerWeek * WEEKS_PER_MONTH
    : (platformEarnings[0] ?? 0);

  const minMonthly = roundCurrency(steadyMonthly * 0.75);
  const maxMonthly = roundCurrency(Math.min(
    steadyMonthly * 1.15,
    monthlyTargetIncome > 0 ? monthlyTargetIncome * 1.1 : steadyMonthly * 1.15,
  ));

  const type = GIG_TYPES.has(gig.type) ? gig.type : 'freelance';
  const title = String(gig.title ?? `Side gig option ${index + 1}`);
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40);
  const initialInvestment = toNumber(gig.initialInvestment, 0);
  const projection = estimateEarningsTrajectory({
    hourlyRate: hourlyRate || steadyMonthly / Math.max(1, hoursPerWeek * WEEKS_PER_MONTH),
    hoursPerWeek,
    months: 6,
    initialInvestment,
  });

  const steps = Array.isArray(gig.steps) ? gig.steps : Array.isArray(gig.signupSteps)
    ? gig.signupSteps.map((s) => String(s))
    : [
      'Create platform profile with niche positioning',
      'Add 3 portfolio samples or case studies',
      'Submit 10 targeted proposals in week one',
    ];

  return {
    gigId: `gig-${slug}-${index + 1}`,
    type,
    title,
    description: String(gig.description ?? `Earn extra income through ${title.toLowerCase()}.`),
    platforms: buildPlatforms(platformNames.length > 0 ? platformNames : ['Upwork']),
    estimatedMonthly: { min: minMonthly, max: maxMonthly },
    hoursPerWeek,
    startupTime: String(gig.startupTime ?? '1-2 weeks'),
    difficulty: DIFFICULTY_LEVELS.has(gig.difficulty) ? gig.difficulty : 'Medium',
    pros: Array.isArray(gig.pros) ? gig.pros.map(String) : [],
    cons: Array.isArray(gig.cons) ? gig.cons.map(String) : [],
    requiredSkills: Array.isArray(gig.requiredSkills)
      ? gig.requiredSkills.map(String)
      : (userProfile?.skills ?? []).slice(0, 3).map(String),
    initialInvestment,
    scalability: ['Limited', 'Moderate', 'High'].includes(gig.scalability)
      ? gig.scalability
      : 'Moderate',
    signupSteps: steps.map((step, stepIndex) => ({
      step: stepIndex + 1,
      description: String(step),
      timeNeeded: stepIndex === 0 ? '1-2 hours' : '2-4 hours',
    })),
    resources: Array.isArray(gig.resources)
      ? gig.resources
      : buildPlatforms(platformNames.length > 0 ? platformNames : ['Upwork']).map((p) => ({
        title: `${p.name} signup`,
        url: p.url,
      })),
    monthlyProjection: projection,
    firstClientTips: getFirstClientTips(type, platformNames[0]),
    source,
  };
}

/**
 * Knowledge-base side gig suggestions (sync MVP).
 * @param {Record<string, unknown>} userProfile
 * @param {number} monthlyTargetIncome
 * @param {number} availableHoursPerWeek
 * @returns {SideGigSuggestion[]}
 */
export function getKnowledgeBaseSideGigs(userProfile, monthlyTargetIncome, availableHoursPerWeek) {
  const hours = Math.max(0, toNumber(availableHoursPerWeek, 10));
  if (hours === 0) {
    return [];
  }

  const family = resolveGigFamily(userProfile ?? {});
  const target = Math.max(0, toNumber(monthlyTargetIncome, 0));

  const ranked = [...family.gigs, ...SIDE_GIG_KB.general.gigs]
    .map((gig) => {
      const gigHours = Math.min(hours, Math.max(2, Math.round(hours * 0.85)));
      const steadyMonthly = gig.hourlyRate * gigHours * WEEKS_PER_MONTH;
      return { ...gig, gigHours, steadyMonthly };
    })
    .sort((a, b) => {
      if (target > 0) {
        const aDistance = Math.abs(a.steadyMonthly - target);
        const bDistance = Math.abs(b.steadyMonthly - target);
        return aDistance - bDistance;
      }
      return b.steadyMonthly - a.steadyMonthly;
    });

  const unique = [];
  const seen = new Set();
  ranked.forEach((gig) => {
    if (!seen.has(gig.title) && unique.length < 5) {
      seen.add(gig.title);
      unique.push(gig);
    }
  });

  return unique.map((gig, index) => normalizeGigSuggestion({
    ...gig,
    hoursPerWeek: gig.gigHours,
    hourlyRate: gig.hourlyRate,
    platforms: gig.platforms,
    steps: [
      `Create profiles on ${gig.platforms.slice(0, 2).join(' and ')}`,
      'Publish 3 portfolio samples aligned to a specific niche',
      'Send 10 targeted proposals in the first 2 weeks',
    ],
  }, userProfile ?? {}, hours, target, index, 'knowledge_base'));
}

/**
 * Suggests side gigs to reach a monthly income target.
 * @param {Record<string, unknown>} userProfile
 * @param {number} monthlyTargetIncome
 * @param {number} availableHoursPerWeek
 * @param {Object} [options]
 * @param {(prompt: string, opts?: object) => Promise<string | null>} [options.llmClient]
 * @returns {Promise<{ gigs: SideGigSuggestion[], source: 'llm' | 'knowledge_base' }>}
 */
export async function suggestSideGigs(
  userProfile,
  monthlyTargetIncome,
  availableHoursPerWeek,
  options = {},
) {
  if (!userProfile || typeof userProfile !== 'object') {
    return { gigs: [], source: 'knowledge_base' };
  }

  const hours = Math.max(0, toNumber(availableHoursPerWeek, toNumber(userProfile?.availableHours, 10)));
  const target = Math.max(0, toNumber(monthlyTargetIncome, 0));

  if (hours === 0) {
    return { gigs: [], source: 'knowledge_base' };
  }

  const prompt = buildSideGigPrompt(userProfile, target, hours);
  const llmClient = options.llmClient
    ?? ((text) => callClaudeApi(text, { apiKey: options.apiKey, fetchFn: options.fetchFn }));

  const rawResponse = await llmClient(prompt, options);
  const parsed = rawResponse ? parseSideGigSuggestions(rawResponse) : null;

  if (parsed && parsed.length > 0) {
    const gigs = parsed
      .slice(0, 5)
      .map((gig, index) => normalizeGigSuggestion(
        gig,
        userProfile,
        hours,
        target,
        index,
        'llm',
      ));

    return { gigs, source: 'llm' };
  }

  return {
    gigs: getKnowledgeBaseSideGigs(userProfile, target, hours),
    source: 'knowledge_base',
  };
}

export { CLAUDE_MODEL };
export default suggestSideGigs;
