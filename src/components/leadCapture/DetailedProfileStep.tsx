import React, { useState } from 'react';
import { DetailedProfile, BasicLeadInfo } from '../../types/leadCapture';

interface DetailedProfileStepProps {
  onComplete: (profile: DetailedProfile) => void;
  onBack: () => void;
  initialData?: Partial<DetailedProfile>;
  basicInfo: BasicLeadInfo;
}

const DetailedProfileStep: React.FC<DetailedProfileStepProps> = ({
  onComplete,
  onBack,
  initialData = {},
  basicInfo
}) => {
  const [formData, setFormData] = useState<Partial<DetailedProfile>>({
    industry: initialData.industry || '',
    education: initialData.education || '',
    yearsOfExperience: initialData.yearsOfExperience || 0,
    careerGoals: initialData.careerGoals || [],
    targetSalary: initialData.targetSalary || basicInfo.currentSalary * 1.2,
    preferredLocation: initialData.preferredLocation || basicInfo.location,
    skills: initialData.skills || [],
    companySize: initialData.companySize || '',
    role: initialData.role || ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const careerGoalOptions = [
    'Increase salary by 20%+',
    'Move into leadership role',
    'Change industries',
    'Start my own business',
    'Achieve work-life balance',
    'Develop new skills',
    'Network with professionals',
    'Get promoted'
  ];

  const skillOptions = [
    'Leadership',
    'Project Management',
    'Data Analysis',
    'Communication',
    'Strategic Planning',
    'Technical Skills',
    'Sales & Marketing',
    'Financial Management',
    'Team Building',
    'Problem Solving',
    'Innovation',
    'Customer Service'
  ];

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.industry) {
      newErrors.industry = 'Industry is required';
    }

    if (!formData.education) {
      newErrors.education = 'Education level is required';
    }

    if (!formData.yearsOfExperience || formData.yearsOfExperience < 0) {
      newErrors.yearsOfExperience = 'Please enter valid years of experience';
    }

    if (!formData.targetSalary || formData.targetSalary <= 0) {
      newErrors.targetSalary = 'Please enter your target salary';
    }

    if (!formData.role) {
      newErrors.role = 'Current role is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      onComplete(formData as DetailedProfile);
    } catch (error) {
      console.error('Failed to submit detailed profile:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof DetailedProfile, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field as string]) {
      setErrors(prev => ({
        ...prev,
        [field as string]: ''
      }));
    }
  };

  const handleCareerGoalToggle = (goal: string) => {
    const currentGoals = formData.careerGoals || [];
    const newGoals = currentGoals.includes(goal)
      ? currentGoals.filter(g => g !== goal)
      : [...currentGoals, goal];

    handleInputChange('careerGoals', newGoals);
  };

  const handleSkillToggle = (skill: string) => {
    const currentSkills = formData.skills || [];
    const newSkills = currentSkills.includes(skill)
      ? currentSkills.filter(s => s !== skill)
      : [...currentSkills, skill];

    handleInputChange('skills', newSkills);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4" className="text-2xl font-semibold text-gray-800 mb-4">
          Tell Us More About Your Career
        </h2>
        <p className="text-lg text-gray-600">
          Help us create a personalized career advancement plan
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Industry */}
        <div>
          <label htmlFor="industry" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Industry <span className="text-red-500">*</span>
          </label>
          <select
            id="industry"
            value={formData.industry}
            onChange={(e) => handleInputChange('industry', e.target.value)}
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.industry ? 'border-red-500' : 'border-gray-300'
            }`}
            required
          >
            <option value="">Select your industry</option>
            <option value="Technology">Technology</option>
            <option value="Healthcare">Healthcare</option>
            <option value="Finance">Finance</option>
            <option value="Education">Education</option>
            <option value="Government">Government</option>
            <option value="Non-Profit">Non-Profit</option>
            <option value="Manufacturing">Manufacturing</option>
            <option value="Retail">Retail</option>
            <option value="Consulting">Consulting</option>
            <option value="Marketing">Marketing</option>
            <option value="Legal">Legal</option>
            <option value="Real Estate">Real Estate</option>
            <option value="Media">Media</option>
            <option value="Other">Other</option>
          </select>
          {errors.industry && (
            <p className="mt-1 text-base leading-relaxed text-red-600">{errors.industry}</p>
          )}
        </div>

        {/* Current Role */}
        <div>
          <label htmlFor="role" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Current Role <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="role"
            value={formData.role}
            onChange={(e) => handleInputChange('role', e.target.value)}
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.role ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="e.g., Software Engineer, Marketing Manager"
            required
          />
          {errors.role && (
            <p className="mt-1 text-base leading-relaxed text-red-600">{errors.role}</p>
          )}
        </div>

        {/* Education */}
        <div>
          <label htmlFor="education" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Highest Education Level <span className="text-red-500">*</span>
          </label>
          <select
            id="education"
            value={formData.education}
            onChange={(e) => handleInputChange('education', e.target.value)}
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.education ? 'border-red-500' : 'border-gray-300'
            }`}
            required
          >
            <option value="">Select education level</option>
            <option value="High School">High School</option>
            <option value="Associate's Degree">Associate's Degree</option>
            <option value="Bachelor's Degree">Bachelor's Degree</option>
            <option value="Master's Degree">Master's Degree</option>
            <option value="Doctorate">Doctorate</option>
            <option value="Professional Certification">Professional Certification</option>
          </select>
          {errors.education && (
            <p className="mt-1 text-base leading-relaxed text-red-600">{errors.education}</p>
          )}
        </div>

        {/* Years of Experience */}
        <div>
          <label htmlFor="yearsOfExperience" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Years of Professional Experience <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            id="yearsOfExperience"
            value={formData.yearsOfExperience || ''}
            onChange={(e) => handleInputChange('yearsOfExperience', parseInt(e.target.value) || 0)}
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.yearsOfExperience ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter years of experience"
            min="0"
            max="50"
            required
          />
          {errors.yearsOfExperience && (
            <p className="mt-1 text-base leading-relaxed text-red-600">{errors.yearsOfExperience}</p>
          )}
        </div>

        {/* Company Size */}
        <div>
          <label htmlFor="companySize" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Company Size
          </label>
          <select
            id="companySize"
            value={formData.companySize}
            onChange={(e) => handleInputChange('companySize', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select company size</option>
            <option value="1-10 employees">1-10 employees</option>
            <option value="11-50 employees">11-50 employees</option>
            <option value="51-200 employees">51-200 employees</option>
            <option value="201-500 employees">201-500 employees</option>
            <option value="501-1000 employees">501-1000 employees</option>
            <option value="1000+ employees">1000+ employees</option>
          </select>
        </div>

        {/* Target Salary */}
        <div>
          <label htmlFor="targetSalary" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Target Annual Salary <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <span className="absolute left-3 top-3 text-gray-500">$</span>
            <input
              type="number"
              id="targetSalary"
              value={formData.targetSalary || ''}
              onChange={(e) => handleInputChange('targetSalary', parseInt(e.target.value) || 0)}
              className={`w-full pl-8 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.targetSalary ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter your target salary"
              min="0"
              step="1000"
              required
            />
          </div>
          {errors.targetSalary && (
            <p className="mt-1 text-base leading-relaxed text-red-600">{errors.targetSalary}</p>
          )}
          <p className="mt-1 text-base leading-relaxed text-gray-500">
            Based on your current salary of ${basicInfo.currentSalary.toLocaleString()}
          </p>
        </div>

        {/* Career Goals */}
        <div>
          <label className="block text-base leading-relaxed font-medium text-gray-700 mb-3">
            Career Goals (Select all that apply)
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {careerGoalOptions.map((goal) => (
              <label key={goal} className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.careerGoals?.includes(goal) || false}
                  onChange={() => handleCareerGoalToggle(goal)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-base leading-relaxed text-gray-700">{goal}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Skills */}
        <div>
          <label className="block text-base leading-relaxed font-medium text-gray-700 mb-3">
            Skills You Want to Develop (Select all that apply)
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {skillOptions.map((skill) => (
              <label key={skill} className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.skills?.includes(skill) || false}
                  onChange={() => handleSkillToggle(skill)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-base leading-relaxed text-gray-700">{skill}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Preferred Location */}
        <div>
          <label htmlFor="preferredLocation" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Preferred Location for Next Role
          </label>
          <select
            id="preferredLocation"
            value={formData.preferredLocation}
            onChange={(e) => handleInputChange('preferredLocation', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={basicInfo.location}>Keep current location ({basicInfo.location})</option>
            <option value="Remote">Remote</option>
            <option value="New York, NY">New York, NY</option>
            <option value="San Francisco, CA">San Francisco, CA</option>
            <option value="Washington, DC">Washington, DC</option>
            <option value="Los Angeles, CA">Los Angeles, CA</option>
            <option value="Chicago, IL">Chicago, IL</option>
            <option value="Seattle, WA">Seattle, WA</option>
            <option value="Austin, TX">Austin, TX</option>
            <option value="Denver, CO">Denver, CO</option>
            <option value="Boston, MA">Boston, MA</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {/* Navigation Buttons */}
        <div className="flex gap-4 pt-6">
          <button
            type="button"
            onClick={onBack}
            className="flex-1 bg-gray-100 text-gray-700 py-4 px-6 rounded-lg font-semibold text-lg hover:bg-gray-200 transition-all duration-200"
          >
            Back
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Processing...
              </div>
            ) : (
              'Generate Personalized Report'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default DetailedProfileStep; 