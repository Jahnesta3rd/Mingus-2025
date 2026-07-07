import { buildGoalFormPrefill } from './useGoalFormPrefill';

describe('buildGoalFormPrefill', () => {
  it('maps home purchase intent and housing data to defaults', () => {
    const result = buildGoalFormPrefill({
      goal_intent: { goal_intent: 'home_purchase', interested: true },
      housing: {
        has_buy_goal: true,
        target_price: 450000,
        target_timeline_months: 36,
        down_payment_saved: 30000,
      },
    });

    expect(result.hasGoalInterest).toBe(true);
    expect(result.suggestedGoalType).toBe('home_purchase');
    expect(result.defaultValues).toEqual({
      type: 'home_purchase',
      parameters: {
        homePrice: 450000,
        savedAmount: 30000,
      },
      timeline: 3,
    });
    expect(result.prefilledFields).toEqual(
      expect.arrayContaining(['homePrice', 'savedAmount', 'timeline']),
    );
  });

  it('detects baby milestone events', () => {
    const result = buildGoalFormPrefill({
      milestones: {
        events: [{ category: 'expecting', estimated_cost: 12000 }],
      },
    });

    expect(result.recentBabyEvent).toBe(true);
    expect(result.suggestedGoalType).toBe('baby');
    expect(result.defaultValues?.parameters.preparationCost).toBe(12000);
  });

  it('returns no goal interest when user prefers not to say', () => {
    const result = buildGoalFormPrefill({
      goal_intent: { goal_intent: 'prefer_not_to_say', interested: false },
    });

    expect(result.hasGoalInterest).toBe(false);
    expect(result.defaultValues).toBeNull();
  });
});
