import React, { useState, useEffect, useCallback } from 'react';
import { createCareerChart, createProgressChart, createROIChart } from '../utils/chartUtils';

const CareerSimulator = ({ userData, onPredictionUpdate }) => {
  const [simulatorParams, setSimulatorParams] = useState({
    education: userData?.education || 'bachelor',
    skills: userData?.skills || [],
    location: userData?.location || 'atlanta',
    experience: userData?.experience || 'mid',
    networking: 50,
    certifications: 0,
    leadership: false,
    industry: userData?.industry || 'technology'
  });

  const [predictions, setPredictions] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [chartInstances, setChartInstances] = useState({});
  const [targetSalary] = useState(100000);

  // Available options
  const educationOptions = [
    { value: 'high-school', label: 'High School', multiplier: 0.8 },
    { value: 'some-college', label: 'Some College', multiplier: 0.9 },
    { value: 'bachelor', label: "Bachelor's Degree", multiplier: 1.0 },
    { value: 'master', label: "Master's Degree", multiplier: 1.2 },
    { value: 'doctorate', label: 'Doctorate', multiplier: 1.4 }
  ];

  const skillOptions = [
    { value: 'leadership', label: 'Leadership', impact: 0.15 },
    { value: 'data-analysis', label: 'Data Analysis', impact: 0.12 },
    { value: 'project-management', label: 'Project Management', impact: 0.10 },
    { value: 'programming', label: 'Programming', impact: 0.18 },
    { value: 'communication', label: 'Communication', impact: 0.08 },
    { value: 'strategic-thinking', label: 'Strategic Thinking', impact: 0.12 },
    { value: 'financial-analysis', label: 'Financial Analysis', impact: 0.14 },
    { value: 'marketing', label: 'Marketing', impact: 0.09 },
    { value: 'sales', label: 'Sales', impact: 0.11 },
    { value: 'operations', label: 'Operations', impact: 0.10 }
  ];

  const locationOptions = [
    { value: 'atlanta', label: 'Atlanta, GA', multiplier: 1.0 },
    { value: 'houston', label: 'Houston, TX', multiplier: 0.95 },
    { value: 'washington-dc', label: 'Washington, DC', multiplier: 1.15 },
    { value: 'dallas', label: 'Dallas, TX', multiplier: 1.05 },
    { value: 'new-york', label: 'New York, NY', multiplier: 1.25 },
    { value: 'philadelphia', label: 'Philadelphia, PA', multiplier: 1.05 },
    { value: 'chicago', label: 'Chicago, IL', multiplier: 1.1 },
    { value: 'charlotte', label: 'Charlotte, NC', multiplier: 0.9 },
    { value: 'miami', label: 'Miami, FL', multiplier: 0.95 },
    { value: 'baltimore', label: 'Baltimore, MD', multiplier: 1.0 },
    { value: 'san-francisco', label: 'San Francisco, CA', multiplier: 1.3 },
    { value: 'los-angeles', label: 'Los Angeles, CA', multiplier: 1.2 },
    { value: 'seattle', label: 'Seattle, WA', multiplier: 1.15 },
    { value: 'denver', label: 'Denver, CO', multiplier: 1.05 },
    { value: 'austin', label: 'Austin, TX', multiplier: 1.1 }
  ];

  const experienceOptions = [
    { value: 'entry', label: 'Entry Level (0-2 years)', multiplier: 0.7 },
    { value: 'mid', label: 'Mid Level (3-7 years)', multiplier: 1.0 },
    { value: 'senior', label: 'Senior Level (8+ years)', multiplier: 1.4 }
  ];

  const industryOptions = [
    { value: 'technology', label: 'Technology', multiplier: 1.2 },
    { value: 'healthcare', label: 'Healthcare', multiplier: 1.1 },
    { value: 'finance', label: 'Finance', multiplier: 1.15 },
    { value: 'education', label: 'Education', multiplier: 0.9 },
    { value: 'manufacturing', label: 'Manufacturing', multiplier: 1.0 },
    { value: 'retail', label: 'Retail', multiplier: 0.8 },
    { value: 'consulting', label: 'Consulting', multiplier: 1.1 },
    { value: 'government', label: 'Government', multiplier: 0.95 },
    { value: 'nonprofit', label: 'Non-Profit', multiplier: 0.85 },
    { value: 'media', label: 'Media & Entertainment', multiplier: 1.0 }
  ];

  // Calculate predictions based on current parameters
  const calculatePredictions = useCallback(async () => {
    setIsLoading(true);
    
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 800));

      const baseSalary = userData?.currentSalary || 75000;
      
      // Calculate multipliers
      const educationMultiplier = educationOptions.find(opt => opt.value === simulatorParams.education)?.multiplier || 1.0;
      const locationMultiplier = locationOptions.find(opt => opt.value === simulatorParams.location)?.multiplier || 1.0;
      const experienceMultiplier = experienceOptions.find(opt => opt.value === simulatorParams.experience)?.multiplier || 1.0;
      const industryMultiplier = industryOptions.find(opt => opt.value === simulatorParams.industry)?.multiplier || 1.0;

      // Calculate skill impact
      const skillImpact = simulatorParams.skills.reduce((total, skill) => {
        const skillData = skillOptions.find(opt => opt.value === skill);
        return total + (skillData?.impact || 0);
      }, 0);

      // Calculate networking impact (0-50% bonus)
      const networkingImpact = (simulatorParams.networking / 100) * 0.5;

      // Calculate certification impact
      const certificationImpact = simulatorParams.certifications * 0.05;

      // Calculate leadership impact
      const leadershipImpact = simulatorParams.leadership ? 0.2 : 0;

      // Calculate total multiplier
      const totalMultiplier = educationMultiplier * locationMultiplier * experienceMultiplier * 
                             industryMultiplier * (1 + skillImpact + networkingImpact + 
                             certificationImpact + leadershipImpact);

      // Calculate predicted salaries
      const predictedSalary1yr = Math.round(baseSalary * totalMultiplier);
      const predictedSalary3yr = Math.round(predictedSalary1yr * 1.15);
      const predictedSalary5yr = Math.round(predictedSalary3yr * 1.2);

      // Calculate career path data
      const careerPath = generateCareerPath(predictedSalary1yr, targetSalary);
      
      // Calculate ROI data
      const roiData = calculateROI(simulatorParams);

      const predictionData = {
        currentSalary: baseSalary,
        predictedSalary1yr,
        predictedSalary3yr,
        predictedSalary5yr,
        targetSalary,
        careerPath,
        roiData,
        parameters: simulatorParams,
        multipliers: {
          education: educationMultiplier,
          location: locationMultiplier,
          experience: experienceMultiplier,
          industry: industryMultiplier,
          skills: skillImpact,
          networking: networkingImpact,
          certifications: certificationImpact,
          leadership: leadershipImpact,
          total: totalMultiplier
        },
        progress: {
          current: baseSalary,
          target: targetSalary,
          percentage: Math.min((predictedSalary1yr / targetSalary) * 100, 100)
        }
      };

      setPredictions(predictionData);
      onPredictionUpdate?.(predictionData);

    } catch (error) {
      console.error('Error calculating predictions:', error);
    } finally {
      setIsLoading(false);
    }
  }, [simulatorParams, userData, targetSalary, onPredictionUpdate]);

  // Generate career path steps
  const generateCareerPath = (currentSalary, targetSalary) => {
    const steps = [];
    let current = currentSalary;
    let year = 1;

    while (current < targetSalary && year <= 10) {
      const growthRate = year <= 3 ? 0.15 : 0.08;
      const nextSalary = Math.round(current * (1 + growthRate));
      
      steps.push({
        year,
        salary: nextSalary,
        growth: Math.round((nextSalary - current) / current * 100),
        milestone: nextSalary >= targetSalary ? 'Target Reached!' : null
      });

      current = nextSalary;
      year++;
    }

    return steps;
  };

  // Calculate ROI for investments
  const calculateROI = (params) => {
    const investments = [];
    let totalInvestment = 0;

    // Education investment
    if (params.education === 'master') {
      investments.push({
        name: "Master's Degree",
        cost: 50000,
        return: 15000,
        timeframe: '2 years',
        roi: 30
      });
      totalInvestment += 50000;
    } else if (params.education === 'doctorate') {
      investments.push({
        name: 'Doctorate',
        cost: 80000,
        return: 25000,
        timeframe: '4 years',
        roi: 31
      });
      totalInvestment += 80000;
    }

    // Certification investment
    if (params.certifications > 0) {
      const certCost = params.certifications * 2000;
      const certReturn = params.certifications * 3000;
      investments.push({
        name: `${params.certifications} Certification(s)`,
        cost: certCost,
        return: certReturn,
        timeframe: '6 months',
        roi: Math.round((certReturn / certCost) * 100)
      });
      totalInvestment += certCost;
    }

    // Skills investment
    if (params.skills.length > 0) {
      const skillCost = params.skills.length * 1500;
      const skillReturn = params.skills.length * 2500;
      investments.push({
        name: 'Skill Development',
        cost: skillCost,
        return: skillReturn,
        timeframe: '1 year',
        roi: Math.round((skillReturn / skillCost) * 100)
      });
      totalInvestment += skillCost;
    }

    return {
      investments,
      totalInvestment,
      totalReturn: investments.reduce((sum, inv) => sum + inv.return, 0),
      averageROI: investments.length > 0 ? 
        Math.round(investments.reduce((sum, inv) => sum + inv.roi, 0) / investments.length) : 0
    };
  };

  // Handle parameter changes
  const handleParamChange = (param, value) => {
    setSimulatorParams(prev => ({
      ...prev,
      [param]: value
    }));
  };

  // Handle skill toggle
  const handleSkillToggle = (skill) => {
    setSimulatorParams(prev => ({
      ...prev,
      skills: prev.skills.includes(skill) 
        ? prev.skills.filter(s => s !== skill)
        : [...prev.skills, skill]
    }));
  };

  // Update predictions when parameters change
  useEffect(() => {
    calculatePredictions();
  }, [calculatePredictions]);

  // Render charts when predictions change
  useEffect(() => {
    if (predictions) {
      renderCharts();
    }
  }, [predictions]);

  // Render all charts
  const renderCharts = () => {
    if (!predictions) return;

    // Career progression chart
    const careerChart = createCareerChart('career-progression-chart', {
      labels: predictions.careerPath.map(step => `Year ${step.year}`),
      data: predictions.careerPath.map(step => step.salary),
      target: targetSalary
    });

    // Progress chart
    const progressChart = createProgressChart('salary-progress-chart', {
      current: predictions.currentSalary,
      target: targetSalary,
      predicted: predictions.predictedSalary1yr
    });

    // ROI chart
    const roiChart = createROIChart('roi-chart', predictions.roiData);

    setChartInstances({
      career: careerChart,
      progress: progressChart,
      roi: roiChart
    });
  };

  // Cleanup charts on unmount
  useEffect(() => {
    return () => {
      Object.values(chartInstances).forEach(chart => {
        if (chart && chart.destroy) {
          chart.destroy();
        }
      });
    };
  }, []);

  if (isLoading) {
    return (
      <div className="career-simulator loading">
        <div className="loading-spinner"></div>
        <p>Calculating career predictions...</p>
      </div>
    );
  }

  return (
    <div className="career-simulator">
      <div className="simulator-header">
        <h2>Career Advancement Simulator</h2>
        <p>Adjust the parameters below to see how they impact your salary trajectory</p>
      </div>

      <div className="simulator-content">
        {/* Parameter Controls */}
        <div className="parameter-controls">
          <div className="control-group">
            <label>Education Level</label>
            <select 
              value={simulatorParams.education}
              onChange={(e) => handleParamChange('education', e.target.value)}
            >
              {educationOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Experience Level</label>
            <select 
              value={simulatorParams.experience}
              onChange={(e) => handleParamChange('experience', e.target.value)}
            >
              {experienceOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Location</label>
            <select 
              value={simulatorParams.location}
              onChange={(e) => handleParamChange('location', e.target.value)}
            >
              {locationOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Industry</label>
            <select 
              value={simulatorParams.industry}
              onChange={(e) => handleParamChange('industry', e.target.value)}
            >
              {industryOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Networking Investment: {simulatorParams.networking}%</label>
            <input 
              type="range" 
              min="0" 
              max="100" 
              value={simulatorParams.networking}
              onChange={(e) => handleParamChange('networking', parseInt(e.target.value))}
            />
            <span className="range-labels">
              <span>Minimal</span>
              <span>Active</span>
              <span>Intensive</span>
            </span>
          </div>

          <div className="control-group">
            <label>Certifications: {simulatorParams.certifications}</label>
            <input 
              type="range" 
              min="0" 
              max="5" 
              value={simulatorParams.certifications}
              onChange={(e) => handleParamChange('certifications', parseInt(e.target.value))}
            />
            <span className="range-labels">
              <span>0</span>
              <span>2-3</span>
              <span>5+</span>
            </span>
          </div>

          <div className="control-group">
            <label>
              <input 
                type="checkbox" 
                checked={simulatorParams.leadership}
                onChange={(e) => handleParamChange('leadership', e.target.checked)}
              />
              Leadership Experience
            </label>
          </div>
        </div>

        {/* Skills Selection */}
        <div className="skills-section">
          <h3>Key Skills</h3>
          <div className="skills-grid">
            {skillOptions.map(skill => (
              <label key={skill.value} className="skill-checkbox">
                <input 
                  type="checkbox" 
                  checked={simulatorParams.skills.includes(skill.value)}
                  onChange={() => handleSkillToggle(skill.value)}
                />
                <span className="skill-label">{skill.label}</span>
                <span className="skill-impact">+{Math.round(skill.impact * 100)}%</span>
              </label>
            ))}
          </div>
        </div>

        {/* Predictions Display */}
        {predictions && (
          <div className="predictions-display">
            <div className="salary-predictions">
              <h3>Salary Predictions</h3>
              <div className="prediction-cards">
                <div className="prediction-card">
                  <h4>1 Year</h4>
                  <div className="salary-amount">${predictions.predictedSalary1yr.toLocaleString()}</div>
                  <div className="salary-change">
                    +${(predictions.predictedSalary1yr - predictions.currentSalary).toLocaleString()}
                  </div>
                </div>
                <div className="prediction-card">
                  <h4>3 Years</h4>
                  <div className="salary-amount">${predictions.predictedSalary3yr.toLocaleString()}</div>
                  <div className="salary-change">
                    +${(predictions.predictedSalary3yr - predictions.currentSalary).toLocaleString()}
                  </div>
                </div>
                <div className="prediction-card">
                  <h4>5 Years</h4>
                  <div className="salary-amount">${predictions.predictedSalary5yr.toLocaleString()}</div>
                  <div className="salary-change">
                    +${(predictions.predictedSalary5yr - predictions.currentSalary).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Charts */}
            <div className="charts-section">
              <div className="chart-container">
                <h4>Career Progression</h4>
                <canvas id="career-progression-chart"></canvas>
              </div>
              
              <div className="chart-container">
                <h4>Progress to $100K</h4>
                <canvas id="salary-progress-chart"></canvas>
              </div>
              
              <div className="chart-container">
                <h4>Investment ROI</h4>
                <canvas id="roi-chart"></canvas>
              </div>
            </div>

            {/* Career Path Steps */}
            <div className="career-path">
              <h3>Path to $100K</h3>
              <div className="path-steps">
                {predictions.careerPath.slice(0, 5).map((step, index) => (
                  <div key={step.year} className={`path-step ${step.milestone ? 'milestone' : ''}`}>
                    <div className="step-number">{index + 1}</div>
                    <div className="step-content">
                      <h4>Year {step.year}</h4>
                      <div className="step-salary">${step.salary.toLocaleString()}</div>
                      <div className="step-growth">+{step.growth}% growth</div>
                      {step.milestone && <div className="milestone-badge">{step.milestone}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Investment Summary */}
            {predictions.roiData.investments.length > 0 && (
              <div className="investment-summary">
                <h3>Investment Summary</h3>
                <div className="investment-stats">
                  <div className="stat">
                    <span className="stat-label">Total Investment</span>
                    <span className="stat-value">${predictions.roiData.totalInvestment.toLocaleString()}</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Expected Return</span>
                    <span className="stat-value">${predictions.roiData.totalReturn.toLocaleString()}</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Average ROI</span>
                    <span className="stat-value">{predictions.roiData.averageROI}%</span>
                  </div>
                </div>
                
                <div className="investment-breakdown">
                  {predictions.roiData.investments.map((investment, index) => (
                    <div key={index} className="investment-item">
                      <div className="investment-name">{investment.name}</div>
                      <div className="investment-details">
                        <span>Cost: ${investment.cost.toLocaleString()}</span>
                        <span>Return: ${investment.return.toLocaleString()}</span>
                        <span>ROI: {investment.roi}%</span>
                        <span>Timeframe: {investment.timeframe}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CareerSimulator; 