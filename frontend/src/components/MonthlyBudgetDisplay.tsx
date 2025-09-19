import React, { useState } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle,
  Fuel,
  Wrench,
  Shield,
  FileText,
  Plus,
  ChevronRight,
  PieChart
} from 'lucide-react';
import { VehicleBudget, VehicleExpense } from '../types/vehicle';

interface MonthlyBudgetDisplayProps {
  budgets: VehicleBudget[];
  recentExpenses: VehicleExpense[];
  loading?: boolean;
}

const MonthlyBudgetDisplay: React.FC<MonthlyBudgetDisplayProps> = ({ 
  budgets, 
  recentExpenses, 
  loading = false 
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState<string>('current');

  if (loading) {
    return <BudgetSkeleton />;
  }

  const currentBudget = budgets.find(b => b.budgetPeriod === getCurrentPeriod()) || budgets[0];
  const totalBudget = currentBudget?.monthlyBudget || 0;
  const totalSpent = currentBudget?.totalSpent || 0;
  const remainingBudget = currentBudget?.remainingBudget || 0;
  const budgetUtilization = totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0;

  const getBudgetStatus = (utilization: number) => {
    if (utilization >= 100) return { color: 'red', label: 'Over Budget', icon: AlertTriangle };
    if (utilization >= 80) return { color: 'orange', label: 'Near Limit', icon: AlertTriangle };
    if (utilization >= 60) return { color: 'yellow', label: 'Moderate', icon: TrendingUp };
    return { color: 'green', label: 'On Track', icon: TrendingDown };
  };

  const budgetStatus = getBudgetStatus(budgetUtilization);

  const getExpenseCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'fuel':
        return <Fuel className="h-4 w-4" />;
      case 'maintenance':
        return <Wrench className="h-4 w-4" />;
      case 'insurance':
        return <Shield className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getExpenseCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'fuel':
        return 'text-blue-600 bg-blue-100';
      case 'maintenance':
        return 'text-orange-600 bg-orange-100';
      case 'insurance':
        return 'text-purple-600 bg-purple-100';
      case 'repair':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Budget Overview */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-900">Monthly Budget</h4>
          <div className="flex items-center gap-2">
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              <option value="current">Current Month</option>
              <option value="last">Last Month</option>
              <option value="year">This Year</option>
            </select>
          </div>
        </div>

        {/* Budget Status Card */}
        <div className={`p-4 rounded-lg border ${
          budgetStatus.color === 'red' ? 'bg-red-50 border-red-200' :
          budgetStatus.color === 'orange' ? 'bg-orange-50 border-orange-200' :
          budgetStatus.color === 'yellow' ? 'bg-yellow-50 border-yellow-200' :
          'bg-green-50 border-green-200'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <budgetStatus.icon className={`h-5 w-5 ${
                budgetStatus.color === 'red' ? 'text-red-600' :
                budgetStatus.color === 'orange' ? 'text-orange-600' :
                budgetStatus.color === 'yellow' ? 'text-yellow-600' :
                'text-green-600'
              }`} />
              <span className={`font-medium ${
                budgetStatus.color === 'red' ? 'text-red-900' :
                budgetStatus.color === 'orange' ? 'text-orange-900' :
                budgetStatus.color === 'yellow' ? 'text-yellow-900' :
                'text-green-900'
              }`}>
                {budgetStatus.label}
              </span>
            </div>
            <span className={`text-sm font-bold ${
              budgetStatus.color === 'red' ? 'text-red-700' :
              budgetStatus.color === 'orange' ? 'text-orange-700' :
              budgetStatus.color === 'yellow' ? 'text-yellow-700' :
              'text-green-700'
            }`}>
              {budgetUtilization.toFixed(1)}%
            </span>
          </div>

          {/* Budget Progress Bar */}
          <div className="mb-3">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Spent: ${totalSpent.toLocaleString()}</span>
              <span>Budget: ${totalBudget.toLocaleString()}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  budgetStatus.color === 'red' ? 'bg-red-500' :
                  budgetStatus.color === 'orange' ? 'bg-orange-500' :
                  budgetStatus.color === 'yellow' ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(budgetUtilization, 100)}%` }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">
              Remaining: ${remainingBudget.toLocaleString()}
            </span>
            {budgetUtilization > 100 && (
              <span className="text-red-600 font-medium">
                Over by ${Math.abs(remainingBudget).toLocaleString()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Budget Breakdown */}
      <div className="mb-6">
        <h5 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <PieChart className="h-4 w-4" />
          Budget Breakdown
        </h5>
        <div className="grid grid-cols-2 gap-3">
          <BudgetCategoryCard
            title="Fuel"
            budget={currentBudget?.fuelBudget || 0}
            spent={getCategorySpent(recentExpenses, 'fuel')}
            icon={<Fuel className="h-4 w-4" />}
            color="blue"
          />
          <BudgetCategoryCard
            title="Maintenance"
            budget={currentBudget?.maintenanceBudget || 0}
            spent={getCategorySpent(recentExpenses, 'maintenance')}
            icon={<Wrench className="h-4 w-4" />}
            color="orange"
          />
          <BudgetCategoryCard
            title="Insurance"
            budget={currentBudget?.insuranceBudget || 0}
            spent={getCategorySpent(recentExpenses, 'insurance')}
            icon={<Shield className="h-4 w-4" />}
            color="purple"
          />
          <BudgetCategoryCard
            title="Other"
            budget={totalBudget - (currentBudget?.fuelBudget || 0) - (currentBudget?.maintenanceBudget || 0) - (currentBudget?.insuranceBudget || 0)}
            spent={getCategorySpent(recentExpenses, 'other')}
            icon={<FileText className="h-4 w-4" />}
            color="gray"
          />
        </div>
      </div>

      {/* Recent Expenses */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h5 className="font-semibold text-gray-900">Recent Expenses</h5>
          <button className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
            View All
            <ChevronRight className="h-3 w-3" />
          </button>
        </div>
        
        <div className="space-y-2">
          {recentExpenses.length === 0 ? (
            <div className="text-center py-4">
              <DollarSign className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600 text-sm">No expenses recorded yet</p>
            </div>
          ) : (
            recentExpenses.slice(0, 5).map((expense) => (
              <ExpenseItem key={expense.id} expense={expense} />
            ))
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex gap-2">
          <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors text-sm flex items-center justify-center gap-2">
            <Plus className="h-4 w-4" />
            Add Expense
          </button>
          <button className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-4 rounded-lg font-medium transition-colors text-sm">
            Set Budget
          </button>
        </div>
      </div>
    </div>
  );
};

// Budget Category Card Component
const BudgetCategoryCard: React.FC<{
  title: string;
  budget: number;
  spent: number;
  icon: React.ReactNode;
  color: 'blue' | 'orange' | 'purple' | 'gray';
}> = ({ title, budget, spent, icon, color }) => {
  const utilization = budget > 0 ? (spent / budget) * 100 : 0;
  
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-100',
    orange: 'text-orange-600 bg-orange-100',
    purple: 'text-purple-600 bg-purple-100',
    gray: 'text-gray-600 bg-gray-100'
  };

  return (
    <div className="p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`p-1 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </div>
          <span className="text-sm font-medium text-gray-900">{title}</span>
        </div>
        <span className="text-sm font-bold text-gray-900">
          ${spent.toLocaleString()}
        </span>
      </div>
      <div className="text-xs text-gray-600 mb-1">
        ${spent.toLocaleString()} of ${budget.toLocaleString()}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-1.5">
        <div 
          className={`h-1.5 rounded-full ${
            color === 'blue' ? 'bg-blue-500' :
            color === 'orange' ? 'bg-orange-500' :
            color === 'purple' ? 'bg-purple-500' :
            'bg-gray-500'
          }`}
          style={{ width: `${Math.min(utilization, 100)}%` }}
        />
      </div>
    </div>
  );
};

// Expense Item Component
const ExpenseItem: React.FC<{ expense: VehicleExpense }> = ({ expense }) => {
  const getExpenseCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'fuel':
        return 'text-blue-600 bg-blue-100';
      case 'maintenance':
        return 'text-orange-600 bg-orange-100';
      case 'insurance':
        return 'text-purple-600 bg-purple-100';
      case 'repair':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getExpenseCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'fuel':
        return <Fuel className="h-3 w-3" />;
      case 'maintenance':
        return <Wrench className="h-3 w-3" />;
      case 'insurance':
        return <Shield className="h-3 w-3" />;
      default:
        return <FileText className="h-3 w-3" />;
    }
  };

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
      <div className="flex items-center gap-3">
        <div className={`p-1.5 rounded-lg ${getExpenseCategoryColor(expense.category)}`}>
          {getExpenseCategoryIcon(expense.category)}
        </div>
        <div>
          <h6 className="font-medium text-gray-900 text-sm">{expense.description}</h6>
          <p className="text-xs text-gray-600">{new Date(expense.date).toLocaleDateString()}</p>
        </div>
      </div>
      <div className="text-right">
        <span className="font-semibold text-gray-900">${expense.amount.toLocaleString()}</span>
        <p className="text-xs text-gray-600 capitalize">{expense.category}</p>
      </div>
    </div>
  );
};

// Helper Functions
const getCurrentPeriod = (): string => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
};

const getCategorySpent = (expenses: VehicleExpense[], category: string): number => {
  return expenses
    .filter(expense => expense.category.toLowerCase() === category.toLowerCase())
    .reduce((total, expense) => total + expense.amount, 0);
};

// Loading Skeleton
const BudgetSkeleton: React.FC = () => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="h-5 w-24 bg-gray-200 rounded animate-pulse" />
        <div className="h-8 w-32 bg-gray-200 rounded-lg animate-pulse" />
      </div>
      
      <div className="p-4 bg-gray-50 rounded-lg mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="h-5 w-20 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-12 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="h-2 w-full bg-gray-200 rounded-full animate-pulse mb-3" />
        <div className="flex items-center justify-between">
          <div className="h-3 w-24 bg-gray-200 rounded animate-pulse" />
          <div className="h-3 w-16 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
      
      <div className="mb-6">
        <div className="h-5 w-32 bg-gray-200 rounded animate-pulse mb-3" />
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
                  <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
                </div>
                <div className="h-4 w-12 bg-gray-200 rounded animate-pulse" />
              </div>
              <div className="h-3 w-20 bg-gray-200 rounded animate-pulse mb-1" />
              <div className="h-1.5 w-full bg-gray-200 rounded-full animate-pulse" />
            </div>
          ))}
        </div>
      </div>
      
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="h-5 w-24 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 bg-gray-200 rounded-lg animate-pulse" />
                <div className="space-y-1">
                  <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                  <div className="h-3 w-16 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
              <div className="h-4 w-12 bg-gray-200 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MonthlyBudgetDisplay;
