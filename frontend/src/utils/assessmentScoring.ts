/**
 * Point-weighted scoring for landing page assessments.
 * Each assessment totals 100 points; score bands determine risk_level and recommendations.
 */

export interface ScoringResult {
  score: number;
  risk_level: string;
  recommendations: string[];
  /** Awareness score (0-100): average of points from knowledge/benchmarking questions. */
  subscores?: { awareness: number; action: number };
}

const SCORE_MIN = 0;
const SCORE_MAX = 100;

function clamp(score: number): number {
  return Math.max(SCORE_MIN, Math.min(SCORE_MAX, Math.round(score)));
}

/** Get points for a single-select by exact option text. */
function pts(answers: Record<string, unknown>, id: string, map: Record<string, number>): number {
  const v = answers[id];
  if (v === undefined || v === null) return 0;
  const s = String(v).trim();
  return map[s] ?? 0;
}

/** Resolve scale points by option index (0 = first option). */
function scalePtsByIndex(answers: Record<string, unknown>, id: string, optionOrder: string[], points: number[]): number {
  const v = answers[id];
  if (v === undefined || v === null) return 0;
  const s = String(v).trim();
  const idx = optionOrder.indexOf(s);
  if (idx < 0 || idx >= points.length) return 0;
  return points[idx];
}

// --- AI REPLACEMENT RISK (lower score = higher risk) ---
function scoreAiRisk(answers: Record<string, unknown>): ScoringResult {
  const q1: Record<string, number> = {
    'Decision-making': 15,
    'Customer communications': 12,
    'Research and summarizing': 9,
    'Administrative/scheduling': 3,
    'Data entry or reporting': 0,
    "I genuinely don't know": -5
  };
  const q2: Record<string, number> = {
    "No, I don't think so": 15,
    "I'm not sure": 8,
    'Yes, in a minor way': 5,
    'Yes, significantly': 0
  };
  const q3: Record<string, number> = {
    'Immediately': 15,
    'Within a few days': 12,
    'Within a week or two': 8,
    'A month or more': 3,
    'Probably not for a while': 0
  };
  const q5: Record<string, number> = {
    'I help others adopt it': 12,
    'I try to learn it early': 9,
    'I adopt it when required': 6,
    'I wait to see what others do': 3,
    'I resist it and stick to what works': 0
  };
  const q6: Record<string, number> = {
    'Yes, completely': 11,
    'Mostly': 8,
    'Somewhat': 5,
    'Not really': 2,
    'No, not at all': 0
  };
  const q7Scale = ['Almost all in my head', 'Mostly in my head', 'Split roughly evenly', 'Mostly documented', 'Almost entirely documented'];
  const q7Pts = [0, 4, 6, 8, 10]; // reversed: head = low, documented = high
  const q8: Record<string, number> = {
    'No': 10,
    "Not that I'm aware of": 8,
    'Not yet but I can see it coming': 5,
    'Yes, one or two things': 2,
    'Yes, several tasks': 0
  };
  const q9: Record<string, number> = {
    'Already using them actively': 5,
    'No time': 3,
    'No access or resources': 3,
    "Don't see the relevance": 1,
    'Worried it will replace me': 0,
    'No particular reason': 3
  };
  const q10: Record<string, number> = {
    'Greater than 90%': 5,
    '75-90%': 4,
    '50-75%': 3,
    '25-50%': 1,
    'Less than 25% chance it survives unchanged': 0
  };

  let total =
    pts(answers, 'automateFirst', q1) +
    pts(answers, 'replacedByProcess', q2) +
    pts(answers, 'productivityDrop', q3) +
    scalePtsByIndex(answers, 'proactiveLearning', ['Never', 'Rarely', 'Sometimes', 'Often', 'Constantly'], [0, 3, 6, 9, 12]) +
    pts(answers, 'newTechReaction', q5) +
    pts(answers, 'salaryDecidersUnderstand', q6) +
    scalePtsByIndex(answers, 'valueInHeadVsDocumented', q7Scale, q7Pts) +
    pts(answers, 'toolTookOverTask', q8) +
    pts(answers, 'reasonNotLearningAI', q9) +
    pts(answers, 'jobExistsFiveYears', q10);

  const score = clamp(total);

  let risk_level: string;
  if (score <= 25) risk_level = 'High Risk';
  else if (score <= 50) risk_level = 'Elevated Risk';
  else if (score <= 75) risk_level = 'Moderate Risk';
  else risk_level = 'Low Risk';

  const recommendations = [
    'Develop skills in areas where human judgment is irreplaceable',
    'Learn to work alongside AI tools rather than compete with them',
    'Focus on creative problem-solving and emotional intelligence',
    'Stay updated with AI trends in your industry'
  ];

  const q6Pts = pts(answers, 'salaryDecidersUnderstand', q6);
  const valueInHeadPts = scalePtsByIndex(answers, 'valueInHeadVsDocumented', q7Scale, q7Pts);
  const q10Pts = pts(answers, 'jobExistsFiveYears', q10);
  const awarenessPts = q6Pts + valueInHeadPts + q10Pts;
  const actionPts = total - awarenessPts;
  const awarenessMax = 11 + 10 + 5;
  const actionMax = 15 + 15 + 15 + 12 + 12 + 10 + 5;
  const subscores = {
    awareness: clamp(awarenessMax > 0 ? (awarenessPts / awarenessMax) * 100 : 50),
    action: clamp(actionMax > 0 ? (actionPts / actionMax) * 100 : 50)
  };

  return { score, risk_level, recommendations, subscores };
}

// --- INCOME COMPARISON ---
function scoreIncomeComparison(answers: Record<string, unknown>): ScoringResult {
  const q1: Record<string, number> = {
    'Within the last 3 months': 15,
    '6-12 months ago': 11,
    '1-2 years ago': 7,
    'More than 2 years ago': 3,
    'Never': 0
  };
  const q2: Record<string, number> = {
    'Yes, and I got more than the initial offer': 15,
    'Yes, but I accepted the first counter': 10,
    'No, I accepted without negotiating': 3,
    "I didn't think I could negotiate": 1,
    "I don't remember": 5
  };
  const q3: Record<string, number> = {
    'Ask my manager immediately': 15,
    'Research whether it\'s true first': 12,
    'Update my resume': 9,
    'Leave as soon as possible': 6,
    'Feel upset but probably do nothing': 0
  };
  const q5: Record<string, number> = {
    'I have been earning more': 12,
    'Limited opportunities at my company': 8,
    "My skills aren't in high demand": 4,
    'Personal circumstances limited my ability to move': 6,
    "Didn't ask for a raise": 0,
    "I don't know": 3
  };
  const q8: Record<string, number> = {
    "No, I've always pursued better pay": 5,
    'Not applicable': 4,
    'Yes, once': 2,
    'Yes, multiple times': 0
  };

  const q1Pts = pts(answers, 'lastSalaryResearch', q1);
  const q2Pts = pts(answers, 'lastRaiseNegotiate', q2);
  const q3Pts = pts(answers, 'colleagueEarnedMore', q3);
  const q4Pts = scalePtsByIndex(answers, 'benchmarkSalaryFrequency', ['Never', 'Rarely', 'Once a year', 'Every few months', 'Continuously'], [0, 3, 6, 9, 12]);
  const q5Pts = pts(answers, 'reasonNotEarnedMore', q5);
  const q6Pts = scalePtsByIndex(answers, 'incomeGrowthInitiative', ['Almost all just happened', 'Mostly happened to me', 'Roughly equal', 'Mostly my initiative', 'Almost entirely my own doing'], [0, 3, 6, 9, 11]);
  const q7Pts = scalePtsByIndex(answers, 'incomeSameFiveYears', ['No impact at all', 'Minor inconvenience', 'Moderate concern', 'Serious problem', 'It would be devastating'], [0, 2, 4, 6, 8]);
  const q8Pts = pts(answers, 'turnedDownHigherPay', q8);
  const q9Pts = scalePtsByIndex(answers, 'understandTotalComp', ['Not at all', 'Vaguely', 'Somewhat', 'Pretty well', 'Completely'], [0, 1, 2, 3, 4]);
  const total = q1Pts + q2Pts + q3Pts + q4Pts + q5Pts + q6Pts + q7Pts + q8Pts + q9Pts;

  const score = clamp(total);

  let risk_level: string;
  if (score <= 25) risk_level = 'Significant Gap';
  else if (score <= 50) risk_level = 'Awareness Gap';
  else if (score <= 75) risk_level = 'Active but Incomplete';
  else risk_level = 'Income Optimized';

  const recommendations = [
    'Research salary benchmarks for your role and location',
    'Document your achievements and value to the company',
    'Practice your negotiation skills and timing',
    'Consider additional certifications or training'
  ];

  const awarenessPts = q1Pts + q4Pts + q9Pts;
  const actionPts = q2Pts + q3Pts + q5Pts + q6Pts + q7Pts + q8Pts;
  const subscores = {
    awareness: clamp((awarenessPts / 31) * 100),
    action: clamp((actionPts / 69) * 100)
  };
  return { score, risk_level, recommendations, subscores };
}

// --- CUFFING SEASON ---
function scoreCuffingSeason(answers: Record<string, unknown>): ScoringResult {
  const q1: Record<string, number> = {
    "I'm currently in a relationship": 15,
    'Compatibility issues': 12,
    'Timing or life circumstances': 10,
    'Financial stress': 7,
    'Emotional unavailability (theirs)': 8,
    'Emotional unavailability (mine)': 4,
    "I'm not sure": 5
  };
  const barriers = [
    'Work schedule or career demands',
    'Financial stress',
    'Where I live',
    'My own emotional state',
    'Past relationship baggage'
  ];
  const q6: Record<string, number> = {
    'No, not at all': 11,
    'Yes, a minor issue': 8,
    "I haven't been in a serious relationship": 7,
    'Yes, it was a major issue': 3
  };
  const q7: Record<string, number> = {
    "Nothing - I'm ready to commit": 10,
    'Not applicable': 8,
    'Making the wrong choice': 7,
    'Getting hurt again': 5,
    'Financial entanglement': 4,
    'Losing my independence': 4
  };

  let q2Pts = 15;
  const selected: string[] = Array.isArray(answers['whatWouldGetInWay']) ? (answers['whatWouldGetInWay'] as string[]) : [];
  if (selected.includes("Nothing - I'm ready")) {
    q2Pts = 15;
  } else if (selected.includes("I don't know")) {
    q2Pts = 8;
  } else {
    const barrierCount = selected.filter((s) => barriers.includes(s)).length;
    q2Pts = Math.max(0, 15 - 5 * barrierCount);
  }

  const q1Pts = pts(answers, 'lastRelationshipEnded', q1);
  const q3Pts = scalePtsByIndex(answers, 'datingHabitsAligned', ['Completely misaligned', 'Somewhat misaligned', 'Neutral', 'Mostly aligned', 'Completely aligned'], [0, 4, 8, 12, 15]);
  const q4Pts = scalePtsByIndex(answers, 'overlookRedFlags', ['Almost always', 'Often', 'Sometimes', 'Rarely', 'Never'], [12, 8, 6, 3, 0]);
  const q5Pts = scalePtsByIndex(answers, 'financialConfidenceDating', ['Not at all', 'Slightly', 'Moderately', 'Quite a bit', 'Significantly'], [12, 9, 6, 3, 0]);
  const q6Pts = pts(answers, 'financialIncompatibilityTension', q6);
  const q7Pts = pts(answers, 'commitmentConcerns', q7);
  const q8Pts = scalePtsByIndex(answers, 'friendsInfluenceDating', ['Barely at all', 'Slightly', 'Somewhat', 'A fair amount', 'Significantly'], [8, 6, 4, 2, 0]);
  const q9Pts = scalePtsByIndex(answers, 'honestAboutFinances', ['Not at all honest', 'Somewhat guarded', 'Neutral', 'Fairly open', 'Completely open'], [0, 2, 4, 6, 7]);
  const total = q1Pts + q2Pts + q3Pts + q4Pts + q5Pts + q6Pts + q7Pts + q8Pts + q9Pts;

  const score = clamp(total);

  let risk_level: string;
  if (score <= 25) risk_level = 'Not Ready';
  else if (score <= 50) risk_level = 'Warming Up';
  else if (score <= 75) risk_level = 'Mostly Ready';
  else risk_level = 'Fully Ready';

  const recommendations = [
    'Be authentic and genuine in your interactions',
    'Focus on building meaningful connections',
    'Work on your communication skills',
    'Take care of your physical and mental health'
  ];

  const awarenessPts = q3Pts + q9Pts;
  const actionPts = total - awarenessPts;
  const subscores = {
    awareness: clamp((awarenessPts / 22) * 100),
    action: clamp((actionPts / 78) * 100)
  };
  return { score, risk_level, recommendations, subscores };
}

// --- LAYOFF RISK (lower score = higher risk) ---
function scoreLayoffRisk(answers: Record<string, unknown>): ScoringResult {
  const proactiveOptions = [
    'Updated my resume',
    'Expanded my professional network',
    'Learned a new in-demand skill',
    'Had a direct conversation with my manager',
    'Built visibility with leadership'
  ];
  const q3: Record<string, number> = {
    "No, I've only received positive signals": 15,
    "I'm not sure": 9,
    "I don't have those kinds of conversations": 7,
    'Yes, subtly or indirectly': 4,
    'Yes, explicitly': 0
  };
  const q4: Record<string, number> = {
    "Strong, I'm well-known and valued": 12,
    'Good, they know who I am': 9,
    'Neutral, they know my name': 5,
    "I don't know": 3,
    'Weak, I\'m mostly invisible to leadership': 0
  };
  const q6: Record<string, number> = {
    "I'd be fine - I have savings": 15,
    "I'd manage but it would be tight": 11,
    'I\'d struggle significantly': 6,
    "I'd be in serious financial trouble within weeks": 2,
    "I haven't thought about it": 5
  };
  const q7: Record<string, number> = {
    'Yes, very transparently': 12,
    'Generally yes': 9,
    "It's inconsistent": 5,
    'Rarely': 2,
    "Never - we're usually the last to know": 0
  };
  const q8: Record<string, number> = {
    'Frequently': 12,
    'A few times': 8,
    'Once': 4,
    'Never that I know of': 2,
    "I wouldn't be told": 0
  };
  const q9: Record<string, number> = {
    'Less than a month': 10,
    '1-3 months': 8,
    '3-6 months': 5,
    '6-12 months': 2,
    'More than a year': 0
  };

  let q5Pts = 0;
  const steps: string[] = Array.isArray(answers['stepsToReduceLayoffRisk']) ? (answers['stepsToReduceLayoffRisk'] as string[]) : [];
  if (steps.includes("No, I haven't done any of these")) {
    q5Pts = 0;
  } else {
    const count = steps.filter((s) => proactiveOptions.includes(s)).length;
    q5Pts = Math.min(12, Math.round(count * 2.4));
  }

  const q1Pts = scalePtsByIndex(answers, 'confidentSurviveCut', ['Not confident at all', 'Slightly confident', 'Somewhat confident', 'Fairly confident', 'Very confident'], [0, 4, 8, 12, 15]);
  const q2Pts = scalePtsByIndex(answers, 'replaceableInstitutionalKnowledge', [
    'Anyone could do my job quickly',
    'It would take some ramp-up',
    "I'd be hard to replace in the short term",
    "I'm very difficult to replace",
    'Irreplaceable in my current context'
  ], [0, 4, 8, 12, 15]);
  const q3Pts = pts(answers, 'trustedColleagueJobSecurityConcerns', q3);
  const q4Pts = pts(answers, 'relationshipWithDecisionMakers', q4);
  const q6Pts = pts(answers, 'incomeExpensesThreeMonths', q6);
  const q7Pts = pts(answers, 'leadershipCommunicateFinancialPressure', q7);
  const q8Pts = pts(answers, 'roleMentionedInRestructuring', q8);
  const q9Pts = pts(answers, 'jobSearchDurationIfLaidOff', q9);
  const total = q1Pts + q2Pts + q3Pts + q4Pts + q5Pts + q6Pts + q7Pts + q8Pts + q9Pts;

  const score = clamp(total);

  let risk_level: string;
  if (score <= 25) risk_level = 'High Risk';
  else if (score <= 50) risk_level = 'Elevated Risk';
  else if (score <= 75) risk_level = 'Moderate Risk';
  else risk_level = 'Low Risk';

  const recommendations = [
    'Build strong relationships with key stakeholders',
    'Develop skills that are in high demand',
    'Create a personal brand and online presence',
    'Have a backup plan and emergency fund'
  ];

  const awarenessPts = q1Pts + q2Pts + q4Pts + q6Pts + q7Pts + q8Pts + q9Pts;
  const actionPts = q3Pts + q5Pts;
  const subscores = {
    awareness: clamp((awarenessPts / 91) * 100),
    action: clamp((actionPts / 27) * 100)
  };
  return { score, risk_level, recommendations, subscores };
}

// --- VEHICLE FINANCIAL HEALTH (no full spec in image; use simple weighted average) ---
function scoreVehicleFinancialHealth(answers: Record<string, unknown>): ScoringResult {
  const singleOptScores: Record<string, Record<string, number>> = {
    researchTotalCostOfOwnership: {
      'Yes, thoroughly': 100,
      'Yes, but only partially': 75,
      'I mainly focused on the monthly payment': 40,
      "No, I didn't think about it that way": 15,
      "I don't own a vehicle": 50
    },
    twoThousandRepairTomorrow: {
      'Pay cash from savings': 100,
      'Put it on a credit card': 50,
      'Finance it somehow': 35,
      "I'd have to delay the repair": 15,
      "I'm not sure": 25,
      "I don't own a vehicle": 50
    },
    unexpectedRepairsPastYear: {
      'Nothing': 100,
      'Under $500': 80,
      '$500-$1,500': 55,
      '$1,500-$3,000': 30,
      'Over $3,000': 10,
      "I don't track this": 20,
      "I don't own a vehicle": 50
    },
    expenseMostUnderestimate: {
      'I account for all of them': 100,
      'Insurance': 60,
      'Fuel': 60,
      'Routine maintenance': 60,
      'Unexpected repairs': 50,
      'Depreciation': 55,
      'Registration and taxes': 60,
      "I don't own a vehicle": 50
    },
    vehicleFinancialOrLifestyle: {
      'Purely financial - it gets me where I need to go': 100,
      'Mostly financial with some preference': 85,
      'An equal mix of both': 60,
      'Mostly about image or lifestyle': 35,
      'Primarily about image or lifestyle': 15,
      "I don't own a vehicle": 50
    },
    stayedLongerThanShouldHave: {
      'No, I\'ve always made good calls': 100,
      'Not applicable': 70,
      'Possibly, I\'m not sure': 40,
      "Yes, that's happened to me": 20,
      "I don't own a vehicle": 50
    },
    breakdownAffectIncome: {
      'No impact - I work remotely or have other options': 100,
      'Minimal impact': 85,
      'Moderate disruption': 55,
      'It would significantly disrupt my work': 25,
      "I'd lose my job or income immediately": 0,
      "I don't own a vehicle": 50
    },
    marketValueAndUnderwater: {
      'Yes, I know both and I\'m in good shape': 100,
      'I have a general idea': 60,
      "No, I haven't looked": 25,
      'Yes, and I owe more than it\'s worth (underwater)': 15,
      "I don't own a vehicle": 50
    },
    betterVehicleDecisionNextTime: {
      "I'm already making good decisions": 100,
      'A clear budget before I shop': 85,
      'Knowledge of total cost, not just payments': 85,
      'More emergency savings going in': 75,
      'A plan for my current vehicle before buying': 70,
      'Less pressure from salespeople or circumstances': 60,
      "I don't plan to buy another vehicle": 50
    }
  };

  const awarenessIds = ['researchTotalCostOfOwnership', 'expenseMostUnderestimate', 'marketValueAndUnderwater'];
  let sum = 0;
  let count = 0;
  let awarenessSum = 0;
  let awarenessCount = 0;
  let actionSum = 0;
  let actionCount = 0;
  for (const [id, map] of Object.entries(singleOptScores)) {
    const v = answers[id];
    if (v !== undefined && v !== null) {
      const p = map[String(v).trim()];
      if (p !== undefined) {
        sum += p;
        count++;
        if (awarenessIds.includes(id)) {
          awarenessSum += p;
          awarenessCount++;
        } else {
          actionSum += p;
          actionCount++;
        }
      }
    }
  }
  const score = count > 0 ? clamp(sum / count) : 50;

  let risk_level: string;
  if (score >= 76) risk_level = 'Low Risk';
  else if (score >= 51) risk_level = 'Moderate Risk';
  else if (score >= 26) risk_level = 'Elevated Risk';
  else risk_level = 'High Risk';

  const recommendations = [
    'Create a dedicated vehicle emergency fund',
    'Track all vehicle-related expenses monthly',
    'Research and compare insurance options regularly',
    'Plan ahead for your next vehicle purchase'
  ];

  const subscores = {
    awareness: awarenessCount > 0 ? clamp(awarenessSum / awarenessCount) : 50,
    action: actionCount > 0 ? clamp(actionSum / actionCount) : 50
  };
  return { score, risk_level, recommendations, subscores };
}

// --- Public API ---
export type AssessmentType = 'ai-risk' | 'income-comparison' | 'cuffing-season' | 'layoff-risk' | 'vehicle-financial-health';

export function calculateAssessmentScore(
  assessmentType: AssessmentType,
  answers: Record<string, unknown>
): ScoringResult {
  switch (assessmentType) {
    case 'ai-risk':
      return scoreAiRisk(answers);
    case 'income-comparison':
      return scoreIncomeComparison(answers);
    case 'cuffing-season':
      return scoreCuffingSeason(answers);
    case 'layoff-risk':
      return scoreLayoffRisk(answers);
    case 'vehicle-financial-health':
      return scoreVehicleFinancialHealth(answers);
    default:
      return {
        score: 50,
        risk_level: 'Moderate',
        recommendations: []
      };
  }
}
