import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface ExpenseData {
  housing: string;
  transportation: string;
  food: string;
  utilities: string;
  healthcare: string;
  entertainment: string;
  shopping: string;
  debt_payments: string;
  savings: string;
  other: string;
}

const ExpensesStep: React.FC = () => {
  const [formData, setFormData] = useState<ExpenseData>({
    housing: '',
    transportation: '',
    food: '',
    utilities: '',
    healthcare: '',
    entertainment: '',
    shopping: '',
    debt_payments: '',
    savings: '',
    other: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const calculateTotal = () => {
    return Object.values(formData).reduce((total, value) => {
      return total + (parseFloat(value) || 0);
    }, 0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/onboarding/expenses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        navigate('/onboarding/financial-questionnaire');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to save expenses');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const expenseCategories = [
    { key: 'housing', label: 'Housing', icon: '🏠', description: 'Rent, mortgage, property taxes' },
    { key: 'transportation', label: 'Transportation', icon: '🚗', description: 'Car payment, gas, public transit' },
    { key: 'food', label: 'Food & Dining', icon: '🍽️', description: 'Groceries, restaurants, takeout' },
    { key: 'utilities', label: 'Utilities', icon: '⚡', description: 'Electricity, water, internet, phone' },
    { key: 'healthcare', label: 'Healthcare', icon: '🏥', description: 'Insurance, medical expenses' },
    { key: 'entertainment', label: 'Entertainment', icon: '🎬', description: 'Movies, streaming, hobbies' },
    { key: 'shopping', label: 'Shopping', icon: '🛍️', description: 'Clothing, personal care, household' },
    { key: 'debt_payments', label: 'Debt Payments', icon: '💳', description: 'Credit cards, loans' },
    { key: 'savings', label: 'Savings', icon: '💰', description: 'Emergency fund, investments' },
    { key: 'other', label: 'Other', icon: '📝', description: 'Miscellaneous expenses' },
  ];

  const totalExpenses = calculateTotal();

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-100 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Progress Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-900" className="text-4xl font-bold text-gray-900 mb-6">Monthly Expenses</h1>
            <span className="text-base leading-relaxed text-gray-500">Step 3 of 7</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-orange-500 to-red-600 h-2 rounded-full" style={{ width: '43%' }}></div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2" className="text-2xl font-semibold text-gray-800 mb-4">Track Your Monthly Expenses</h2>
            <p className="text-gray-600">Understanding your spending helps us provide better financial insights and recommendations.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600">{error}</p>
              </div>
            )}

            {/* Expense Categories */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {expenseCategories.map(category => (
                <div key={category.key} className="space-y-2">
                  <label className="block text-base leading-relaxed font-medium text-gray-700">
                    <span className="text-lg mr-2">{category.icon}</span>
                    {category.label}
                  </label>
                  <input
                    type="number"
                    name={category.key}
                    value={formData[category.key as keyof ExpenseData]}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    placeholder="0"
                    min="0"
                    step="0.01"
                  />
                  <p className="text-base leading-relaxed text-gray-500">{category.description}</p>
                </div>
              ))}
            </div>

            {/* Total Summary */}
            <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-6 border border-orange-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900" className="text-xl font-semibold text-gray-800 mb-3">Total Monthly Expenses</h3>
                <span className="text-2xl font-bold text-orange-600">
                  ${totalExpenses.toLocaleString()}
                </span>
              </div>
              <p className="text-base leading-relaxed text-gray-600 mt-2">
                This helps us understand your spending patterns and provide personalized recommendations.
              </p>
            </div>

            {/* Tips */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-800 mb-2">💡 Tips for accurate tracking:</h4>
              <ul className="text-base leading-relaxed text-blue-700 space-y-1">
                <li>• Include all regular monthly expenses</li>
                <li>• Don't forget annual expenses divided by 12</li>
                <li>• Be honest - this helps us provide better advice</li>
                <li>• You can always update these later</li>
              </ul>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between pt-6">
              <button
                type="button"
                onClick={() => navigate('/onboarding/preferences')}
                className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-8 py-2 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-lg hover:from-orange-700 hover:to-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Saving...' : 'Continue'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ExpensesStep; 