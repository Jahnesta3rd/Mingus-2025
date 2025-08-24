// pages/api/user/onboarding-progress.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { getUserFromSession } from '../../../lib/auth';

interface OnboardingProgressRequest {
  currentStep: number;
  completedSteps: number[];
  userData: Record<string, any>;
  profileCompletionPercentage?: number;
}

interface OnboardingProgressResponse {
  success: boolean;
  message: string;
  progress?: {
    currentStep: number;
    completedSteps: number[];
    totalSteps: number;
    completionPercentage: number;
  };
  analytics?: {
    completionPercentage: number;
    completedFields: number;
    totalFields: number;
    missingFields: string[];
    categoryCompletions: Record<string, number>;
    nextRecommendedFields: string[];
  };
  errors?: Array<{
    field: string;
    message: string;
    code: string;
  }>;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse<OnboardingProgressResponse>) {
  switch (req.method) {
    case 'GET':
      return handleGetProgress(req, res);
    case 'POST':
      return handleSaveProgress(req, res);
    case 'DELETE':
      return handleClearProgress(req, res);
    default:
      return res.status(405).json({ 
        success: false, 
        message: 'Method not allowed' 
      });
  }
}

async function handleGetProgress(req: NextApiRequest, res: NextApiResponse<OnboardingProgressResponse>) {
  try {
    const user = await getUserFromSession(req);
    if (!user) {
      return res.status(401).json({ 
        success: false, 
        message: 'Unauthorized' 
      });
    }

    // Get saved progress from database or local storage
    const progress = await getOnboardingProgress(user.id);
    
    if (!progress) {
      return res.status(200).json({
        success: true,
        message: 'No saved progress found',
        progress: {
          currentStep: 1,
          completedSteps: [],
          totalSteps: 10,
          completionPercentage: 0
        }
      });
    }

    // Calculate analytics
    const analytics = calculateOnboardingAnalytics(progress.userData);

    res.status(200).json({
      success: true,
      message: 'Progress retrieved successfully',
      progress: {
        currentStep: progress.currentStep,
        completedSteps: progress.completedSteps,
        totalSteps: 10,
        completionPercentage: Math.round((progress.completedSteps.length / 10) * 100)
      },
      analytics
    });

  } catch (error) {
    console.error('Get progress error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Internal server error' 
    });
  }
}

async function handleSaveProgress(req: NextApiRequest, res: NextApiResponse<OnboardingProgressResponse>) {
  try {
    const user = await getUserFromSession(req);
    if (!user) {
      return res.status(401).json({ 
        success: false, 
        message: 'Unauthorized' 
      });
    }

    const { currentStep, completedSteps, userData, profileCompletionPercentage }: OnboardingProgressRequest = req.body;

    // Validate request
    if (currentStep < 1 || currentStep > 10) {
      return res.status(400).json({
        success: false,
        message: 'Invalid current step',
        errors: [{
          field: 'currentStep',
          message: 'Current step must be between 1 and 10',
          code: 'INVALID_STEP'
        }]
      });
    }

    if (!Array.isArray(completedSteps)) {
      return res.status(400).json({
        success: false,
        message: 'Completed steps must be an array',
        errors: [{
          field: 'completedSteps',
          message: 'Completed steps must be an array',
          code: 'INVALID_TYPE'
        }]
      });
    }

    // Save progress to database
    const savedProgress = await saveOnboardingProgress(user.id, {
      currentStep,
      completedSteps,
      userData,
      profileCompletionPercentage,
      updatedAt: new Date()
    });

    // Calculate analytics
    const analytics = calculateOnboardingAnalytics(userData);

    // Log progress save for analytics
    await logProgressSave(user.id, {
      currentStep,
      completedStepsCount: completedSteps.length,
      completionPercentage: analytics.completionPercentage
    });

    res.status(200).json({
      success: true,
      message: 'Progress saved successfully',
      progress: {
        currentStep: savedProgress.currentStep,
        completedSteps: savedProgress.completedSteps,
        totalSteps: 10,
        completionPercentage: Math.round((savedProgress.completedSteps.length / 10) * 100)
      },
      analytics
    });

  } catch (error) {
    console.error('Save progress error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Internal server error' 
    });
  }
}

async function handleClearProgress(req: NextApiRequest, res: NextApiResponse<OnboardingProgressResponse>) {
  try {
    const user = await getUserFromSession(req);
    if (!user) {
      return res.status(401).json({ 
        success: false, 
        message: 'Unauthorized' 
      });
    }

    // Clear saved progress
    await clearOnboardingProgress(user.id);

    // Log progress clear for analytics
    await logProgressClear(user.id);

    res.status(200).json({
      success: true,
      message: 'Progress cleared successfully'
    });

  } catch (error) {
    console.error('Clear progress error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Internal server error' 
    });
  }
}

// Helper functions
async function getOnboardingProgress(userId: string) {
  // Mock implementation - replace with actual database call
  console.log('Getting onboarding progress for user:', userId);
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // Return mock progress data
  return {
    currentStep: 3,
    completedSteps: [1, 2],
    userData: {
      firstName: 'John',
      lastName: 'Doe',
      email: 'john@example.com',
      monthlyIncome: 5000,
      incomeFrequency: 'monthly'
    },
    profileCompletionPercentage: 30,
    updatedAt: new Date()
  };
}

async function saveOnboardingProgress(userId: string, progress: any) {
  // Mock implementation - replace with actual database call
  console.log('Saving onboarding progress for user:', userId, progress);
  await new Promise(resolve => setTimeout(resolve, 100));
  
  return progress;
}

async function clearOnboardingProgress(userId: string) {
  // Mock implementation - replace with actual database call
  console.log('Clearing onboarding progress for user:', userId);
  await new Promise(resolve => setTimeout(resolve, 100));
}

function calculateOnboardingAnalytics(userData: Record<string, any>) {
  const totalFields = 25; // Total number of profile fields
  const completedFields = Object.keys(userData).filter(key => {
    const value = userData[key];
    return value !== null && value !== undefined && value !== '';
  }).length;

  const completionPercentage = Math.round((completedFields / totalFields) * 100);

  // Calculate category completions
  const categories = {
    personal: ['firstName', 'lastName', 'dateOfBirth', 'zipCode', 'phoneNumber'],
    financial: ['monthlyIncome', 'incomeFrequency', 'primaryIncomeSource', 'currentSavingsBalance', 'totalDebtAmount'],
    demographics: ['ageRange', 'maritalStatus', 'dependentsCount', 'householdSize', 'educationLevel'],
    goals: ['primaryFinancialGoal', 'riskToleranceLevel', 'financialKnowledgeLevel'],
    wellness: ['healthCheckinFrequency', 'stressLevelBaseline', 'wellnessGoals']
  };

  const categoryCompletions: Record<string, number> = {};
  
  Object.entries(categories).forEach(([category, fields]) => {
    const completed = fields.filter(field => {
      const value = userData[field];
      return value !== null && value !== undefined && value !== '';
    }).length;
    categoryCompletions[category] = Math.round((completed / fields.length) * 100);
  });

  // Identify missing fields
  const missingFields = Object.keys(userData).filter(key => {
    const value = userData[key];
    return value === null || value === undefined || value === '';
  });

  // Recommend next fields to complete
  const nextRecommendedFields = missingFields.slice(0, 3);

  return {
    completionPercentage,
    completedFields,
    totalFields,
    missingFields,
    categoryCompletions,
    nextRecommendedFields
  };
}

async function logProgressSave(userId: string, data: any) {
  // Mock implementation - replace with actual analytics logging
  console.log('Progress save logged:', { userId, ...data });
}

async function logProgressClear(userId: string) {
  // Mock implementation - replace with actual analytics logging
  console.log('Progress clear logged:', { userId });
} 