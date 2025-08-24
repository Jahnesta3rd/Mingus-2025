import React, { useState, useEffect } from 'react';

const ProgressiveLeadForm = ({ onComplete, initialData = {} }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Basic Info
    email: initialData.email || '',
    firstName: initialData.firstName || '',
    lastName: initialData.lastName || '',
    phone: initialData.phone || '',
    currentSalary: initialData.currentSalary || '',
    location: initialData.location || '',
    
    // Detailed Profile
    industry: initialData.industry || '',
    role: initialData.role || '',
    education: initialData.education || '',
    yearsOfExperience: initialData.yearsOfExperience || '',
    companySize: initialData.companySize || '',
    
    // Career Goals
    targetSalary: initialData.targetSalary || '',
    careerGoals: initialData.careerGoals || [],
    preferredLocation: initialData.preferredLocation || '',
    skills: initialData.skills || [],
    
    // Preferences
    newsletter: initialData.newsletter || false,
    contactMethod: initialData.contactMethod || 'email',
    urgency: initialData.urgency || 'medium'
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);

  const totalSteps = 4;

  useEffect(() => {
    setProgress((currentStep / totalSteps) * 100);
  }, [currentStep]);

  const validateStep = (step) => {
    const newErrors = {};

    switch (step) {
      case 1:
        if (!formData.email) newErrors.email = 'Email is required';
        if (!formData.currentSalary) newErrors.currentSalary = 'Current salary is required';
        if (!formData.location) newErrors.location = 'Location is required';
        break;
      
      case 2:
        if (!formData.industry) newErrors.industry = 'Industry is required';
        if (!formData.role) newErrors.role = 'Current role is required';
        if (!formData.education) newErrors.education = 'Education level is required';
        break;
      
      case 3:
        if (!formData.targetSalary) newErrors.targetSalary = 'Target salary is required';
        if (formData.careerGoals.length === 0) newErrors.careerGoals = 'Please select at least one career goal';
        break;
      
      default:
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, totalSteps));
    }
  };

  const handleBack = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setIsSubmitting(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      onComplete?.(formData);
    } catch (error) {
      console.error('Form submission failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

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

  const renderStep1 = () => (
    <div className="form-step">
      <h3>Basic Information</h3>
      <p>Let's start with some basic details to personalize your experience.</p>
      
      <div className="form-grid">
        <div className="form-group">
          <label htmlFor="email">Email Address *</label>
          <input
            type="email"
            id="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            className={errors.email ? 'error' : ''}
            placeholder="Enter your email address"
          />
          {errors.email && <span className="error-message">{errors.email}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="firstName">First Name</label>
          <input
            type="text"
            id="firstName"
            value={formData.firstName}
            onChange={(e) => handleInputChange('firstName', e.target.value)}
            placeholder="Enter your first name"
          />
        </div>

        <div className="form-group">
          <label htmlFor="lastName">Last Name</label>
          <input
            type="text"
            id="lastName"
            value={formData.lastName}
            onChange={(e) => handleInputChange('lastName', e.target.value)}
            placeholder="Enter your last name"
          />
        </div>

        <div className="form-group">
          <label htmlFor="phone">Phone Number</label>
          <input
            type="tel"
            id="phone"
            value={formData.phone}
            onChange={(e) => handleInputChange('phone', e.target.value)}
            placeholder="Enter your phone number"
          />
        </div>

        <div className="form-group">
          <label htmlFor="currentSalary">Current Annual Salary *</label>
          <div className="input-with-prefix">
            <span className="prefix">$</span>
            <input
              type="number"
              id="currentSalary"
              value={formData.currentSalary}
              onChange={(e) => handleInputChange('currentSalary', e.target.value)}
              className={errors.currentSalary ? 'error' : ''}
              placeholder="Enter your current salary"
              min="0"
              step="1000"
            />
          </div>
          {errors.currentSalary && <span className="error-message">{errors.currentSalary}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="location">Location *</label>
          <select
            id="location"
            value={formData.location}
            onChange={(e) => handleInputChange('location', e.target.value)}
            className={errors.location ? 'error' : ''}
          >
            <option value="">Select your location</option>
            <option value="atlanta">Atlanta, GA</option>
            <option value="washington-dc">Washington, DC</option>
            <option value="new-york">New York, NY</option>
            <option value="los-angeles">Los Angeles, CA</option>
            <option value="chicago">Chicago, IL</option>
            <option value="houston">Houston, TX</option>
            <option value="phoenix">Phoenix, AZ</option>
            <option value="philadelphia">Philadelphia, PA</option>
            <option value="san-antonio">San Antonio, TX</option>
            <option value="san-diego">San Diego, CA</option>
            <option value="dallas">Dallas, TX</option>
            <option value="san-jose">San Jose, CA</option>
            <option value="austin">Austin, TX</option>
            <option value="jacksonville">Jacksonville, FL</option>
            <option value="fort-worth">Fort Worth, TX</option>
            <option value="columbus">Columbus, OH</option>
            <option value="charlotte">Charlotte, NC</option>
            <option value="san-francisco">San Francisco, CA</option>
            <option value="indianapolis">Indianapolis, IN</option>
            <option value="seattle">Seattle, WA</option>
            <option value="denver">Denver, CO</option>
            <option value="boston">Boston, MA</option>
            <option value="el-paso">El Paso, TX</option>
            <option value="detroit">Detroit, MI</option>
            <option value="nashville">Nashville, TN</option>
            <option value="portland">Portland, OR</option>
            <option value="memphis">Memphis, TN</option>
            <option value="oklahoma-city">Oklahoma City, OK</option>
            <option value="las-vegas">Las Vegas, NV</option>
            <option value="louisville">Louisville, KY</option>
            <option value="baltimore">Baltimore, MD</option>
            <option value="milwaukee">Milwaukee, WI</option>
            <option value="albuquerque">Albuquerque, NM</option>
            <option value="tucson">Tucson, AZ</option>
            <option value="fresno">Fresno, CA</option>
            <option value="sacramento">Sacramento, CA</option>
            <option value="mesa">Mesa, AZ</option>
            <option value="kansas-city">Kansas City, MO</option>
            <option value="long-beach">Long Beach, CA</option>
            <option value="colorado-springs">Colorado Springs, CO</option>
            <option value="raleigh">Raleigh, NC</option>
            <option value="miami">Miami, FL</option>
            <option value="virginia-beach">Virginia Beach, VA</option>
            <option value="omaha">Omaha, NE</option>
            <option value="oakland">Oakland, CA</option>
            <option value="minneapolis">Minneapolis, MN</option>
            <option value="tulsa">Tulsa, OK</option>
            <option value="arlington">Arlington, TX</option>
            <option value="tampa">Tampa, FL</option>
            <option value="new-orleans">New Orleans, LA</option>
            <option value="wichita">Wichita, KS</option>
            <option value="cleveland">Cleveland, OH</option>
            <option value="bakersfield">Bakersfield, CA</option>
            <option value="aurora">Aurora, CO</option>
            <option value="anaheim">Anaheim, CA</option>
            <option value="honolulu">Honolulu, HI</option>
            <option value="santa-ana">Santa Ana, CA</option>
            <option value="corpus-christi">Corpus Christi, TX</option>
            <option value="riverside">Riverside, CA</option>
            <option value="lexington">Lexington, KY</option>
            <option value="stockton">Stockton, CA</option>
            <option value="henderson">Henderson, NV</option>
            <option value="saint-paul">Saint Paul, MN</option>
            <option value="st-louis">St. Louis, MO</option>
            <option value="cincinnati">Cincinnati, OH</option>
            <option value="pittsburgh">Pittsburgh, PA</option>
            <option value="greensboro">Greensboro, NC</option>
            <option value="anchorage">Anchorage, AK</option>
            <option value="plano">Plano, TX</option>
            <option value="lincoln">Lincoln, NE</option>
            <option value="orlando">Orlando, FL</option>
            <option value="irvine">Irvine, CA</option>
            <option value="newark">Newark, NJ</option>
            <option value="durham">Durham, NC</option>
            <option value="chula-vista">Chula Vista, CA</option>
            <option value="toledo">Toledo, OH</option>
            <option value="fort-wayne">Fort Wayne, IN</option>
            <option value="st-petersburg">St. Petersburg, FL</option>
            <option value="laredo">Laredo, TX</option>
            <option value="jersey-city">Jersey City, NJ</option>
            <option value="chandler">Chandler, AZ</option>
            <option value="madison">Madison, WI</option>
            <option value="lubbock">Lubbock, TX</option>
            <option value="scottsdale">Scottsdale, AZ</option>
            <option value="reno">Reno, NV</option>
            <option value="buffalo">Buffalo, NY</option>
            <option value="gilbert">Gilbert, AZ</option>
            <option value="glendale">Glendale, AZ</option>
            <option value="north-las-vegas">North Las Vegas, NV</option>
            <option value="winston-salem">Winston-Salem, NC</option>
            <option value="chesapeake">Chesapeake, VA</option>
            <option value="norfolk">Norfolk, VA</option>
            <option value="fremont">Fremont, CA</option>
            <option value="garland">Garland, TX</option>
            <option value="irving">Irving, TX</option>
            <option value="hialeah">Hialeah, FL</option>
            <option value="richmond">Richmond, VA</option>
            <option value="boise">Boise, ID</option>
            <option value="spokane">Spokane, WA</option>
            <option value="baton-rouge">Baton Rouge, LA</option>
            <option value="tacoma">Tacoma, WA</option>
            <option value="san-bernardino">San Bernardino, CA</option>
            <option value="grand-rapids">Grand Rapids, MI</option>
            <option value="huntsville">Huntsville, AL</option>
            <option value="salt-lake-city">Salt Lake City, UT</option>
            <option value="frisco">Frisco, TX</option>
            <option value="cary">Cary, NC</option>
            <option value="yonkers">Yonkers, NY</option>
            <option value="amarillo">Amarillo, TX</option>
            <option value="santa-clarita">Santa Clarita, CA</option>
            <option value="glendale-ca">Glendale, CA</option>
            <option value="mobile">Mobile, AL</option>
            <option value="grand-prairie">Grand Prairie, TX</option>
            <option value="overland-park">Overland Park, KS</option>
            <option value="cape-coral">Cape Coral, FL</option>
            <option value="des-moines">Des Moines, IA</option>
            <option value="mckinney">McKinney, TX</option>
            <option value="modesto">Modesto, CA</option>
            <option value="fayetteville">Fayetteville, NC</option>
            <option value="tacoma-wa">Tacoma, WA</option>
            <option value="oxnard">Oxnard, CA</option>
            <option value="fontana">Fontana, CA</option>
            <option value="columbus-ga">Columbus, GA</option>
            <option value="montgomery">Montgomery, AL</option>
            <option value="moreno-valley">Moreno Valley, CA</option>
            <option value="shreveport">Shreveport, LA</option>
            <option value="aurora-il">Aurora, IL</option>
            <option value="yonkers-ny">Yonkers, NY</option>
            <option value="akron">Akron, OH</option>
            <option value="huntington-beach">Huntington Beach, CA</option>
            <option value="little-rock">Little Rock, AR</option>
            <option value="augusta">Augusta, GA</option>
            <option value="amarillo-tx">Amarillo, TX</option>
            <option value="glendale-az">Glendale, AZ</option>
            <option value="grand-rapids-mi">Grand Rapids, MI</option>
            <option value="tallahassee">Tallahassee, FL</option>
            <option value="huntsville-al">Huntsville, AL</option>
            <option value="grand-prairie-tx">Grand Prairie, TX</option>
            <option value="overland-park-ks">Overland Park, KS</option>
            <option value="cape-coral-fl">Cape Coral, FL</option>
            <option value="tempe">Tempe, AZ</option>
            <option value="mckinney-tx">McKinney, TX</option>
            <option value="mobile-al">Mobile, AL</option>
            <option value="cary-nc">Cary, NC</option>
            <option value="shreveport-la">Shreveport, LA</option>
            <option value="frisco-tx">Frisco, TX</option>
            <option value="rochester">Rochester, NY</option>
            <option value="winston-salem-nc">Winston-Salem, NC</option>
            <option value="santa-clarita-ca">Santa Clarita, CA</option>
            <option value="fayetteville-nc">Fayetteville, NC</option>
            <option value="anchorage-ak">Anchorage, AK</option>
            <option value="knoxville">Knoxville, TN</option>
            <option value="aurora-il-2">Aurora, IL</option>
            <option value="bakersfield-ca">Bakersfield, CA</option>
            <option value="new-orleans-la">New Orleans, LA</option>
            <option value="cleveland-oh">Cleveland, OH</option>
            <option value="tampa-fl">Tampa, FL</option>
            <option value="tulsa-ok">Tulsa, OK</option>
            <option value="arlington-tx">Arlington, TX</option>
            <option value="wichita-ks">Wichita, KS</option>
            <option value="minneapolis-mn">Minneapolis, MN</option>
            <option value="oakland-ca">Oakland, CA</option>
            <option value="omaha-ne">Omaha, NE</option>
            <option value="virginia-beach-va">Virginia Beach, VA</option>
            <option value="miami-fl">Miami, FL</option>
            <option value="raleigh-nc">Raleigh, NC</option>
            <option value="colorado-springs-co">Colorado Springs, CO</option>
            <option value="long-beach-ca">Long Beach, CA</option>
            <option value="kansas-city-mo">Kansas City, MO</option>
            <option value="mesa-az">Mesa, AZ</option>
            <option value="sacramento-ca">Sacramento, CA</option>
            <option value="fresno-ca">Fresno, CA</option>
            <option value="tucson-az">Tucson, AZ</option>
            <option value="albuquerque-nm">Albuquerque, NM</option>
            <option value="milwaukee-wi">Milwaukee, WI</option>
            <option value="baltimore-md">Baltimore, MD</option>
            <option value="louisville-ky">Louisville, KY</option>
            <option value="las-vegas-nv">Las Vegas, NV</option>
            <option value="oklahoma-city-ok">Oklahoma City, OK</option>
            <option value="memphis-tn">Memphis, TN</option>
            <option value="portland-or">Portland, OR</option>
            <option value="nashville-tn">Nashville, TN</option>
            <option value="detroit-mi">Detroit, MI</option>
            <option value="el-paso-tx">El Paso, TX</option>
            <option value="boston-ma">Boston, MA</option>
            <option value="seattle-wa">Seattle, WA</option>
            <option value="indianapolis-in">Indianapolis, IN</option>
            <option value="san-francisco-ca">San Francisco, CA</option>
            <option value="charlotte-nc">Charlotte, NC</option>
            <option value="columbus-oh">Columbus, OH</option>
            <option value="fort-worth-tx">Fort Worth, TX</option>
            <option value="jacksonville-fl">Jacksonville, FL</option>
            <option value="austin-tx">Austin, TX</option>
            <option value="san-jose-ca">San Jose, CA</option>
            <option value="dallas-tx">Dallas, TX</option>
            <option value="san-diego-ca">San Diego, CA</option>
            <option value="san-antonio-tx">San Antonio, TX</option>
            <option value="philadelphia-pa">Philadelphia, PA</option>
            <option value="phoenix-az">Phoenix, AZ</option>
            <option value="houston-tx">Houston, TX</option>
            <option value="chicago-il">Chicago, IL</option>
            <option value="los-angeles-ca">Los Angeles, CA</option>
            <option value="new-york-ny">New York, NY</option>
            <option value="washington-dc">Washington, DC</option>
            <option value="remote">Remote</option>
            <option value="other">Other</option>
          </select>
          {errors.location && <span className="error-message">{errors.location}</span>}
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="form-step">
      <h3>Professional Background</h3>
      <p>Tell us about your current role and experience.</p>
      
      <div className="form-grid">
        <div className="form-group">
          <label htmlFor="industry">Industry *</label>
          <select
            id="industry"
            value={formData.industry}
            onChange={(e) => handleInputChange('industry', e.target.value)}
            className={errors.industry ? 'error' : ''}
          >
            <option value="">Select your industry</option>
            <option value="technology">Technology</option>
            <option value="healthcare">Healthcare</option>
            <option value="finance">Finance</option>
            <option value="education">Education</option>
            <option value="government">Government</option>
            <option value="non-profit">Non-Profit</option>
            <option value="manufacturing">Manufacturing</option>
            <option value="retail">Retail</option>
            <option value="consulting">Consulting</option>
            <option value="marketing">Marketing</option>
            <option value="legal">Legal</option>
            <option value="real-estate">Real Estate</option>
            <option value="media">Media</option>
            <option value="other">Other</option>
          </select>
          {errors.industry && <span className="error-message">{errors.industry}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="role">Current Role *</label>
          <input
            type="text"
            id="role"
            value={formData.role}
            onChange={(e) => handleInputChange('role', e.target.value)}
            className={errors.role ? 'error' : ''}
            placeholder="e.g., Software Engineer, Marketing Manager"
          />
          {errors.role && <span className="error-message">{errors.role}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="education">Education Level *</label>
          <select
            id="education"
            value={formData.education}
            onChange={(e) => handleInputChange('education', e.target.value)}
            className={errors.education ? 'error' : ''}
          >
            <option value="">Select education level</option>
            <option value="high-school">High School</option>
            <option value="associate">Associate's Degree</option>
            <option value="bachelor">Bachelor's Degree</option>
            <option value="master">Master's Degree</option>
            <option value="doctorate">Doctorate</option>
            <option value="certification">Professional Certification</option>
          </select>
          {errors.education && <span className="error-message">{errors.education}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="yearsOfExperience">Years of Experience</label>
          <input
            type="number"
            id="yearsOfExperience"
            value={formData.yearsOfExperience}
            onChange={(e) => handleInputChange('yearsOfExperience', e.target.value)}
            placeholder="Enter years of experience"
            min="0"
            max="50"
          />
        </div>

        <div className="form-group">
          <label htmlFor="companySize">Company Size</label>
          <select
            id="companySize"
            value={formData.companySize}
            onChange={(e) => handleInputChange('companySize', e.target.value)}
          >
            <option value="">Select company size</option>
            <option value="1-10">1-10 employees</option>
            <option value="11-50">11-50 employees</option>
            <option value="51-200">51-200 employees</option>
            <option value="201-500">201-500 employees</option>
            <option value="501-1000">501-1000 employees</option>
            <option value="1000+">1000+ employees</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="form-step">
      <h3>Career Goals</h3>
      <p>What are your career aspirations and goals?</p>
      
      <div className="form-grid">
        <div className="form-group">
          <label htmlFor="targetSalary">Target Annual Salary *</label>
          <div className="input-with-prefix">
            <span className="prefix">$</span>
            <input
              type="number"
              id="targetSalary"
              value={formData.targetSalary}
              onChange={(e) => handleInputChange('targetSalary', e.target.value)}
              className={errors.targetSalary ? 'error' : ''}
              placeholder="Enter your target salary"
              min="0"
              step="1000"
            />
          </div>
          {errors.targetSalary && <span className="error-message">{errors.targetSalary}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="preferredLocation">Preferred Location</label>
          <select
            id="preferredLocation"
            value={formData.preferredLocation}
            onChange={(e) => handleInputChange('preferredLocation', e.target.value)}
          >
            <option value="">Keep current location</option>
            <option value="remote">Remote</option>
            <option value="new-york">New York, NY</option>
            <option value="san-francisco">San Francisco, CA</option>
            <option value="washington-dc">Washington, DC</option>
            <option value="los-angeles">Los Angeles, CA</option>
            <option value="chicago">Chicago, IL</option>
            <option value="seattle">Seattle, WA</option>
            <option value="austin">Austin, TX</option>
            <option value="denver">Denver, CO</option>
            <option value="boston">Boston, MA</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="form-group full-width">
          <label>Career Goals (Select all that apply) *</label>
          <div className="checkbox-grid">
            {careerGoalOptions.map((goal) => (
              <label key={goal} className="checkbox-item">
                <input
                  type="checkbox"
                  checked={formData.careerGoals.includes(goal)}
                  onChange={(e) => {
                    const newGoals = e.target.checked
                      ? [...formData.careerGoals, goal]
                      : formData.careerGoals.filter(g => g !== goal);
                    handleInputChange('careerGoals', newGoals);
                  }}
                />
                <span>{goal}</span>
              </label>
            ))}
          </div>
          {errors.careerGoals && <span className="error-message">{errors.careerGoals}</span>}
        </div>

        <div className="form-group full-width">
          <label>Skills You Want to Develop (Select all that apply)</label>
          <div className="checkbox-grid">
            {skillOptions.map((skill) => (
              <label key={skill} className="checkbox-item">
                <input
                  type="checkbox"
                  checked={formData.skills.includes(skill)}
                  onChange={(e) => {
                    const newSkills = e.target.checked
                      ? [...formData.skills, skill]
                      : formData.skills.filter(s => s !== skill);
                    handleInputChange('skills', newSkills);
                  }}
                />
                <span>{skill}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="form-step">
      <h3>Preferences</h3>
      <p>How would you like us to contact you?</p>
      
      <div className="form-grid">
        <div className="form-group">
          <label htmlFor="contactMethod">Preferred Contact Method</label>
          <select
            id="contactMethod"
            value={formData.contactMethod}
            onChange={(e) => handleInputChange('contactMethod', e.target.value)}
          >
            <option value="email">Email</option>
            <option value="phone">Phone</option>
            <option value="text">Text Message</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="urgency">How urgent is your career transition?</label>
          <select
            id="urgency"
            value={formData.urgency}
            onChange={(e) => handleInputChange('urgency', e.target.value)}
          >
            <option value="low">Not urgent (6+ months)</option>
            <option value="medium">Somewhat urgent (3-6 months)</option>
            <option value="high">Very urgent (1-3 months)</option>
            <option value="immediate">Immediate (within 1 month)</option>
          </select>
        </div>

        <div className="form-group full-width">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={formData.newsletter}
              onChange={(e) => handleInputChange('newsletter', e.target.checked)}
            />
            <span>Subscribe to our newsletter for career insights and opportunities</span>
          </label>
        </div>
      </div>

      <div className="form-summary">
        <h4>Summary</h4>
        <div className="summary-grid">
          <div className="summary-item">
            <strong>Email:</strong> {formData.email}
          </div>
          <div className="summary-item">
            <strong>Current Salary:</strong> ${formData.currentSalary?.toLocaleString()}
          </div>
          <div className="summary-item">
            <strong>Industry:</strong> {formData.industry}
          </div>
          <div className="summary-item">
            <strong>Target Salary:</strong> ${formData.targetSalary?.toLocaleString()}
          </div>
          <div className="summary-item">
            <strong>Career Goals:</strong> {formData.careerGoals.length} selected
          </div>
          <div className="summary-item">
            <strong>Skills:</strong> {formData.skills.length} selected
          </div>
        </div>
      </div>
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return renderStep1();
      case 2:
        return renderStep2();
      case 3:
        return renderStep3();
      case 4:
        return renderStep4();
      default:
        return renderStep1();
    }
  };

  return (
    <div className="progressive-lead-form">
      <div className="form-header">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="step-indicators">
          {Array.from({ length: totalSteps }, (_, i) => (
            <div 
              key={i + 1} 
              className={`step-indicator ${i + 1 <= currentStep ? 'active' : ''}`}
            >
              {i + 1}
            </div>
          ))}
        </div>
      </div>

      <div className="form-content">
        {renderCurrentStep()}
      </div>

      <div className="form-actions">
        {currentStep > 1 && (
          <button 
            type="button" 
            onClick={handleBack}
            className="btn-secondary"
          >
            Back
          </button>
        )}
        
        {currentStep < totalSteps ? (
          <button 
            type="button" 
            onClick={handleNext}
            className="btn-primary"
          >
            Next
          </button>
        ) : (
          <button 
            type="button" 
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="btn-primary"
          >
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </button>
        )}
      </div>

      <div className="form-footer">
        <p>
          By submitting this form, you agree to our{' '}
          <a href="/privacy">Privacy Policy</a> and{' '}
          <a href="/terms">Terms of Service</a>
        </p>
      </div>
    </div>
  );
};

export default ProgressiveLeadForm; 