import {
  buildTimelineProjectionData,
  getGoalReachedYear,
  getPathColor,
  getPathSavingsAtYear,
  progressToGoal,
  resolveGoalThreshold,
} from './timelineProjectionUtils.js';

const paths = [
  {
    pathId: 'career_advancement',
    title: 'Career Advancement',
    monthlyBoost: 1500,
    feasibility: 'Medium',
    projections: [
      { year: 1, cumulativeSavings: 43000, goalReached: false },
      { year: 2, cumulativeSavings: 61000, goalReached: false },
      { year: 3, cumulativeSavings: 79000, goalReached: false },
      { year: 4, cumulativeSavings: 97000, goalReached: true },
    ],
  },
  {
    pathId: 'side_income',
    title: 'Side Income',
    monthlyBoost: 1000,
    feasibility: 'High',
    projections: [
      { year: 1, cumulativeSavings: 37000, goalReached: false },
      { year: 2, cumulativeSavings: 49000, goalReached: false },
      { year: 3, cumulativeSavings: 61000, goalReached: false },
    ],
  },
  {
    pathId: 'combined',
    title: 'Combined Strategy',
    monthlyBoost: 2200,
    feasibility: 'Very High',
    mostRealistic: true,
    projections: [
      { year: 1, cumulativeSavings: 51400, goalReached: false },
      { year: 2, cumulativeSavings: 77800, goalReached: false },
      { year: 3, cumulativeSavings: 104200, goalReached: true },
    ],
  },
];

describe('timelineProjectionUtils', () => {
  it('resolves goal threshold from analysis', () => {
    expect(resolveGoalThreshold(
      null,
      { futureState: { savingsTarget: 80000 }, gaps: { savingsGap: 55000 } },
      25000,
    )).toBe(80000);
  });

  it('builds year-by-year chart rows including year zero', () => {
    const { chartData, goalThreshold, pathMeta } = buildTimelineProjectionData({
      goal: { timeline: 5 },
      paths,
      analysis: { futureState: { savingsTarget: 97000 } },
      currentSavings: 25000,
    });

    expect(chartData).toHaveLength(6);
    expect(chartData[0]).toMatchObject({
      year: 0,
      currentSavings: 25000,
      goalThreshold: 97000,
      career_advancement: 25000,
    });
    expect(chartData[3].combined).toBe(104200);
    expect(pathMeta).toHaveLength(3);
    expect(pathMeta[2].goalReachedYear).toBe(3);
  });

  it('colors paths by feasibility', () => {
    expect(getPathColor('Very High')).toBe('#059669');
    expect(getPathColor('Low')).toBe('#DC2626');
  });

  it('finds savings at year with carry-forward', () => {
    expect(getPathSavingsAtYear(paths[1], 0, 25000)).toBe(25000);
    expect(getPathSavingsAtYear(paths[1], 5, 25000)).toBe(61000);
  });

  it('calculates goal reached year', () => {
    expect(getGoalReachedYear(paths[0], 97000)).toBe(4);
    expect(getGoalReachedYear(paths[1], 97000)).toBeNull();
  });

  it('calculates progress percentage', () => {
    expect(progressToGoal(48500, 97000)).toBe(50);
    expect(progressToGoal(120000, 97000)).toBe(100);
  });
});
