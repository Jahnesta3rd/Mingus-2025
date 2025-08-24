// pages/api/user/profile.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { getUserFromSession, updateUserProfile } from '../../../lib/auth';
import { validateUserProfileData } from '../../../lib/validation';
import { UserProfile, UserProfileUpdate } from '../../../types/user';

interface ProfileUpdateRequest {
  data: Partial<UserProfileUpdate>;
  onboardingStep?: number;
  profileCompletionPercentage?: number;
}

interface ProfileUpdateResponse {
  success: boolean;
  message: string;
  user?: Partial<UserProfile>;
  analytics?: {
    completionPercentage: number;
    completedFields: number;
    totalFields: number;
    missingFields: string[];
    categoryCompletions: Record<string, number>;
  };
  errors?: Array<{
    field: string;
    message: string;
    code: string;
  }>;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse<ProfileUpdateResponse>) {
  // Handle different HTTP methods
  switch (req.method) {
    case 'GET':
      return handleGetProfile(req, res);
    case 'PATCH':
      return handleUpdateProfile(req, res);
    case 'POST':
      return handleCreateProfile(req, res);
    default:
      return res.status(405).json({ 
        success: false, 
        message: 'Method not allowed' 
      });
  }
}

async function handleGetProfile(req: NextApiRequest, res: NextApiResponse<ProfileUpdateResponse>) {
  try {
    const user = await getUserFromSession(req);
    if (!user) {
      return res.status(401).json({ 
        success: false, 
        message: 'Unauthorized' 
      });
    }

    // Get user profile from database
    const userProfile = await getUserProfile(user.id);
    
    if (!userProfile) {
      return res.status(404).json({ 
        success: false, 
        message: 'Profile not found' 
      });
    }

    // Calculate analytics
    const analytics = calculateProfileAnalytics(userProfile);

    res.status(200).json({
      success: true,
      message: 'Profile retrieved successfully',
      user: userProfile,
      analytics
    });

  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Internal server error' 
    });
  }
}

async function handleUpdateProfile(req: NextApiRequest, res: NextApiResponse<ProfileUpdateResponse>) {
  try {
    const user = await getUserFromSession(req);
    if (!user) {
      return res.status(401).json({ 
        success: false, 
        message: 'Unauthorized' 
      });
    }

    const { data, onboardingStep, profileCompletionPercentage }: ProfileUpdateRequest = req.body;

    // Validate request body
    if (!data || typeof data !== 'object') {
      return res.status(400).json({
        success: false,
        message: 'Invalid request body',
        errors: [{
          field: 'data',
          message: 'Profile data is required',
          code: 'MISSING_DATA'
        }]
      });
    }

    // Validate user profile data
    const validation = validateUserProfileData(data);
    if (!validation.isValid) {
      return res.status(400).json({
        success: false,
        message: 'Validation failed',
        errors: validation.errors.map(error => ({
          field: 'data',
          message: error,
          code: 'VALIDATION_ERROR'
        }))
      });
    }

    // Prepare update data
    const updateData: Partial<UserProfileUpdate> = {
      ...data,
      updatedAt: new Date()
    };

    // Add onboarding-specific fields if provided
    if (onboardingStep !== undefined) {
      updateData.onboardingStep = onboardingStep;
    }

    if (profileCompletionPercentage !== undefined) {
      updateData.profileCompletionPercentage = profileCompletionPercentage;
    }

    // Update user profile in database
    const updatedUser = await updateUserProfile(user.id, updateData);
    
    // Calculate updated analytics
    const analytics = calculateProfileAnalytics(updatedUser);

    // Log profile update for analytics
    await logProfileUpdate(user.id, {
      updatedFields: Object.keys(data),
      completionPercentage: analytics.completionPercentage,
      onboardingStep: onboardingStep || updatedUser.onboardingStep
    });

    res.status(200).json({
      success: true,
      message: 'Profile updated successfully',
      user: updatedUser,
      analytics
    });

  } catch (error) {
    console.error('Profile update error:', error);
    
    // Handle specific database errors
    if (error.code === 'DUPLICATE_ENTRY') {
      return res.status(409).json({
        success: false,
        message: 'Profile already exists',
        errors: [{
          field: 'email',
          message: 'A profile with this email already exists',
          code: 'DUPLICATE_EMAIL'
        }]
      });
    }

    if (error.code === 'FOREIGN_KEY_CONSTRAINT') {
      return res.status(400).json({
        success: false,
        message: 'Invalid reference data',
        errors: [{
          field: 'reference',
          message: 'Referenced data does not exist',
          code: 'INVALID_REFERENCE'
        }]
      });
    }

    res.status(500).json({ 
      success: false, 
      message: 'Internal server error' 
    });
  }
}

async function handleCreateProfile(req: NextApiRequest, res: NextApiResponse<ProfileUpdateResponse>) {
  try {
    const user = await getUserFromSession(req);
    if (!user) {
      return res.status(401).json({ 
        success: false, 
        message: 'Unauthorized' 
      });
    }

    const { data }: { data: Partial<UserProfile> } = req.body;

    // Validate request body
    if (!data || typeof data !== 'object') {
      return res.status(400).json({
        success: false,
        message: 'Invalid request body',
        errors: [{
          field: 'data',
          message: 'Profile data is required',
          code: 'MISSING_DATA'
        }]
      });
    }

    // Validate user profile data
    const validation = validateUserProfileData(data);
    if (!validation.isValid) {
      return res.status(400).json({
        success: false,
        message: 'Validation failed',
        errors: validation.errors.map(error => ({
          field: 'data',
          message: error,
          code: 'VALIDATION_ERROR'
        }))
      });
    }

    // Check if profile already exists
    const existingProfile = await getUserProfile(user.id);
    if (existingProfile) {
      return res.status(409).json({
        success: false,
        message: 'Profile already exists',
        errors: [{
          field: 'id',
          message: 'User profile already exists',
          code: 'PROFILE_EXISTS'
        }]
      });
    }

    // Create new profile
    const newProfile = await createUserProfile(user.id, {
      ...data,
      id: user.id,
      createdAt: new Date(),
      updatedAt: new Date(),
      profileCompletionPercentage: 0,
      onboardingStep: 1
    });

    // Calculate analytics
    const analytics = calculateProfileAnalytics(newProfile);

    // Log profile creation
    await logProfileCreation(user.id, {
      initialFields: Object.keys(data),
      completionPercentage: analytics.completionPercentage
    });

    res.status(201).json({
      success: true,
      message: 'Profile created successfully',
      user: newProfile,
      analytics
    });

  } catch (error) {
    console.error('Profile creation error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Internal server error' 
    });
  }
}

// Helper functions (these would be implemented in your database layer)
async function getUserProfile(userId: string): Promise<Partial<UserProfile> | null> {
  // Implementation would connect to your database
  // Example: return await db.users.findUnique({ where: { id: userId } });
  throw new Error('getUserProfile not implemented');
}

async function updateUserProfile(userId: string, data: Partial<UserProfileUpdate>): Promise<Partial<UserProfile>> {
  // Implementation would connect to your database
  // Example: return await db.users.update({ where: { id: userId }, data });
  throw new Error('updateUserProfile not implemented');
}

async function createUserProfile(userId: string, data: Partial<UserProfile>): Promise<Partial<UserProfile>> {
  // Implementation would connect to your database
  // Example: return await db.users.create({ data });
  throw new Error('createUserProfile not implemented');
}

function calculateProfileAnalytics(profile: Partial<UserProfile>) {
  const totalFields = 25; // Total number of profile fields
  const completedFields = Object.keys(profile).filter(key => {
    const value = profile[key as keyof UserProfile];
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
      const value = profile[field as keyof UserProfile];
      return value !== null && value !== undefined && value !== '';
    }).length;
    categoryCompletions[category] = Math.round((completed / fields.length) * 100);
  });

  // Identify missing fields
  const missingFields = Object.keys(profile).filter(key => {
    const value = profile[key as keyof UserProfile];
    return value === null || value === undefined || value === '';
  });

  return {
    completionPercentage,
    completedFields,
    totalFields,
    missingFields,
    categoryCompletions
  };
}

async function logProfileUpdate(userId: string, data: any) {
  // Implementation would log to your analytics system
  // Example: await analytics.track('profile_updated', { userId, ...data });
  console.log('Profile update logged:', { userId, ...data });
}

async function logProfileCreation(userId: string, data: any) {
  // Implementation would log to your analytics system
  // Example: await analytics.track('profile_created', { userId, ...data });
  console.log('Profile creation logged:', { userId, ...data });
} 