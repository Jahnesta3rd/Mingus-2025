import React, { useState } from 'react';
import { BasicLeadInfo } from '../../types/leadCapture';

interface BasicInfoStepProps {
  onComplete: (info: BasicLeadInfo) => void;
  initialData?: Partial<BasicLeadInfo>;
}

const BasicInfoStep: React.FC<BasicInfoStepProps> = ({
  onComplete,
  initialData = {}
}) => {
  const [formData, setFormData] = useState<Partial<BasicLeadInfo>>({
    email: initialData.email || '',
    currentSalary: initialData.currentSalary || 0,
    location: initialData.location || '',
    firstName: initialData.firstName || '',
    lastName: initialData.lastName || '',
    phone: initialData.phone || ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.currentSalary || formData.currentSalary <= 0) {
      newErrors.currentSalary = 'Please enter your current salary';
    }

    if (!formData.location) {
      newErrors.location = 'Location is required';
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
      
      onComplete(formData as BasicLeadInfo);
    } catch (error) {
      console.error('Failed to submit basic info:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof BasicLeadInfo, value: any) => {
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

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4" className="text-2xl font-semibold text-gray-800 mb-4">
          Let's Get Started
        </h2>
        <p className="text-lg text-gray-600">
          Share some basic information to unlock your personalized salary insights
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Name Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="firstName" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
              First Name
            </label>
            <input
              type="text"
              id="firstName"
              value={formData.firstName}
              onChange={(e) => handleInputChange('firstName', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your first name"
            />
          </div>
          <div>
            <label htmlFor="lastName" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
              Last Name
            </label>
            <input
              type="text"
              id="lastName"
              value={formData.lastName}
              onChange={(e) => handleInputChange('lastName', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your last name"
            />
          </div>
        </div>

        {/* Email Field */}
        <div>
          <label htmlFor="email" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Email Address <span className="text-red-500">*</span>
          </label>
          <input
            type="email"
            id="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.email ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter your email address"
            required
          />
          {errors.email && (
            <p className="mt-1 text-base leading-relaxed text-red-600">{errors.email}</p>
          )}
        </div>

        {/* Phone Field */}
        <div>
          <label htmlFor="phone" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Phone Number (Optional)
          </label>
          <input
            type="tel"
            id="phone"
            value={formData.phone}
            onChange={(e) => handleInputChange('phone', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter your phone number"
          />
        </div>

        {/* Current Salary Field */}
        <div>
          <label htmlFor="currentSalary" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Current Annual Salary <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <span className="absolute left-3 top-3 text-gray-500">$</span>
            <input
              type="number"
              id="currentSalary"
              value={formData.currentSalary || ''}
              onChange={(e) => handleInputChange('currentSalary', parseInt(e.target.value) || 0)}
              className={`w-full pl-8 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.currentSalary ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter your current salary"
              min="0"
              step="1000"
              required
            />
          </div>
          {errors.currentSalary && (
            <p className="mt-1 text-base leading-relaxed text-red-600">{errors.currentSalary}</p>
          )}
          <p className="mt-1 text-base leading-relaxed text-gray-500">
            This helps us provide accurate salary comparisons
          </p>
        </div>

        {/* Location Field */}
        <div>
          <label htmlFor="location" className="block text-base leading-relaxed font-medium text-gray-700 mb-2">
            Location <span className="text-red-500">*</span>
          </label>
          <select
            id="location"
            value={formData.location}
            onChange={(e) => handleInputChange('location', e.target.value)}
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.location ? 'border-red-500' : 'border-gray-300'
            }`}
            required
          >
            <option value="">Select your location</option>
            <option value="Atlanta, GA">Atlanta, GA</option>
            <option value="Washington, DC">Washington, DC</option>
            <option value="New York, NY">New York, NY</option>
            <option value="Los Angeles, CA">Los Angeles, CA</option>
            <option value="Chicago, IL">Chicago, IL</option>
            <option value="Houston, TX">Houston, TX</option>
            <option value="Phoenix, AZ">Phoenix, AZ</option>
            <option value="Philadelphia, PA">Philadelphia, PA</option>
            <option value="San Antonio, TX">San Antonio, TX</option>
            <option value="San Diego, CA">San Diego, CA</option>
            <option value="Dallas, TX">Dallas, TX</option>
            <option value="San Jose, CA">San Jose, CA</option>
            <option value="Austin, TX">Austin, TX</option>
            <option value="Jacksonville, FL">Jacksonville, FL</option>
            <option value="Fort Worth, TX">Fort Worth, TX</option>
            <option value="Columbus, OH">Columbus, OH</option>
            <option value="Charlotte, NC">Charlotte, NC</option>
            <option value="San Francisco, CA">San Francisco, CA</option>
            <option value="Indianapolis, IN">Indianapolis, IN</option>
            <option value="Seattle, WA">Seattle, WA</option>
            <option value="Denver, CO">Denver, CO</option>
            <option value="Boston, MA">Boston, MA</option>
            <option value="El Paso, TX">El Paso, TX</option>
            <option value="Detroit, MI">Detroit, MI</option>
            <option value="Nashville, TN">Nashville, TN</option>
            <option value="Portland, OR">Portland, OR</option>
            <option value="Memphis, TN">Memphis, TN</option>
            <option value="Oklahoma City, OK">Oklahoma City, OK</option>
            <option value="Las Vegas, NV">Las Vegas, NV</option>
            <option value="Louisville, KY">Louisville, KY</option>
            <option value="Baltimore, MD">Baltimore, MD</option>
            <option value="Milwaukee, WI">Milwaukee, WI</option>
            <option value="Albuquerque, NM">Albuquerque, NM</option>
            <option value="Tucson, AZ">Tucson, AZ</option>
            <option value="Fresno, CA">Fresno, CA</option>
            <option value="Sacramento, CA">Sacramento, CA</option>
            <option value="Mesa, AZ">Mesa, AZ</option>
            <option value="Kansas City, MO">Kansas City, MO</option>
            <option value="Atlanta, GA">Atlanta, GA</option>
            <option value="Long Beach, CA">Long Beach, CA</option>
            <option value="Colorado Springs, CO">Colorado Springs, CO</option>
            <option value="Raleigh, NC">Raleigh, NC</option>
            <option value="Miami, FL">Miami, FL</option>
            <option value="Virginia Beach, VA">Virginia Beach, VA</option>
            <option value="Omaha, NE">Omaha, NE</option>
            <option value="Oakland, CA">Oakland, CA</option>
            <option value="Minneapolis, MN">Minneapolis, MN</option>
            <option value="Tulsa, OK">Tulsa, OK</option>
            <option value="Arlington, TX">Arlington, TX</option>
            <option value="Tampa, FL">Tampa, FL</option>
            <option value="New Orleans, LA">New Orleans, LA</option>
            <option value="Wichita, KS">Wichita, KS</option>
            <option value="Cleveland, OH">Cleveland, OH</option>
            <option value="Bakersfield, CA">Bakersfield, CA</option>
            <option value="Aurora, CO">Aurora, CO</option>
            <option value="Anaheim, CA">Anaheim, CA</option>
            <option value="Honolulu, HI">Honolulu, HI</option>
            <option value="Santa Ana, CA">Santa Ana, CA</option>
            <option value="Corpus Christi, TX">Corpus Christi, TX</option>
            <option value="Riverside, CA">Riverside, CA</option>
            <option value="Lexington, KY">Lexington, KY</option>
            <option value="Stockton, CA">Stockton, CA</option>
            <option value="Henderson, NV">Henderson, NV</option>
            <option value="Saint Paul, MN">Saint Paul, MN</option>
            <option value="St. Louis, MO">St. Louis, MO</option>
            <option value="Cincinnati, OH">Cincinnati, OH</option>
            <option value="Pittsburgh, PA">Pittsburgh, PA</option>
            <option value="Greensboro, NC">Greensboro, NC</option>
            <option value="Anchorage, AK">Anchorage, AK</option>
            <option value="Plano, TX">Plano, TX</option>
            <option value="Lincoln, NE">Lincoln, NE</option>
            <option value="Orlando, FL">Orlando, FL</option>
            <option value="Irvine, CA">Irvine, CA</option>
            <option value="Newark, NJ">Newark, NJ</option>
            <option value="Durham, NC">Durham, NC</option>
            <option value="Chula Vista, CA">Chula Vista, CA</option>
            <option value="Toledo, OH">Toledo, OH</option>
            <option value="Fort Wayne, IN">Fort Wayne, IN</option>
            <option value="St. Petersburg, FL">St. Petersburg, FL</option>
            <option value="Laredo, TX">Laredo, TX</option>
            <option value="Jersey City, NJ">Jersey City, NJ</option>
            <option value="Chandler, AZ">Chandler, AZ</option>
            <option value="Madison, WI">Madison, WI</option>
            <option value="Lubbock, TX">Lubbock, TX</option>
            <option value="Scottsdale, AZ">Scottsdale, AZ</option>
            <option value="Reno, NV">Reno, NV</option>
            <option value="Buffalo, NY">Buffalo, NY</option>
            <option value="Gilbert, AZ">Gilbert, AZ</option>
            <option value="Glendale, AZ">Glendale, AZ</option>
            <option value="North Las Vegas, NV">North Las Vegas, NV</option>
            <option value="Winston-Salem, NC">Winston-Salem, NC</option>
            <option value="Chesapeake, VA">Chesapeake, VA</option>
            <option value="Norfolk, VA">Norfolk, VA</option>
            <option value="Fremont, CA">Fremont, CA</option>
            <option value="Garland, TX">Garland, TX</option>
            <option value="Irving, TX">Irving, TX</option>
            <option value="Hialeah, FL">Hialeah, FL</option>
            <option value="Richmond, VA">Richmond, VA</option>
            <option value="Boise, ID">Boise, ID</option>
            <option value="Spokane, WA">Spokane, WA</option>
            <option value="Baton Rouge, LA">Baton Rouge, LA</option>
            <option value="Tacoma, WA">Tacoma, WA</option>
            <option value="San Bernardino, CA">San Bernardino, CA</option>
            <option value="Grand Rapids, MI">Grand Rapids, MI</option>
            <option value="Huntsville, AL">Huntsville, AL</option>
            <option value="Salt Lake City, UT">Salt Lake City, UT</option>
            <option value="Frisco, TX">Frisco, TX</option>
            <option value="Cary, NC">Cary, NC</option>
            <option value="Yonkers, NY">Yonkers, NY</option>
            <option value="Amarillo, TX">Amarillo, TX</option>
            <option value="Santa Clarita, CA">Santa Clarita, CA</option>
            <option value="Glendale, CA">Glendale, CA</option>
            <option value="Mobile, AL">Mobile, AL</option>
            <option value="Grand Prairie, TX">Grand Prairie, TX</option>
            <option value="Overland Park, KS">Overland Park, KS</option>
            <option value="Cape Coral, FL">Cape Coral, FL</option>
            <option value="Des Moines, IA">Des Moines, IA</option>
            <option value="McKinney, TX">McKinney, TX</option>
            <option value="Modesto, CA">Modesto, CA</option>
            <option value="Fayetteville, NC">Fayetteville, NC</option>
            <option value="Tacoma, WA">Tacoma, WA</option>
            <option value="Oxnard, CA">Oxnard, CA</option>
            <option value="Fontana, CA">Fontana, CA</option>
            <option value="Columbus, GA">Columbus, GA</option>
            <option value="Montgomery, AL">Montgomery, AL</option>
            <option value="Moreno Valley, CA">Moreno Valley, CA</option>
            <option value="Shreveport, LA">Shreveport, LA</option>
            <option value="Aurora, IL">Aurora, IL</option>
            <option value="Yonkers, NY">Yonkers, NY</option>
            <option value="Akron, OH">Akron, OH</option>
            <option value="Huntington Beach, CA">Huntington Beach, CA</option>
            <option value="Little Rock, AR">Little Rock, AR</option>
            <option value="Augusta, GA">Augusta, GA</option>
            <option value="Amarillo, TX">Amarillo, TX</option>
            <option value="Glendale, AZ">Glendale, AZ</option>
            <option value="Grand Rapids, MI">Grand Rapids, MI</option>
            <option value="Tallahassee, FL">Tallahassee, FL</option>
            <option value="Huntsville, AL">Huntsville, AL</option>
            <option value="Grand Prairie, TX">Grand Prairie, TX</option>
            <option value="Overland Park, KS">Overland Park, KS</option>
            <option value="Cape Coral, FL">Cape Coral, FL</option>
            <option value="Tempe, AZ">Tempe, AZ</option>
            <option value="McKinney, TX">McKinney, TX</option>
            <option value="Mobile, AL">Mobile, AL</option>
            <option value="Cary, NC">Cary, NC</option>
            <option value="Shreveport, LA">Shreveport, LA</option>
            <option value="Frisco, TX">Frisco, TX</option>
            <option value="Rochester, NY">Rochester, NY</option>
            <option value="Winston-Salem, NC">Winston-Salem, NC</option>
            <option value="Santa Clarita, CA">Santa Clarita, CA</option>
            <option value="Fayetteville, NC">Fayetteville, NC</option>
            <option value="Anchorage, AK">Anchorage, AK</option>
            <option value="Knoxville, TN">Knoxville, TN</option>
            <option value="Aurora, IL">Aurora, IL</option>
            <option value="Bakersfield, CA">Bakersfield, CA</option>
            <option value="New Orleans, LA">New Orleans, LA</option>
            <option value="Cleveland, OH">Cleveland, OH</option>
            <option value="Tampa, FL">Tampa, FL</option>
            <option value="Tulsa, OK">Tulsa, OK</option>
            <option value="Arlington, TX">Arlington, TX</option>
            <option value="Wichita, KS">Wichita, KS</option>
            <option value="Minneapolis, MN">Minneapolis, MN</option>
            <option value="Oakland, CA">Oakland, CA</option>
            <option value="Omaha, NE">Omaha, NE</option>
            <option value="Virginia Beach, VA">Virginia Beach, VA</option>
            <option value="Miami, FL">Miami, FL</option>
            <option value="Raleigh, NC">Raleigh, NC</option>
            <option value="Colorado Springs, CO">Colorado Springs, CO</option>
            <option value="Long Beach, CA">Long Beach, CA</option>
            <option value="Kansas City, MO">Kansas City, MO</option>
            <option value="Mesa, AZ">Mesa, AZ</option>
            <option value="Sacramento, CA">Sacramento, CA</option>
            <option value="Fresno, CA">Fresno, CA</option>
            <option value="Tucson, AZ">Tucson, AZ</option>
            <option value="Albuquerque, NM">Albuquerque, NM</option>
            <option value="Milwaukee, WI">Milwaukee, WI</option>
            <option value="Baltimore, MD">Baltimore, MD</option>
            <option value="Louisville, KY">Louisville, KY</option>
            <option value="Las Vegas, NV">Las Vegas, NV</option>
            <option value="Oklahoma City, OK">Oklahoma City, OK</option>
            <option value="Memphis, TN">Memphis, TN</option>
            <option value="Portland, OR">Portland, OR</option>
            <option value="Nashville, TN">Nashville, TN</option>
            <option value="Detroit, MI">Detroit, MI</option>
            <option value="El Paso, TX">El Paso, TX</option>
            <option value="Boston, MA">Boston, MA</option>
            <option value="Seattle, WA">Seattle, WA</option>
            <option value="Indianapolis, IN">Indianapolis, IN</option>
            <option value="San Francisco, CA">San Francisco, CA</option>
            <option value="Charlotte, NC">Charlotte, NC</option>
            <option value="Columbus, OH">Columbus, OH</option>
            <option value="Fort Worth, TX">Fort Worth, TX</option>
            <option value="Jacksonville, FL">Jacksonville, FL</option>
            <option value="Austin, TX">Austin, TX</option>
            <option value="San Jose, CA">San Jose, CA</option>
            <option value="Dallas, TX">Dallas, TX</option>
            <option value="San Diego, CA">San Diego, CA</option>
            <option value="San Antonio, TX">San Antonio, TX</option>
            <option value="Philadelphia, PA">Philadelphia, PA</option>
            <option value="Phoenix, AZ">Phoenix, AZ</option>
            <option value="Houston, TX">Houston, TX</option>
            <option value="Chicago, IL">Chicago, IL</option>
            <option value="Los Angeles, CA">Los Angeles, CA</option>
            <option value="New York, NY">New York, NY</option>
            <option value="Washington, DC">Washington, DC</option>
            <option value="Remote">Remote</option>
            <option value="Other">Other</option>
          </select>
          {errors.location && (
            <p className="mt-1 text-base leading-relaxed text-red-600">{errors.location}</p>
          )}
        </div>

        {/* Submit Button */}
        <div className="pt-6">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Processing...
              </div>
            ) : (
              'Continue to Detailed Profile'
            )}
          </button>
        </div>

        {/* Privacy Notice */}
        <div className="text-center">
          <p className="text-base leading-relaxed text-gray-500">
            By continuing, you agree to our{' '}
            <a text-blue-600 hover:underline className="text-blue-600 hover:underline font-medium text-base">
              Privacy Policy
            </a>{' '}
            and{' '}
            <a text-blue-600 hover:underline className="text-blue-600 hover:underline font-medium text-base">
              Terms of Service
            </a>
          </p>
        </div>
      </form>
    </div>
  );
};

export default BasicInfoStep; 