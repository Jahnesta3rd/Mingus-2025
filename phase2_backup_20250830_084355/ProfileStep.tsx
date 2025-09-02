import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface ProfileData {
  // Basic Info
  first_name: string;
  last_name: string;
  age_range: string;
  gender: string;
  
  // Location & Household
  zip_code: string;
  location_state: string;
  location_city: string;
  household_size: string;
  dependents: string;
  relationship_status: string;
  
  // Income & Employment
  monthly_income: string;
  income_frequency: string;
  primary_income_source: string;
  employment_status: string;
  industry: string;
  job_title: string;
  naics_code: string;
  
  // Financial Status
  current_savings: string;
  current_debt: string;
  credit_score_range: string;
}

// Industry options with NAICS codes
const industries = [
  { value: "technology", label: "Technology/Software", naics: "541500" },
  { value: "healthcare", label: "Healthcare", naics: "621100" },
  { value: "finance", label: "Financial Services", naics: "522100" },
  { value: "education", label: "Education", naics: "611100" },
  { value: "government", label: "Government", naics: "921000" },
  { value: "retail", label: "Retail/Hospitality", naics: "445000" },
  { value: "manufacturing", label: "Manufacturing", naics: "332000" },
  { value: "consulting", label: "Professional Services", naics: "541600" },
  { value: "legal", label: "Legal Services", naics: "541100" },
  { value: "real_estate", label: "Real Estate", naics: "531000" },
  { value: "construction", label: "Construction", naics: "236000" },
  { value: "transportation", label: "Transportation", naics: "484000" },
  { value: "utilities", label: "Utilities", naics: "221000" },
  { value: "media", label: "Media/Entertainment", naics: "512000" },
  { value: "nonprofit", label: "Non-Profit", naics: "813000" },
  { value: "other", label: "Other", naics: "" }
];

const ProfileStep: React.FC = () => {
  const [formData, setFormData] = useState<ProfileData>({
    // Basic Info
    first_name: '',
    last_name: '',
    age_range: '',
    gender: '',
    
    // Location & Household
    zip_code: '',
    location_state: '',
    location_city: '',
    household_size: '',
    dependents: '',
    relationship_status: '',
    
    // Income & Employment
    monthly_income: '',
    income_frequency: 'monthly',
    primary_income_source: '',
    employment_status: '',
    industry: '',
    job_title: '',
    naics_code: '',
    
    // Financial Status
    current_savings: '',
    current_debt: '',
    credit_score_range: '',
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const navigate = useNavigate();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear validation error when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
    
    // Auto-populate NAICS code when industry changes
    if (name === 'industry') {
      const selectedIndustry = industries.find(ind => ind.value === value);
      if (selectedIndustry) {
        setFormData(prev => ({
          ...prev,
          naics_code: selectedIndustry.naics
        }));
      }
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    // Basic Info validation
    if (!formData.first_name.trim()) errors.first_name = 'First name is required';
    if (!formData.last_name.trim()) errors.last_name = 'Last name is required';
    if (!formData.age_range) errors.age_range = 'Age range is required';
    
    // Location validation
    if (!formData.zip_code.trim()) errors.zip_code = 'Zip code is required';
    if (!/^\d{5}(-\d{4})?$/.test(formData.zip_code)) {
      errors.zip_code = 'Please enter a valid zip code';
    }
    if (!formData.location_state.trim()) errors.location_state = 'State is required';
    if (!formData.location_city.trim()) errors.location_city = 'City is required';
    
    // Household validation
    if (!formData.household_size) errors.household_size = 'Household size is required';
    if (!formData.relationship_status) errors.relationship_status = 'Relationship status is required';
    
    // Employment validation
    if (!formData.industry) errors.industry = 'Industry is required';
    if (!formData.job_title.trim()) errors.job_title = 'Job title is required';
    if (!formData.employment_status) errors.employment_status = 'Employment status is required';
    
    // Income validation
    if (!formData.monthly_income) errors.monthly_income = 'Monthly income is required';
    if (!formData.primary_income_source) errors.primary_income_source = 'Primary income source is required';
    
    // Financial validation
    if (!formData.current_savings) errors.current_savings = 'Current savings is required';
    if (!formData.current_debt) errors.current_debt = 'Current debt is required';
    if (!formData.credit_score_range) errors.credit_score_range = 'Credit score range is required';
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      setError('Please fix the validation errors below');
      return;
    }
    
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/onboarding/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        navigate('/onboarding/verification');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to save profile');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Progress Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-900">Profile Setup</h1>
            <span className="text-base leading-relaxed text-gray-500">Step 2 of 7</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-600 h-2 rounded-full" style={{ width: '28%' }}></div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Tell us about yourself</h2>
            <p className="text-gray-600">This helps us provide personalized financial insights and recommendations.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600">{error}</p>
              </div>
            )}

            {/* Basic Information Section */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                          <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
          First Name *
        </label>
                  <input
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.first_name ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter your first name"
                  />
                  {validationErrors.first_name && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.first_name}</p>
                  )}
                </div>

                <div>
                          <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
          Last Name *
        </label>
                  <input
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.last_name ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter your last name"
                  />
                  {validationErrors.last_name && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.last_name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Gender
                  </label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Prefer not to say</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="non_binary">Non-binary</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div className="mt-6">
                        <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
          Age Range *
        </label>
                <select
                  name="age_range"
                  value={formData.age_range}
                  onChange={handleInputChange}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    validationErrors.age_range ? 'border-red-300' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select age range</option>
                  <option value="18-24">18-24</option>
                  <option value="25-34">25-34</option>
                  <option value="35-44">35-44</option>
                  <option value="45-54">45-54</option>
                  <option value="55-64">55-64</option>
                  <option value="65+">65+</option>
                </select>
                {validationErrors.age_range && (
                  <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.age_range}</p>
                )}
              </div>
            </div>

            {/* Location & Household Section */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Location & Household</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                          <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
          Zip Code *
        </label>
                  <input
                    type="text"
                    name="zip_code"
                    value={formData.zip_code}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.zip_code ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter zip code"
                    maxLength={10}
                  />
                  {validationErrors.zip_code && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.zip_code}</p>
                  )}
                </div>

                <div>
                          <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
          State *
        </label>
                  <input
                    type="text"
                    name="location_state"
                    value={formData.location_state}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.location_state ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter your state"
                  />
                  {validationErrors.location_state && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.location_state}</p>
                  )}
                </div>

                <div>
                          <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
          City *
        </label>
                  <input
                    type="text"
                    name="location_city"
                    value={formData.location_city}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.location_city ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter your city"
                  />
                  {validationErrors.location_city && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.location_city}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Household Size *
                  </label>
                  <select
                    name="household_size"
                    value={formData.household_size}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.household_size ? 'border-red-300' : 'border-gray-300'
                    }`}
                  >
                    <option value="">Select household size</option>
                    <option value="1">1 person</option>
                    <option value="2">2 people</option>
                    <option value="3">3 people</option>
                    <option value="4">4 people</option>
                    <option value="5+">5+ people</option>
                  </select>
                  {validationErrors.household_size && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.household_size}</p>
                  )}
                </div>

                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Dependents
                  </label>
                  <select
                    name="dependents"
                    value={formData.dependents}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select number of dependents</option>
                    <option value="0">0 dependents</option>
                    <option value="1">1 dependent</option>
                    <option value="2">2 dependents</option>
                    <option value="3">3 dependents</option>
                    <option value="4+">4+ dependents</option>
                  </select>
                </div>

                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Relationship Status *
                  </label>
                  <select
                    name="relationship_status"
                    value={formData.relationship_status}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.relationship_status ? 'border-red-300' : 'border-gray-300'
                    }`}
                  >
                    <option value="">Select relationship status</option>
                    <option value="single">Single</option>
                    <option value="married">Married</option>
                    <option value="domestic_partner">Domestic Partner</option>
                    <option value="divorced">Divorced</option>
                    <option value="widowed">Widowed</option>
                    <option value="separated">Separated</option>
                  </select>
                  {validationErrors.relationship_status && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.relationship_status}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Income & Employment Section */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Income & Employment</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Monthly Income *
                  </label>
                  <input
                    type="number"
                    name="monthly_income"
                    value={formData.monthly_income}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.monthly_income ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter your monthly income"
                  />
                  {validationErrors.monthly_income && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.monthly_income}</p>
                  )}
                </div>

                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Income Frequency
                  </label>
                  <select
                    name="income_frequency"
                    value={formData.income_frequency}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Bi-weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Employment Status *
                  </label>
                  <select
                    name="employment_status"
                    value={formData.employment_status}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.employment_status ? 'border-red-300' : 'border-gray-300'
                    }`}
                  >
                    <option value="">Select employment status</option>
                    <option value="employed">Employed</option>
                    <option value="self_employed">Self-Employed</option>
                    <option value="unemployed">Unemployed</option>
                    <option value="student">Student</option>
                    <option value="retired">Retired</option>
                    <option value="seeking">Seeking Employment</option>
                    <option value="other">Other</option>
                  </select>
                  {validationErrors.employment_status && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.employment_status}</p>
                  )}
                </div>

                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Primary Income Source *
                  </label>
                  <select
                    name="primary_income_source"
                    value={formData.primary_income_source}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.primary_income_source ? 'border-red-300' : 'border-gray-300'
                    }`}
                  >
                    <option value="">Select your primary income source</option>
                    <option value="employment">Employment</option>
                    <option value="self_employed">Self-Employed</option>
                    <option value="business_owner">Business Owner</option>
                    <option value="freelance">Freelance</option>
                    <option value="investments">Investments</option>
                    <option value="other">Other</option>
                  </select>
                  {validationErrors.primary_income_source && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.primary_income_source}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Industry *
                  </label>
                  <select
                    name="industry"
                    value={formData.industry}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.industry ? 'border-red-300' : 'border-gray-300'
                    }`}
                  >
                    <option value="">Select your industry</option>
                    {industries.map((industry) => (
                      <option key={industry.value} value={industry.value}>
                        {industry.label}
                      </option>
                    ))}
                  </select>
                  {validationErrors.industry && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.industry}</p>
                  )}
                </div>

                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    name="job_title"
                    value={formData.job_title}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.job_title ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter your job title"
                  />
                  {validationErrors.job_title && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.job_title}</p>
                  )}
                </div>
              </div>

              {formData.naics_code && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-base leading-relaxed text-blue-700">
                    <strong>NAICS Code:</strong> {formData.naics_code} - {industries.find(ind => ind.value === formData.industry)?.label}
                  </p>
                </div>
              )}
            </div>

            {/* Financial Status Section */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Financial Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Current Savings *
                  </label>
                  <input
                    type="number"
                    name="current_savings"
                    value={formData.current_savings}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.current_savings ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter your current savings"
                  />
                  {validationErrors.current_savings && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.current_savings}</p>
                  )}
                </div>

                <div>
                  <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                    Current Debt *
                  </label>
                  <input
                    type="number"
                    name="current_debt"
                    value={formData.current_debt}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationErrors.current_debt ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter your current debt"
                  />
                  {validationErrors.current_debt && (
                    <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.current_debt}</p>
                  )}
                </div>
              </div>

              <div className="mt-6">
                <label className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
                  Credit Score Range *
                </label>
                <select
                  name="credit_score_range"
                  value={formData.credit_score_range}
                  onChange={handleInputChange}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    validationErrors.credit_score_range ? 'border-red-300' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select credit score range</option>
                  <option value="300-579">300-579 (Poor)</option>
                  <option value="580-669">580-669 (Fair)</option>
                  <option value="670-739">670-739 (Good)</option>
                  <option value="740-799">740-799 (Very Good)</option>
                  <option value="800-850">800-850 (Excellent)</option>
                  <option value="unknown">I don't know</option>
                </select>
                {validationErrors.credit_score_range && (
                  <p className="text-red-500 text-base leading-relaxed mt-1">{validationErrors.credit_score_range}</p>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between pt-6">
              <button
                type="button"
                onClick={() => navigate('/onboarding/welcome')}
                className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-8 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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

export default ProfileStep; 