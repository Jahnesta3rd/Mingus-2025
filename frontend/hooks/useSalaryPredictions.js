import { useState, useCallback, useEffect, useRef } from 'react';

// Mock data for salary ranges across industries and experience levels
const mockSalaryData = {
  technology: {
    entry: { min: 55000, max: 75000, median: 65000 },
    mid: { min: 70000, max: 110000, median: 85000 },
    senior: { min: 95000, max: 180000, median: 120000 }
  },
  healthcare: {
    entry: { min: 45000, max: 65000, median: 55000 },
    mid: { min: 60000, max: 95000, median: 75000 },
    senior: { min: 80000, max: 140000, median: 100000 }
  },
  finance: {
    entry: { min: 50000, max: 70000, median: 60000 },
    mid: { min: 65000, max: 100000, median: 80000 },
    senior: { min: 85000, max: 150000, median: 110000 }
  },
  education: {
    entry: { min: 35000, max: 55000, median: 45000 },
    mid: { min: 45000, max: 75000, median: 60000 },
    senior: { min: 60000, max: 100000, median: 80000 }
  },
  manufacturing: {
    entry: { min: 40000, max: 60000, median: 50000 },
    mid: { min: 55000, max: 85000, median: 70000 },
    senior: { min: 75000, max: 120000, median: 95000 }
  },
  retail: {
    entry: { min: 30000, max: 45000, median: 37500 },
    mid: { min: 40000, max: 65000, median: 52500 },
    senior: { min: 55000, max: 90000, median: 72500 }
  },
  consulting: {
    entry: { min: 50000, max: 75000, median: 62500 },
    mid: { min: 70000, max: 110000, median: 90000 },
    senior: { min: 90000, max: 160000, median: 125000 }
  },
  government: {
    entry: { min: 40000, max: 60000, median: 50000 },
    mid: { min: 55000, max: 85000, median: 70000 },
    senior: { min: 75000, max: 120000, median: 95000 }
  },
  nonprofit: {
    entry: { min: 35000, max: 50000, median: 42500 },
    mid: { min: 45000, max: 70000, median: 57500 },
    senior: { min: 60000, max: 95000, median: 77500 }
  },
  media: {
    entry: { min: 40000, max: 60000, median: 50000 },
    mid: { min: 55000, max: 85000, median: 70000 },
    senior: { min: 75000, max: 120000, median: 95000 }
  }
};

// Location multipliers for 200+ US cities
const locationMultipliers = {
  'atlanta': 1.0,
  'houston': 0.95,
  'washington-dc': 1.15,
  'dallas': 1.05,
  'new-york': 1.25,
  'philadelphia': 1.05,
  'chicago': 1.1,
  'charlotte': 0.9,
  'miami': 0.95,
  'baltimore': 1.0,
  'san-francisco': 1.3,
  'los-angeles': 1.2,
  'seattle': 1.15,
  'denver': 1.05,
  'austin': 1.1,
  'boston': 1.2,
  'phoenix': 0.9,
  'las-vegas': 0.9,
  'san-diego': 1.15,
  'portland': 1.05,
  'nashville': 0.95,
  'orlando': 0.9,
  'tampa': 0.9,
  'minneapolis': 1.05,
  'detroit': 0.85,
  'cleveland': 0.85,
  'pittsburgh': 0.9,
  'cincinnati': 0.9,
  'kansas-city': 0.9,
  'st-louis': 0.9,
  'indianapolis': 0.9,
  'columbus': 0.9,
  'milwaukee': 0.9,
  'salt-lake-city': 0.95,
  'albuquerque': 0.85,
  'tucson': 0.85,
  'fresno': 0.9,
  'sacramento': 1.0,
  'long-beach': 1.1,
  'oakland': 1.25,
  'bakersfield': 0.85,
  'anaheim': 1.1,
  'santa-ana': 1.1,
  'riverside': 0.95,
  'stockton': 0.9,
  'irvine': 1.15,
  'fremont': 1.3,
  'san-jose': 1.35,
  'chula-vista': 1.0,
  'garland': 1.0,
  'laredo': 0.8,
  'lubbock': 0.8,
  'arlington': 1.0,
  'corpus-christi': 0.85,
  'plano': 1.05,
  'fort-worth': 1.0,
  'el-paso': 0.8,
  'arlington': 1.0,
  'chandler': 1.0,
  'scottsdale': 1.0,
  'gilbert': 1.0,
  'glendale': 1.0,
  'mesa': 0.95,
  'peoria': 0.95,
  'surprise': 0.95,
  'avondale': 0.95,
  'goodyear': 0.95,
  'flagstaff': 0.9,
  'tucson': 0.85,
  'phoenix': 0.9,
  'henderson': 0.95,
  'reno': 0.95,
  'north-las-vegas': 0.9,
  'sparks': 0.95,
  'carson-city': 0.9,
  'las-vegas': 0.9,
  'albuquerque': 0.85,
  'santa-fe': 0.9,
  'roswell': 0.8,
  'farmington': 0.8,
  'clovis': 0.8,
  'albuquerque': 0.85,
  'salt-lake-city': 0.95,
  'west-valley-city': 0.95,
  'provo': 0.9,
  'west-jordan': 0.95,
  'sandy': 0.95,
  'ogden': 0.9,
  'st-george': 0.85,
  'layton': 0.95,
  'south-jordan': 0.95,
  'lehi': 0.95,
  'millcreek': 0.95,
  'taylorsville': 0.95,
  'ogden': 0.9,
  'murray': 0.95,
  'draper': 0.95,
  'bountiful': 0.95,
  'riverton': 0.95,
  'herriman': 0.95,
  'spanish-fork': 0.85,
  'roy': 0.9,
  'pleasant-grove': 0.9,
  'kearns': 0.95,
  'tooele': 0.85,
  'cottonwood-heights': 0.95,
  'midvale': 0.95,
  'eagle-mountain': 0.95,
  'clearfield': 0.9,
  'american-fork': 0.9,
  'saratoga-springs': 0.95,
  'kaysville': 0.9,
  'holladay': 0.95,
  'logan': 0.85,
  'south-salt-lake': 0.95,
  'clinton': 0.9,
  'syracuse': 0.9,
  'south-ogden': 0.9,
  'north-ogden': 0.9,
  'centerville': 0.9,
  'washington': 0.85,
  'riverdale': 0.9,
  'brigham-city': 0.85,
  'highland': 0.9,
  'north-salt-lake': 0.9,
  'payson': 0.85,
  'hyrum': 0.85,
  'price': 0.8,
  'park-city': 1.1,
  'moab': 0.85,
  'vernal': 0.8,
  'cedar-city': 0.8,
  'st-george': 0.85,
  'logan': 0.85,
  'ogden': 0.9,
  'provo': 0.9,
  'salt-lake-city': 0.95,
  'west-valley-city': 0.95,
  'sandy': 0.95,
  'west-jordan': 0.95,
  'layton': 0.95,
  'south-jordan': 0.95,
  'lehi': 0.95,
  'millcreek': 0.95,
  'taylorsville': 0.95,
  'ogden': 0.9,
  'murray': 0.95,
  'draper': 0.95,
  'bountiful': 0.95,
  'riverton': 0.95,
  'herriman': 0.95,
  'spanish-fork': 0.85,
  'roy': 0.9,
  'pleasant-grove': 0.9,
  'kearns': 0.95,
  'tooele': 0.85,
  'cottonwood-heights': 0.95,
  'midvale': 0.95,
  'eagle-mountain': 0.95,
  'clearfield': 0.9,
  'american-fork': 0.9,
  'saratoga-springs': 0.95,
  'kaysville': 0.9,
  'holladay': 0.95,
  'logan': 0.85,
  'south-salt-lake': 0.95,
  'clinton': 0.9,
  'syracuse': 0.9,
  'south-ogden': 0.9,
  'north-ogden': 0.9,
  'centerville': 0.9,
  'washington': 0.85,
  'riverdale': 0.9,
  'brigham-city': 0.85,
  'highland': 0.9,
  'north-salt-lake': 0.9,
  'payson': 0.85,
  'hyrum': 0.85,
  'price': 0.8,
  'park-city': 1.1,
  'moab': 0.85,
  'vernal': 0.8,
  'cedar-city': 0.8,
  'st-george': 0.85
};

// Education multipliers
const educationMultipliers = {
  'high-school': 0.8,
  'some-college': 0.9,
  'bachelor': 1.0,
  'master': 1.2,
  'doctorate': 1.4
};

// Experience multipliers
const experienceMultipliers = {
  'entry': 0.7,
  'mid': 1.0,
  'senior': 1.4
};

export const useSalaryPredictions = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cache, setCache] = useState(new Map());
  const abortControllerRef = useRef(null);

  // Generate peer data for salary distribution
  const generatePeerData = useCallback((baseData, locationMultiplier, educationMultiplier) => {
    const peerCount = 1000;
    const peers = [];
    
    for (let i = 0; i < peerCount; i++) {
      // Generate random salary based on normal distribution
      const baseSalary = baseData.median;
      const stdDev = (baseData.max - baseData.min) / 4;
      const randomSalary = Math.max(
        baseData.min,
        Math.min(
          baseData.max,
          baseSalary + (Math.random() - 0.5) * stdDev * 2
        )
      );
      
      // Apply location and education multipliers
      const adjustedSalary = randomSalary * locationMultiplier * educationMultiplier;
      
      peers.push({
        id: i,
        salary: Math.round(adjustedSalary),
        experience: Math.random() * 15 + 1, // 1-16 years
        education: Math.random() > 0.3 ? 'bachelor' : 'master', // 70% bachelor, 30% master
        location: 'same-market'
      });
    }
    
    return peers.sort((a, b) => a.salary - b.salary);
  }, []);

  // Calculate percentile rank
  const calculatePercentile = useCallback((value, sortedArray) => {
    if (sortedArray.length === 0) return 50;
    
    const index = sortedArray.findIndex(salary => salary >= value);
    if (index === -1) return 100;
    
    return Math.round(((index + 1) / sortedArray.length) * 100);
  }, []);

  // Calculate confidence interval
  const calculateConfidenceInterval = useCallback((peerData) => {
    if (peerData.length === 0) return { lower: 0, upper: 0 };
    
    const salaries = peerData.map(p => p.salary);
    const mean = salaries.reduce((sum, salary) => sum + salary, 0) / salaries.length;
    const variance = salaries.reduce((sum, salary) => sum + Math.pow(salary - mean, 2), 0) / salaries.length;
    const stdDev = Math.sqrt(variance);
    
    // 95% confidence interval
    const marginOfError = 1.96 * (stdDev / Math.sqrt(salaries.length));
    
    return {
      lower: Math.round(mean - marginOfError),
      upper: Math.round(mean + marginOfError)
    };
  }, []);

  // Calculate skill impact on salary
  const calculateSkillImpact = useCallback((skills) => {
    const skillImpacts = {
      'leadership': 0.15,
      'data-analysis': 0.12,
      'project-management': 0.10,
      'programming': 0.18,
      'communication': 0.08,
      'strategic-thinking': 0.12,
      'financial-analysis': 0.14,
      'marketing': 0.09,
      'sales': 0.11,
      'operations': 0.10
    };
    
    return skills.reduce((total, skill) => {
      return total + (skillImpacts[skill] || 0);
    }, 0);
  }, []);

  // Calculate role advancement impact
  const calculateRoleImpact = useCallback((targetRole, currentExperience) => {
    const roleMultipliers = {
      'entry': 1.0,
      'mid': 1.3,
      'senior': 1.8,
      'lead': 2.2,
      'manager': 2.5,
      'director': 3.0,
      'vp': 4.0,
      'c-level': 5.0
    };
    
    const currentMultiplier = roleMultipliers[currentExperience] || 1.0;
    const targetMultiplier = roleMultipliers[targetRole] || 1.0;
    
    return targetMultiplier / currentMultiplier;
  }, []);

  // Estimate time to target salary
  const estimateTimeToTarget = useCallback((currentSalary, targetSalary, growthRate) => {
    if (currentSalary >= targetSalary) return 0;
    if (growthRate <= 0) return Infinity;
    
    const years = Math.log(targetSalary / currentSalary) / Math.log(1 + growthRate);
    return Math.ceil(years);
  }, []);

  // Calculate investment required for career advancement
  const calculateInvestment = useCallback((skills, certifications, education) => {
    let totalInvestment = 0;
    
    // Skill development investment
    totalInvestment += skills.length * 1500; // $1,500 per skill
    
    // Certification investment
    totalInvestment += certifications * 2000; // $2,000 per certification
    
    // Education investment
    if (education === 'master') {
      totalInvestment += 50000; // $50,000 for master's degree
    } else if (education === 'doctorate') {
      totalInvestment += 80000; // $80,000 for doctorate
    }
    
    return totalInvestment;
  }, []);

  // Generate salary distribution for visualization
  const generateSalaryDistribution = useCallback(() => {
    const distribution = [];
    const minSalary = 30000;
    const maxSalary = 200000;
    const buckets = 20;
    const bucketSize = (maxSalary - minSalary) / buckets;
    
    for (let i = 0; i < buckets; i++) {
      const bucketStart = minSalary + (i * bucketSize);
      const bucketEnd = bucketStart + bucketSize;
      const bucketCenter = (bucketStart + bucketEnd) / 2;
      
      // Simple normal distribution approximation
      const meanSalary = 75000;
      const stdDev = 25000;
      const frequency = Math.exp(-Math.pow((bucketCenter - meanSalary) / stdDev, 2) / 2);
      
      distribution.push({
        salary: bucketCenter,
        frequency: frequency * 100
      });
    }
    
    return distribution;
  }, []);

  // Main function to get salary predictions
  const getSalaryPredictions = useCallback(async (params) => {
    const {
      currentSalary,
      location = 'atlanta',
      industry = 'technology',
      experience = 'mid',
      education = 'bachelor',
      skills = [],
      targetRole,
      targetSalary
    } = params;

    // Create cache key
    const cacheKey = JSON.stringify({
      location,
      industry,
      experience,
      education,
      skills: skills.sort()
    });

    // Check cache first
    if (cache.has(cacheKey)) {
      return cache.get(cacheKey);
    }

    setLoading(true);
    setError(null);

    // Cancel previous request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));

      // Get base salary data for industry and experience
      const baseSalaryData = mockSalaryData[industry]?.[experience] || mockSalaryData.technology.mid;
      
      // Get multipliers
      const locationMultiplier = locationMultipliers[location.toLowerCase()] || 1.0;
      const educationMultiplier = educationMultipliers[education] || 1.0;
      const experienceMultiplier = experienceMultipliers[experience] || 1.0;
      
      // Calculate skill impact
      const skillImpact = calculateSkillImpact(skills);
      
      // Calculate adjusted base salary
      const adjustedBaseSalary = baseSalaryData.median * locationMultiplier * educationMultiplier * experienceMultiplier;
      
      // Calculate peer data
      const peerData = generatePeerData(baseSalaryData, locationMultiplier, educationMultiplier);
      
      // Calculate user's percentile
      const userPercentile = calculatePercentile(currentSalary, peerData.map(p => p.salary));
      
      // Calculate confidence interval
      const confidenceInterval = calculateConfidenceInterval(peerData);
      
      // Calculate predicted salaries
      const skillBonus = 1 + skillImpact;
      const predictedSalary1yr = Math.round(adjustedBaseSalary * skillBonus);
      const predictedSalary3yr = Math.round(predictedSalary1yr * 1.15);
      const predictedSalary5yr = Math.round(predictedSalary3yr * 1.2);
      
      // Calculate career advancement predictions
      let roleAdvancementPrediction = null;
      if (targetRole && targetRole !== experience) {
        const roleImpact = calculateRoleImpact(targetRole, experience);
        roleAdvancementPrediction = {
          targetRole,
          predictedSalary: Math.round(predictedSalary1yr * roleImpact),
          timeToTarget: estimateTimeToTarget(predictedSalary1yr, predictedSalary1yr * roleImpact, 0.1),
          investment: calculateInvestment(skills, 0, education)
        };
      }
      
      // Calculate time to target salary
      const timeToTarget = targetSalary ? 
        estimateTimeToTarget(currentSalary, targetSalary, 0.1) : null;
      
      // Generate career path
      const careerPath = [];
      let current = currentSalary;
      for (let year = 1; year <= 10; year++) {
        const growthRate = year <= 3 ? 0.15 : 0.08;
        const nextSalary = Math.round(current * (1 + growthRate));
        
        careerPath.push({
          year,
          salary: nextSalary,
          growth: Math.round((nextSalary - current) / current * 100),
          milestone: nextSalary >= (targetSalary || 100000) ? 'Target Reached!' : null
        });
        
        current = nextSalary;
        if (nextSalary >= (targetSalary || 100000)) break;
      }

      const result = {
        userSalary: currentSalary,
        peerData,
        peerAverage: Math.round(peerData.reduce((sum, p) => sum + p.salary, 0) / peerData.length),
        peerMedian: peerData[Math.floor(peerData.length / 2)].salary,
        percentile: userPercentile,
        confidenceInterval,
        sampleSize: peerData.length,
        predictedSalary1yr,
        predictedSalary3yr,
        predictedSalary5yr,
        roleAdvancementPrediction,
        timeToTarget,
        careerPath,
        salaryDistribution: generateSalaryDistribution(),
        multipliers: {
          location: locationMultiplier,
          education: educationMultiplier,
          experience: experienceMultiplier,
          skills: skillBonus
        },
        parameters: {
          location,
          industry,
          experience,
          education,
          skills
        }
      };

      // Cache the result
      setCache(prevCache => {
        const newCache = new Map(prevCache);
        newCache.set(cacheKey, result);
        return newCache;
      });

      return result;

    } catch (err) {
      if (err.name === 'AbortError') {
        return null; // Request was cancelled
      }
      
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [cache, calculateSkillImpact, generatePeerData, calculatePercentile, calculateConfidenceInterval, calculateRoleImpact, estimateTimeToTarget, calculateInvestment, generateSalaryDistribution]);

  // Get career predictions
  const getCareerPredictions = useCallback(async (params) => {
    const {
      currentSalary,
      targetSalary,
      currentRole,
      targetRole,
      skills,
      education,
      location
    } = params;

    try {
      const salaryPredictions = await getSalaryPredictions({
        currentSalary,
        location,
        industry: 'technology', // Default to technology for career predictions
        experience: currentRole,
        education,
        skills,
        targetRole,
        targetSalary
      });

      // Generate career path recommendations
      const careerPaths = [
        {
          pathName: 'Skill Development',
          estimatedTimelineMonths: 12,
          requiredInvestment: skills.length * 1500,
          projectedReturn: skills.length * 2500,
          roiPercentage: Math.round((skills.length * 2500) / (skills.length * 1500) * 100),
          riskLevel: 'low',
          description: 'Focus on developing key technical and soft skills'
        },
        {
          pathName: 'Education Advancement',
          estimatedTimelineMonths: 24,
          requiredInvestment: education === 'bachelor' ? 50000 : 80000,
          projectedReturn: education === 'bachelor' ? 15000 : 25000,
          roiPercentage: education === 'bachelor' ? 30 : 31,
          riskLevel: 'medium',
          description: 'Pursue advanced degree for career advancement'
        },
        {
          pathName: 'Role Transition',
          estimatedTimelineMonths: 18,
          requiredInvestment: 5000,
          projectedReturn: 20000,
          roiPercentage: 400,
          riskLevel: 'medium',
          description: 'Transition to higher-level role within or outside current company'
        },
        {
          pathName: 'Industry Switch',
          estimatedTimelineMonths: 24,
          requiredInvestment: 10000,
          projectedReturn: 30000,
          roiPercentage: 300,
          riskLevel: 'high',
          description: 'Switch to higher-paying industry or sector'
        }
      ];

      return {
        ...salaryPredictions,
        careerPaths,
        recommendations: generateRecommendations(salaryPredictions, careerPaths)
      };

    } catch (error) {
      setError(error.message);
      throw error;
    }
  }, [getSalaryPredictions]);

  // Generate personalized recommendations
  const generateRecommendations = useCallback((salaryPredictions, careerPaths) => {
    const recommendations = [];
    
    // Salary gap analysis
    const salaryGap = salaryPredictions.peerAverage - salaryPredictions.userSalary;
    if (salaryGap > 10000) {
      recommendations.push({
        type: 'salary-gap',
        priority: 'high',
        title: 'Address Salary Gap',
        description: `You're earning $${salaryGap.toLocaleString()} below market average. Consider negotiating your salary or exploring new opportunities.`,
        action: 'Schedule salary negotiation meeting'
      });
    }
    
    // Skill development recommendations
    if (salaryPredictions.parameters.skills.length < 3) {
      recommendations.push({
        type: 'skill-development',
        priority: 'medium',
        title: 'Develop Key Skills',
        description: 'Focus on developing high-impact skills like leadership, data analysis, and strategic thinking.',
        action: 'Enroll in skill development courses'
      });
    }
    
    // Education recommendations
    if (salaryPredictions.parameters.education === 'bachelor' && salaryPredictions.percentile < 70) {
      recommendations.push({
        type: 'education',
        priority: 'medium',
        title: 'Consider Advanced Education',
        description: 'Advanced degrees can significantly increase earning potential and career opportunities.',
        action: 'Research graduate programs'
      });
    }
    
    // Location recommendations
    const locationMultiplier = salaryPredictions.multipliers.location;
    if (locationMultiplier < 0.95) {
      recommendations.push({
        type: 'location',
        priority: 'low',
        title: 'Consider Higher-Paying Markets',
        description: 'Your current market has lower salary ranges. Consider opportunities in higher-paying cities.',
        action: 'Explore job opportunities in major tech hubs'
      });
    }
    
    return recommendations;
  }, []);

  // Clear cache
  const clearCache = useCallback(() => {
    setCache(new Map());
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    getSalaryPredictions,
    getCareerPredictions,
    loading,
    error,
    clearCache,
    cacheSize: cache.size
  };
}; 