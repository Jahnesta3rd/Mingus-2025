import React from 'react';
import { GoalType, GoalSuggestion } from '../../types/goals';

interface SmartSuggestionsProps {
  userIncome: number;
  userExpenses: number;
  goalType: GoalType;
  onApplyAmount: (amount: number) => void;
}

const SmartSuggestions: React.FC<SmartSuggestionsProps> = ({
  userIncome,
  userExpenses,
  goalType,
  onApplyAmount
}) => {
  const generateGoalSuggestions = (): GoalSuggestion[] => {
    const availableIncome = userIncome - userExpenses;
    const monthlySavings = availableIncome * 0.3; // 30% of available income
    
    const suggestions: GoalSuggestion[] = [];
    
    // Base suggestions for different goal types
    switch (goalType) {
      case 'emergency_fund':
        const emergencyFund = userExpenses * 6; // 6 months of expenses
        suggestions.push(
          { amount: emergencyFund, reasoning: '6 months of expenses (recommended)' },
          { amount: emergencyFund * 0.75, reasoning: '4.5 months of expenses' },
          { amount: emergencyFund * 0.5, reasoning: '3 months of expenses (minimum)' }
        );
        break;
        
      case 'home_purchase':
        const downPayment = userIncome * 2; // 2 years of income for down payment
        suggestions.push(
          { amount: downPayment, reasoning: '20% down payment (conventional loan)' },
          { amount: downPayment * 0.6, reasoning: '12% down payment (FHA loan)' },
          { amount: downPayment * 0.4, reasoning: '8% down payment (minimum)' }
        );
        break;
        
      case 'wedding_fund':
        const weddingCost = userIncome * 1.5; // 1.5 years of income
        suggestions.push(
          { amount: weddingCost, reasoning: 'Average wedding cost' },
          { amount: weddingCost * 0.7, reasoning: 'Modest wedding budget' },
          { amount: weddingCost * 0.4, reasoning: 'Intimate celebration' }
        );
        break;
        
      case 'vacation_fund':
        const vacationCost = userIncome * 0.3; // 3.6 months of income
        suggestions.push(
          { amount: vacationCost, reasoning: 'International trip budget' },
          { amount: vacationCost * 0.6, reasoning: 'Domestic vacation' },
          { amount: vacationCost * 0.3, reasoning: 'Weekend getaway' }
        );
        break;
        
      case 'car_purchase':
        const carCost = userIncome * 0.8; // 9.6 months of income
        suggestions.push(
          { amount: carCost, reasoning: 'New car down payment' },
          { amount: carCost * 0.6, reasoning: 'Used car purchase' },
          { amount: carCost * 0.3, reasoning: 'Reliable used car' }
        );
        break;
        
      case 'education_fund':
        const educationCost = userIncome * 2; // 2 years of income
        suggestions.push(
          { amount: educationCost, reasoning: 'Graduate degree program' },
          { amount: educationCost * 0.5, reasoning: 'Certification program' },
          { amount: educationCost * 0.2, reasoning: 'Skill development courses' }
        );
        break;
        
      case 'child_fund':
        const childCost = userIncome * 1.2; // 1.2 years of income
        suggestions.push(
          { amount: childCost, reasoning: 'Childcare and education fund' },
          { amount: childCost * 0.7, reasoning: 'Childcare expenses' },
          { amount: childCost * 0.4, reasoning: 'Basic child expenses' }
        );
        break;
        
      case 'side_business':
        const businessCost = userIncome * 0.5; // 6 months of income
        suggestions.push(
          { amount: businessCost, reasoning: 'Startup capital' },
          { amount: businessCost * 0.6, reasoning: 'Equipment and marketing' },
          { amount: businessCost * 0.3, reasoning: 'Basic startup costs' }
        );
        break;
        
      case 'debt_payoff':
        const debtAmount = userIncome * 0.8; // 9.6 months of income
        suggestions.push(
          { amount: debtAmount, reasoning: 'Credit card debt payoff' },
          { amount: debtAmount * 0.7, reasoning: 'Student loan payoff' },
          { amount: debtAmount * 0.5, reasoning: 'Personal loan payoff' }
        );
        break;
        
      case 'retirement_savings':
        const retirementTarget = userIncome * 10; // 10 years of income
        suggestions.push(
          { amount: retirementTarget, reasoning: 'Long-term retirement goal' },
          { amount: retirementTarget * 0.5, reasoning: 'Mid-term retirement savings' },
          { amount: retirementTarget * 0.2, reasoning: 'Initial retirement fund' }
        );
        break;
        
      case 'investment_portfolio':
        const investmentAmount = userIncome * 2; // 2 years of income
        suggestions.push(
          { amount: investmentAmount, reasoning: 'Diversified portfolio start' },
          { amount: investmentAmount * 0.6, reasoning: 'Stock investment fund' },
          { amount: investmentAmount * 0.3, reasoning: 'Initial investment' }
        );
        break;
        
      default:
        // Generic suggestions based on income
        suggestions.push(
          { amount: userIncome * 0.5, reasoning: 'Conservative goal (6 months income)' },
          { amount: userIncome, reasoning: 'Moderate goal (1 year income)' },
          { amount: userIncome * 2, reasoning: 'Ambitious goal (2 years income)' }
        );
    }
    
    return suggestions.slice(0, 3); // Return top 3 suggestions
  };

  const suggestions = generateGoalSuggestions();

  return (
    <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
      <h4 className="text-lg font-semibold text-blue-900 mb-3 flex items-center">
        <span className="text-2xl mr-2">💡</span>
        Based on your income, consider:
      </h4>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onApplyAmount(suggestion.amount)}
            className="text-left p-4 bg-white rounded-lg border border-blue-200 hover:border-blue-300 hover:shadow-md transition-all duration-200"
          >
            <div className="text-xl font-bold text-blue-600 mb-1">
              ${Math.round(suggestion.amount).toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">
              {suggestion.reasoning}
            </div>
          </button>
        ))}
      </div>
      
      <div className="mt-4 text-xs text-blue-700">
        💡 These suggestions are based on your income of ${userIncome.toLocaleString()}/month and typical financial planning guidelines.
      </div>
    </div>
  );
};

export default SmartSuggestions; 