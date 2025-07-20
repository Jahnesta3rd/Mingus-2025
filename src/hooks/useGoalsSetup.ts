import { useState, useEffect, useCallback } from 'react';
import { Goal, GoalType, UserFinances, GoalSuggestion } from '../types/goals';

export const useGoalsSetup = () => {
  const [selectedGoals, setSelectedGoals] = useState<GoalType[]>([]);
  const [currentGoalIndex, setCurrentGoalIndex] = useState(0);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [userFinances, setUserFinances] = useState<UserFinances | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load user finances from previous onboarding steps
  const loadUserFinances = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // In a real app, this would fetch from your API
      // For now, we'll simulate with mock data
      const mockFinances: UserFinances = {
        monthlyIncome: 5000,
        monthlyExpenses: 3000,
        currentSavings: 5000,
        debtPayments: 500
      };
      
      setUserFinances(mockFinances);
    } catch (err) {
      setError('Failed to load financial data');
      console.error('Error loading finances:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Toggle goal selection
  const toggleGoalSelection = useCallback((goalType: GoalType) => {
    setSelectedGoals(prev => {
      if (prev.includes(goalType)) {
        return prev.filter(type => type !== goalType);
      } else {
        return [...prev, goalType];
      }
    });
  }, []);

  // Add a new goal
  const addGoal = useCallback((goal: Goal) => {
    setGoals(prev => [...prev, goal]);
  }, []);

  // Update an existing goal
  const updateGoal = useCallback((goalId: string, updates: Partial<Goal>) => {
    setGoals(prev => 
      prev.map(goal => 
        goal.id === goalId ? { ...goal, ...updates } : goal
      )
    );
  }, []);

  // Remove a goal
  const removeGoal = useCallback((goalId: string) => {
    setGoals(prev => prev.filter(goal => goal.id !== goalId));
  }, []);

  // Save goals to backend
  const saveGoals = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // In a real app, this would save to your API
      console.log('Saving goals:', goals);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // You could also save to localStorage as backup
      localStorage.setItem('mingus_goals', JSON.stringify(goals));
      
    } catch (err) {
      setError('Failed to save goals');
      console.error('Error saving goals:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [goals]);

  // Load saved goals from localStorage (backup)
  const loadSavedGoals = useCallback(() => {
    try {
      const saved = localStorage.getItem('mingus_goals');
      if (saved) {
        const parsedGoals = JSON.parse(saved);
        setGoals(parsedGoals);
      }
    } catch (err) {
      console.error('Error loading saved goals:', err);
    }
  }, []);

  // Calculate monthly contribution for a goal
  const calculateMonthlyContribution = useCallback((goal: Goal) => {
    if (!goal.targetAmount || !goal.targetDate) return 0;
    
    const monthsRemaining = Math.max(1, 
      (new Date(goal.targetDate).getTime() - new Date().getTime()) / 
      (1000 * 60 * 60 * 24 * 30.44)
    );
    
    return Math.ceil((goal.targetAmount - (goal.currentAmount || 0)) / monthsRemaining);
  }, []);

  // Analyze goal feasibility
  const analyzeFeasibility = useCallback((goal: Goal) => {
    if (!userFinances) return null;
    
    const monthlyContribution = calculateMonthlyContribution(goal);
    const availableIncome = userFinances.monthlyIncome - userFinances.monthlyExpenses - userFinances.debtPayments;
    const feasibilityScore = monthlyContribution / availableIncome;
    
    return {
      score: feasibilityScore,
      isFeasible: feasibilityScore <= 0.8,
      monthlyContribution,
      availableIncome
    };
  }, [userFinances, calculateMonthlyContribution]);

  // Generate goal suggestions based on user finances
  const generateSuggestions = useCallback((goalType: GoalType): GoalSuggestion[] => {
    if (!userFinances) return [];
    
    const suggestions: GoalSuggestion[] = [];
    const { monthlyIncome, monthlyExpenses } = userFinances;
    
    switch (goalType) {
      case 'emergency_fund':
        const emergencyFund = monthlyExpenses * 6;
        suggestions.push(
          { amount: emergencyFund, reasoning: '6 months of expenses (recommended)' },
          { amount: emergencyFund * 0.75, reasoning: '4.5 months of expenses' },
          { amount: emergencyFund * 0.5, reasoning: '3 months of expenses (minimum)' }
        );
        break;
      case 'home_purchase':
        const downPayment = monthlyIncome * 24; // 2 years of income
        suggestions.push(
          { amount: downPayment, reasoning: '20% down payment' },
          { amount: downPayment * 0.6, reasoning: '12% down payment (FHA)' },
          { amount: downPayment * 0.4, reasoning: '8% down payment (minimum)' }
        );
        break;
      default:
        suggestions.push(
          { amount: monthlyIncome * 6, reasoning: 'Conservative goal' },
          { amount: monthlyIncome * 12, reasoning: 'Moderate goal' },
          { amount: monthlyIncome * 24, reasoning: 'Ambitious goal' }
        );
    }
    
    return suggestions;
  }, [userFinances]);

  // Initialize on mount
  useEffect(() => {
    loadUserFinances();
    loadSavedGoals();
  }, [loadUserFinances, loadSavedGoals]);

  return {
    selectedGoals,
    currentGoalIndex,
    goals,
    userFinances,
    isLoading,
    error,
    toggleGoalSelection,
    addGoal,
    updateGoal,
    removeGoal,
    saveGoals,
    loadUserFinances,
    calculateMonthlyContribution,
    analyzeFeasibility,
    generateSuggestions,
    setCurrentGoalIndex
  };
}; 