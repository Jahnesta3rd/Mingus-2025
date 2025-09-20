import React, { useState, useEffect } from 'react';
import { User, MapPin, GraduationCap, Briefcase, DollarSign, Calendar, Target, TrendingUp, AlertCircle, CheckCircle, Car } from 'lucide-react';

// Types
interface PersonalInfo {
  age: number;
  location: string;
  education: string;
  employment: string;
}

interface FinancialInfo {
  annualIncome: number;
  monthlyTakehome: number;
  studentLoans: number;
  creditCardDebt: number;
  currentSavings: number;
}

interface MonthlyExpenses {
  rent: number;
  carPayment: number;
  insurance: number;
  groceries: number;
  utilities: number;
  studentLoanPayment: number;
  creditCardMinimum: number;
}

interface ImportantDates {
  birthday: string;
  plannedVacation: { date: string; cost: number };
  carInspection: { date: string; cost: number };
  sistersWedding: { date: string; cost: number };
}

interface HealthWellness {
  physicalActivity: number; // workouts per week
  relationshipSatisfaction: number; // 1-10 scale
  meditationMinutes: number; // total minutes
  stressSpending: number; // dollars spent when stressed
}

interface VehicleWellness {
  vehicleExpenses: number; // unexpected vehicle costs this week
  transportationStress: number; // 1-5 scale
  commuteSatisfaction: number; // 1-5 scale
  vehicleDecisions: string; // financial decisions made this week
}

interface Goals {
  emergencyFund: number;
  debtPayoffDate: string;
  monthlySavings: number;
}

interface UserProfileData {
  personalInfo: PersonalInfo;
  financialInfo: FinancialInfo;
  monthlyExpenses: MonthlyExpenses;
  importantDates: ImportantDates;
  healthWellness: HealthWellness;
  vehicleWellness: VehicleWellness;
  goals: Goals;
}

interface UserProfileProps {
  onSave: (data: UserProfileData) => void;
  onComplete: () => void;
  className?: string;
}

const UserProfile: React.FC<UserProfileProps> = ({ onSave, onComplete, className = '' }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [profileData, setProfileData] = useState<UserProfileData>({
    personalInfo: {
      age: 0,
      location: '',
      education: '',
      employment: ''
    },
    financialInfo: {
      annualIncome: 0,
      monthlyTakehome: 0,
      studentLoans: 0,
      creditCardDebt: 0,
      currentSavings: 0
    },
    monthlyExpenses: {
      rent: 0,
      carPayment: 0,
      insurance: 0,
      groceries: 0,
      utilities: 0,
      studentLoanPayment: 0,
      creditCardMinimum: 0
    },
    importantDates: {
      birthday: '',
      plannedVacation: { date: '', cost: 0 },
      carInspection: { date: '', cost: 0 },
      sistersWedding: { date: '', cost: 0 }
    },
    healthWellness: {
      physicalActivity: 0,
      relationshipSatisfaction: 0,
      meditationMinutes: 0,
      stressSpending: 0
    },
    vehicleWellness: {
      vehicleExpenses: 0,
      transportationStress: 0,
      commuteSatisfaction: 0,
      vehicleDecisions: ''
    },
    goals: {
      emergencyFund: 0,
      debtPayoffDate: '',
      monthlySavings: 0
    }
  });

  const steps = [
    { title: 'Personal Info', icon: User },
    { title: 'Financial Info', icon: DollarSign },
    { title: 'Monthly Expenses', icon: TrendingUp },
    { title: 'Important Dates', icon: Calendar },
    { title: 'Health & Wellness', icon: Target },
    { title: 'Vehicle & Transportation', icon: Car },
    { title: 'Goals', icon: CheckCircle }
  ];

  const handleInputChange = (section: keyof UserProfileData, field: string, value: any) => {
    setProfileData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const handleNestedInputChange = (section: keyof UserProfileData, parentField: string, childField: string, value: any) => {
    setProfileData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [parentField]: {
          ...(prev[section] as any)[parentField],
          [childField]: value
        }
      }
    }));
  };

  const handleNext = async () => {
    if (currentStep < steps.length - 1) {
      // Submit weekly check-in data when moving from vehicle wellness step
      if (currentStep === 5) { // Vehicle & Transportation step
        await submitWeeklyCheckin();
      }
      setCurrentStep(currentStep + 1);
    } else {
      onSave(profileData);
      onComplete();
    }
  };

  const submitWeeklyCheckin = async () => {
    try {
      const checkinData = {
        check_in_date: new Date().toISOString().split('T')[0], // Today's date
        healthWellness: profileData.healthWellness,
        vehicleWellness: profileData.vehicleWellness
      };

      const response = await fetch('/api/weekly-checkin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': 'user_123', // This should come from props or context
        },
        credentials: 'include',
        body: JSON.stringify(checkinData)
      });

      if (!response.ok) {
        console.error('Failed to submit weekly check-in:', response.statusText);
      } else {
        console.log('Weekly check-in submitted successfully');
      }
    } catch (error) {
      console.error('Error submitting weekly check-in:', error);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const isStepValid = (step: number): boolean => {
    switch (step) {
      case 0: // Personal Info
        return profileData.personalInfo.age > 0 && 
               profileData.personalInfo.location !== '' && 
               profileData.personalInfo.education !== '' && 
               profileData.personalInfo.employment !== '';
      case 1: // Financial Info
        return profileData.financialInfo.annualIncome > 0 && 
               profileData.financialInfo.monthlyTakehome > 0;
      case 2: // Monthly Expenses
        return profileData.monthlyExpenses.rent > 0;
      case 3: // Important Dates
        return profileData.importantDates.birthday !== '';
      case 4: // Health & Wellness
        return true; // All fields optional
      case 5: // Goals
        return profileData.goals.emergencyFund > 0;
      default:
        return false;
    }
  };

  const renderPersonalInfo = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <User className="w-12 h-12 text-violet-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Personal Information</h2>
        <p className="text-gray-400">Tell us about yourself</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-white mb-2">Age</label>
          <input
            type="number"
            value={profileData.personalInfo.age || ''}
            onChange={(e) => handleInputChange('personalInfo', 'age', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="28"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Location</label>
          <input
            type="text"
            value={profileData.personalInfo.location}
            onChange={(e) => handleInputChange('personalInfo', 'location', e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="Atlanta, GA"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Education</label>
          <select
            value={profileData.personalInfo.education}
            onChange={(e) => handleInputChange('personalInfo', 'education', e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
          >
            <option value="">Select Education Level</option>
            <option value="High School">High School</option>
            <option value="Associate's Degree">Associate's Degree</option>
            <option value="Bachelor's Degree">Bachelor's Degree</option>
            <option value="Master's Degree">Master's Degree</option>
            <option value="Doctorate">Doctorate</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Employment</label>
          <input
            type="text"
            value={profileData.personalInfo.employment}
            onChange={(e) => handleInputChange('personalInfo', 'employment', e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="Marketing Coordinator"
          />
        </div>
      </div>
    </div>
  );

  const renderFinancialInfo = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <DollarSign className="w-12 h-12 text-violet-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Financial Information</h2>
        <p className="text-gray-400">Let's understand your financial situation</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-white mb-2">Annual Income</label>
          <input
            type="number"
            value={profileData.financialInfo.annualIncome || ''}
            onChange={(e) => handleInputChange('financialInfo', 'annualIncome', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="65000"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Monthly Take-home</label>
          <input
            type="number"
            value={profileData.financialInfo.monthlyTakehome || ''}
            onChange={(e) => handleInputChange('financialInfo', 'monthlyTakehome', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="4200"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Student Loans</label>
          <input
            type="number"
            value={profileData.financialInfo.studentLoans || ''}
            onChange={(e) => handleInputChange('financialInfo', 'studentLoans', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="35000"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Credit Card Debt</label>
          <input
            type="number"
            value={profileData.financialInfo.creditCardDebt || ''}
            onChange={(e) => handleInputChange('financialInfo', 'creditCardDebt', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="8500"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-white mb-2">Current Savings</label>
          <input
            type="number"
            value={profileData.financialInfo.currentSavings || ''}
            onChange={(e) => handleInputChange('financialInfo', 'currentSavings', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="1200"
          />
        </div>
      </div>
    </div>
  );

  const renderMonthlyExpenses = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <TrendingUp className="w-12 h-12 text-violet-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Monthly Expenses</h2>
        <p className="text-gray-400">Track your monthly spending</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-white mb-2">Rent</label>
          <input
            type="number"
            value={profileData.monthlyExpenses.rent || ''}
            onChange={(e) => handleInputChange('monthlyExpenses', 'rent', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="1400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Car Payment</label>
          <input
            type="number"
            value={profileData.monthlyExpenses.carPayment || ''}
            onChange={(e) => handleInputChange('monthlyExpenses', 'carPayment', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="320"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Insurance</label>
          <input
            type="number"
            value={profileData.monthlyExpenses.insurance || ''}
            onChange={(e) => handleInputChange('monthlyExpenses', 'insurance', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="180"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Groceries</label>
          <input
            type="number"
            value={profileData.monthlyExpenses.groceries || ''}
            onChange={(e) => handleInputChange('monthlyExpenses', 'groceries', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Utilities</label>
          <input
            type="number"
            value={profileData.monthlyExpenses.utilities || ''}
            onChange={(e) => handleInputChange('monthlyExpenses', 'utilities', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="150"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Student Loan Payment</label>
          <input
            type="number"
            value={profileData.monthlyExpenses.studentLoanPayment || ''}
            onChange={(e) => handleInputChange('monthlyExpenses', 'studentLoanPayment', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="380"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Credit Card Minimum</label>
          <input
            type="number"
            value={profileData.monthlyExpenses.creditCardMinimum || ''}
            onChange={(e) => handleInputChange('monthlyExpenses', 'creditCardMinimum', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="210"
          />
        </div>
      </div>
    </div>
  );

  const renderImportantDates = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <Calendar className="w-12 h-12 text-violet-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Important Dates</h2>
        <p className="text-gray-400">Plan for upcoming events and expenses</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-white mb-2">Birthday</label>
          <input
            type="date"
            value={profileData.importantDates.birthday}
            onChange={(e) => handleInputChange('importantDates', 'birthday', e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Planned Vacation Date</label>
          <input
            type="date"
            value={profileData.importantDates.plannedVacation.date}
            onChange={(e) => handleNestedInputChange('importantDates', 'plannedVacation', 'date', e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Vacation Cost</label>
          <input
            type="number"
            value={profileData.importantDates.plannedVacation.cost || ''}
            onChange={(e) => handleNestedInputChange('importantDates', 'plannedVacation', 'cost', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="2000"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Car Inspection Date</label>
          <input
            type="date"
            value={profileData.importantDates.carInspection.date}
            onChange={(e) => handleNestedInputChange('importantDates', 'carInspection', 'date', e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Inspection Cost</label>
          <input
            type="number"
            value={profileData.importantDates.carInspection.cost || ''}
            onChange={(e) => handleNestedInputChange('importantDates', 'carInspection', 'cost', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="150"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Sister's Wedding Date</label>
          <input
            type="date"
            value={profileData.importantDates.sistersWedding.date}
            onChange={(e) => handleNestedInputChange('importantDates', 'sistersWedding', 'date', e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Wedding Cost</label>
          <input
            type="number"
            value={profileData.importantDates.sistersWedding.cost || ''}
            onChange={(e) => handleNestedInputChange('importantDates', 'sistersWedding', 'cost', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="800"
          />
        </div>
      </div>
    </div>
  );

  const renderHealthWellness = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <Target className="w-12 h-12 text-violet-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Health & Wellness</h2>
        <p className="text-gray-400">Complete your weekly check-in</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-white mb-2">Physical Activity (workouts this week)</label>
          <input
            type="number"
            value={profileData.healthWellness.physicalActivity || ''}
            onChange={(e) => handleInputChange('healthWellness', 'physicalActivity', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="3"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Relationship Satisfaction (1-10)</label>
          <input
            type="number"
            min="1"
            max="10"
            value={profileData.healthWellness.relationshipSatisfaction || ''}
            onChange={(e) => handleInputChange('healthWellness', 'relationshipSatisfaction', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="7"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Meditation/Mindfulness (total minutes)</label>
          <input
            type="number"
            value={profileData.healthWellness.meditationMinutes || ''}
            onChange={(e) => handleInputChange('healthWellness', 'meditationMinutes', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="45"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Stress-related Spending ($)</label>
          <input
            type="number"
            value={profileData.healthWellness.stressSpending || ''}
            onChange={(e) => handleInputChange('healthWellness', 'stressSpending', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="120"
          />
        </div>
      </div>
    </div>
  );

  const renderVehicleWellness = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <Car className="w-12 h-12 text-violet-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Vehicle & Transportation</h2>
        <p className="text-gray-400">Track your vehicle-related expenses and satisfaction</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-white mb-2">Unexpected Vehicle Costs This Week ($)</label>
          <input
            type="number"
            value={profileData.vehicleWellness.vehicleExpenses || ''}
            onChange={(e) => handleInputChange('vehicleWellness', 'vehicleExpenses', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="0"
          />
          <p className="text-sm text-gray-400 mt-1">Repairs, maintenance, tickets, etc.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Transportation Stress Level (1-5)</label>
          <select
            value={profileData.vehicleWellness.transportationStress || ''}
            onChange={(e) => handleInputChange('vehicleWellness', 'transportationStress', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
          >
            <option value="">Select stress level</option>
            <option value="1">1 - Very Low</option>
            <option value="2">2 - Low</option>
            <option value="3">3 - Moderate</option>
            <option value="4">4 - High</option>
            <option value="5">5 - Very High</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Commute Satisfaction (1-5)</label>
          <select
            value={profileData.vehicleWellness.commuteSatisfaction || ''}
            onChange={(e) => handleInputChange('vehicleWellness', 'commuteSatisfaction', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
          >
            <option value="">Select satisfaction level</option>
            <option value="1">1 - Very Dissatisfied</option>
            <option value="2">2 - Dissatisfied</option>
            <option value="3">3 - Neutral</option>
            <option value="4">4 - Satisfied</option>
            <option value="5">5 - Very Satisfied</option>
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-white mb-2">Vehicle-Related Financial Decisions This Week</label>
          <textarea
            value={profileData.vehicleWellness.vehicleDecisions}
            onChange={(e) => handleInputChange('vehicleWellness', 'vehicleDecisions', e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            rows={3}
            placeholder="e.g., Decided to get new tires, researched car insurance options, planned maintenance schedule..."
          />
          <p className="text-sm text-gray-400 mt-1">Any financial decisions or planning related to your vehicle</p>
        </div>
      </div>
    </div>
  );

  const renderGoals = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <CheckCircle className="w-12 h-12 text-violet-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Goals Setting</h2>
        <p className="text-gray-400">Set your financial goals</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-white mb-2">Emergency Fund Goal</label>
          <input
            type="number"
            value={profileData.goals.emergencyFund || ''}
            onChange={(e) => handleInputChange('goals', 'emergencyFund', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="12000"
          />
          <p className="text-sm text-gray-400 mt-1">3 months of expenses</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-white mb-2">Debt Payoff Goal Date</label>
          <input
            type="date"
            value={profileData.goals.debtPayoffDate}
            onChange={(e) => handleInputChange('goals', 'debtPayoffDate', e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
          />
          <p className="text-sm text-gray-400 mt-1">Credit cards by December 2026</p>
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-white mb-2">Monthly Savings Goal</label>
          <input
            type="number"
            value={profileData.goals.monthlySavings || ''}
            onChange={(e) => handleInputChange('goals', 'monthlySavings', parseInt(e.target.value) || 0)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="500"
          />
          <p className="text-sm text-gray-400 mt-1">Starting next month</p>
        </div>
      </div>
    </div>
  );

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: return renderPersonalInfo();
      case 1: return renderFinancialInfo();
      case 2: return renderMonthlyExpenses();
      case 3: return renderImportantDates();
      case 4: return renderHealthWellness();
      case 5: return renderVehicleWellness();
      case 6: return renderGoals();
      default: return null;
    }
  };

  return (
    <div className={`bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">Profile Setup</h2>
            <p className="text-violet-100 text-sm">Step {currentStep + 1} of {steps.length}</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-violet-200">Jordan Washington</div>
            <div className="text-xs text-violet-300">Profile Completion</div>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-violet-400 bg-opacity-30 rounded-full h-3 mb-2">
          <div 
            className="bg-white h-3 rounded-full transition-all duration-500 ease-out shadow-lg"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>
        <div className="flex items-center justify-between">
          <p className="text-violet-100 text-sm font-medium">
            {steps[currentStep].title}
          </p>
          <p className="text-violet-200 text-xs">
            {Math.round(((currentStep + 1) / steps.length) * 100)}% Complete
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
        {renderStepContent()}
      </div>

      {/* Navigation */}
      <div className="bg-gray-800 px-6 py-4 flex items-center justify-between">
        <button
          onClick={handlePrevious}
          disabled={currentStep === 0}
          className="flex items-center space-x-2 bg-gray-700 text-white px-6 py-2 rounded-lg font-semibold hover:bg-gray-600 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors duration-200"
        >
          <span>Previous</span>
        </button>

        <div className="flex space-x-2">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div
                key={index}
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  index <= currentStep ? 'bg-violet-500 text-white' : 'bg-gray-600 text-gray-400'
                }`}
              >
                <Icon className="w-4 h-4" />
              </div>
            );
          })}
        </div>

        <button
          onClick={handleNext}
          disabled={!isStepValid(currentStep)}
          className="flex items-center space-x-2 bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 disabled:from-gray-600 disabled:to-gray-600 text-white px-6 py-2 rounded-lg font-semibold transition-all duration-200 disabled:cursor-not-allowed"
        >
          <span>{currentStep === steps.length - 1 ? 'Complete Setup' : 'Next'}</span>
        </button>
      </div>
    </div>
  );
};

export default UserProfile;
