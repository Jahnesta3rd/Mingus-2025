export interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  category: 'profile' | 'accounts' | 'notifications' | 'community' | 'goals' | 'insights';
  priority: 'high' | 'medium' | 'low';
  completed: boolean;
  completedAt?: string;
  action?: {
    type: 'navigate' | 'modal' | 'external';
    target: string;
    text: string;
  };
  estimatedTime?: number; // in minutes
  dependencies?: string[]; // IDs of items that must be completed first
  userSpecific?: boolean; // Whether this item is personalized for the user
}

export interface ChecklistProgress {
  totalItems: number;
  completedItems: number;
  progressPercentage: number;
  estimatedTimeRemaining: number;
  nextPriorityItem?: ChecklistItem;
  categories: {
    [key: string]: {
      total: number;
      completed: number;
      percentage: number;
    };
  };
}

export class ChecklistService {
  private static instance: ChecklistService;

  static getInstance(): ChecklistService {
    if (!ChecklistService.instance) {
      ChecklistService.instance = new ChecklistService();
    }
    return ChecklistService.instance;
  }

  async generatePersonalizedChecklist(userId: string): Promise<ChecklistItem[]> {
    try {
      // In a real app, this would fetch user data and generate personalized items
      // For now, we'll return a sample checklist that can be customized
      const baseItems = this.getBaseChecklistItems();
      const personalizedItems = await this.addPersonalizedItems(userId, baseItems);
      
      return personalizedItems;
    } catch (error) {
      console.error('Error generating personalized checklist:', error);
      return this.getBaseChecklistItems();
    }
  }

  private getBaseChecklistItems(): ChecklistItem[] {
    return [
      {
        id: 'complete-profile',
        title: 'Complete Your Profile',
        description: 'Add your employment details, income sources, and financial goals for personalized insights.',
        category: 'profile',
        priority: 'high',
        completed: false,
        action: {
          type: 'navigate',
          target: '/profile',
          text: 'Complete Profile'
        },
        estimatedTime: 5,
        userSpecific: false
      },
      {
        id: 'connect-bank',
        title: 'Connect Your Bank Account',
        description: 'Link your primary bank account for automatic expense tracking and cash flow analysis.',
        category: 'accounts',
        priority: 'high',
        completed: false,
        action: {
          type: 'modal',
          target: 'connect-accounts',
          text: 'Connect Account'
        },
        estimatedTime: 3,
        userSpecific: false
      },
      {
        id: 'setup-notifications',
        title: 'Set Up Notifications',
        description: 'Choose your preferred notification settings to stay updated on your progress and insights.',
        category: 'notifications',
        priority: 'medium',
        completed: false,
        action: {
          type: 'modal',
          target: 'notification-settings',
          text: 'Set Up Notifications'
        },
        estimatedTime: 2,
        userSpecific: false
      },
      {
        id: 'join-community',
        title: 'Join Community Event',
        description: 'Connect with others on similar financial journeys. Share experiences and get support.',
        category: 'community',
        priority: 'medium',
        completed: false,
        action: {
          type: 'navigate',
          target: '/community',
          text: 'Join Event'
        },
        estimatedTime: 10,
        userSpecific: true
      },
      {
        id: 'set-emergency-goal',
        title: 'Set Emergency Fund Goal',
        description: 'Define your emergency fund target based on your job security and monthly expenses.',
        category: 'goals',
        priority: 'high',
        completed: false,
        dependencies: ['complete-profile'],
        action: {
          type: 'navigate',
          target: '/goals',
          text: 'Set Goal'
        },
        estimatedTime: 3,
        userSpecific: true
      },
      {
        id: 'review-insights',
        title: 'Review Your Insights',
        description: 'Check out your personalized financial insights and recommendations.',
        category: 'insights',
        priority: 'low',
        completed: false,
        dependencies: ['complete-profile'],
        action: {
          type: 'navigate',
          target: '/insights',
          text: 'View Insights'
        },
        estimatedTime: 5,
        userSpecific: true
      },
      {
        id: 'connect-additional-accounts',
        title: 'Connect Additional Accounts',
        description: 'Link your investment accounts, credit cards, and other financial accounts for comprehensive tracking.',
        category: 'accounts',
        priority: 'medium',
        completed: false,
        dependencies: ['connect-bank'],
        action: {
          type: 'modal',
          target: 'connect-accounts',
          text: 'Add More Accounts'
        },
        estimatedTime: 5,
        userSpecific: true
      },
      {
        id: 'set-spending-goals',
        title: 'Set Spending Goals',
        description: 'Create monthly spending targets for different categories to improve your financial habits.',
        category: 'goals',
        priority: 'medium',
        completed: false,
        dependencies: ['connect-bank'],
        action: {
          type: 'navigate',
          target: '/goals/spending',
          text: 'Set Spending Goals'
        },
        estimatedTime: 4,
        userSpecific: true
      }
    ];
  }

  private async addPersonalizedItems(userId: string, baseItems: ChecklistItem[]): Promise<ChecklistItem[]> {
    try {
      // This would typically fetch user data and add personalized items
      // For now, we'll add some conditional items based on common scenarios
      
      const personalizedItems = [...baseItems];

      // Add job security specific items if user has job security concerns
      const hasJobSecurityConcerns = await this.checkJobSecurityConcerns(userId);
      if (hasJobSecurityConcerns) {
        personalizedItems.push({
          id: 'job-security-plan',
          title: 'Create Job Security Plan',
          description: 'Develop a plan to improve your job security and career stability.',
          category: 'goals',
          priority: 'high',
          completed: false,
          action: {
            type: 'navigate',
            target: '/job-security/plan',
            text: 'Create Plan'
          },
          estimatedTime: 8,
          userSpecific: true
        });
      }

      // Add debt management items if user has debt
      const hasDebt = await this.checkUserDebt(userId);
      if (hasDebt) {
        personalizedItems.push({
          id: 'debt-payoff-plan',
          title: 'Create Debt Payoff Plan',
          description: 'Develop a strategy to pay off your debts efficiently and save on interest.',
          category: 'goals',
          priority: 'high',
          completed: false,
          action: {
            type: 'navigate',
            target: '/debt/plan',
            text: 'Create Plan'
          },
          estimatedTime: 6,
          userSpecific: true
        });
      }

      // Add investment items if user has investment accounts
      const hasInvestments = await this.checkInvestmentAccounts(userId);
      if (hasInvestments) {
        personalizedItems.push({
          id: 'review-investments',
          title: 'Review Investment Portfolio',
          description: 'Analyze your investment portfolio and get personalized recommendations.',
          category: 'insights',
          priority: 'medium',
          completed: false,
          action: {
            type: 'navigate',
            target: '/investments/portfolio',
            text: 'Review Portfolio'
          },
          estimatedTime: 7,
          userSpecific: true
        });
      }

      return personalizedItems;
    } catch (error) {
      console.error('Error adding personalized items:', error);
      return baseItems;
    }
  }

  private async checkJobSecurityConcerns(userId: string): Promise<boolean> {
    // This would check user's job security assessment
    // For now, return a random value for demonstration
    return Math.random() > 0.5;
  }

  private async checkUserDebt(userId: string): Promise<boolean> {
    // This would check if user has debt accounts
    // For now, return a random value for demonstration
    return Math.random() > 0.3;
  }

  private async checkInvestmentAccounts(userId: string): Promise<boolean> {
    // This would check if user has investment accounts
    // For now, return a random value for demonstration
    return Math.random() > 0.4;
  }

  async getChecklistProgress(items: ChecklistItem[]): Promise<ChecklistProgress> {
    const totalItems = items.length;
    const completedItems = items.filter(item => item.completed).length;
    const progressPercentage = totalItems > 0 ? (completedItems / totalItems) * 100 : 0;

    // Calculate estimated time remaining
    const remainingItems = items.filter(item => !item.completed);
    const estimatedTimeRemaining = remainingItems.reduce((total, item) => {
      return total + (item.estimatedTime || 0);
    }, 0);

    // Find next priority item
    const nextPriorityItem = remainingItems
      .filter(item => this.canCompleteItem(item, items))
      .sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      })[0];

    // Calculate category progress
    const categories: { [key: string]: { total: number; completed: number; percentage: number } } = {};
    const categoryGroups = items.reduce((acc, item) => {
      if (!acc[item.category]) {
        acc[item.category] = [];
      }
      acc[item.category].push(item);
      return acc;
    }, {} as { [key: string]: ChecklistItem[] });

    Object.entries(categoryGroups).forEach(([category, categoryItems]) => {
      const total = categoryItems.length;
      const completed = categoryItems.filter(item => item.completed).length;
      const percentage = total > 0 ? (completed / total) * 100 : 0;

      categories[category] = { total, completed, percentage };
    });

    return {
      totalItems,
      completedItems,
      progressPercentage,
      estimatedTimeRemaining,
      nextPriorityItem,
      categories
    };
  }

  private canCompleteItem(item: ChecklistItem, allItems: ChecklistItem[]): boolean {
    if (!item.dependencies || item.dependencies.length === 0) {
      return true;
    }

    return item.dependencies.every(depId => {
      const dependency = allItems.find(item => item.id === depId);
      return dependency?.completed || false;
    });
  }

  async markItemComplete(itemId: string, items: ChecklistItem[]): Promise<ChecklistItem[]> {
    return items.map(item => {
      if (item.id === itemId) {
        return {
          ...item,
          completed: true,
          completedAt: new Date().toISOString()
        };
      }
      return item;
    });
  }

  async markItemIncomplete(itemId: string, items: ChecklistItem[]): Promise<ChecklistItem[]> {
    return items.map(item => {
      if (item.id === itemId) {
        const { completed, completedAt, ...rest } = item;
        return rest;
      }
      return item;
    });
  }

  getEncouragementMessage(progress: ChecklistProgress): string {
    if (progress.progressPercentage === 0) {
      return "Let's get started! Every journey begins with a single step. 💪";
    } else if (progress.progressPercentage < 25) {
      return "Great start! You're building momentum. Keep going! 🚀";
    } else if (progress.progressPercentage < 50) {
      return "You're making excellent progress! You're almost halfway there! ✨";
    } else if (progress.progressPercentage < 75) {
      return "Fantastic work! You're in the home stretch now! 🎯";
    } else if (progress.progressPercentage < 100) {
      return "Almost there! Just a few more steps to complete your setup! 🏁";
    } else {
      return "Congratulations! You've completed all your next steps! 🎉";
    }
  }

  getCategoryDisplayName(category: string): string {
    const displayNames: { [key: string]: string } = {
      profile: 'Profile Setup',
      accounts: 'Account Connections',
      notifications: 'Notifications',
      community: 'Community',
      goals: 'Financial Goals',
      insights: 'Insights & Analysis'
    };
    return displayNames[category] || category;
  }

  getCategoryIcon(category: string): string {
    const icons: { [key: string]: string } = {
      profile: '👤',
      accounts: '🏦',
      notifications: '🔔',
      community: '👥',
      goals: '🎯',
      insights: '📊'
    };
    return icons[category] || '📝';
  }
} 