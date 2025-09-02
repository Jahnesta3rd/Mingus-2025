/**
 * Financial Calculator Web Worker
 * Handles heavy financial calculations off the main thread
 * Optimized for African American professionals' financial assessment needs
 */

// Financial calculation constants
const FINANCIAL_CONSTANTS = {
    // Tax brackets for 2024
    TAX_BRACKETS: {
        single: [
            { rate: 0.10, min: 0, max: 11600 },
            { rate: 0.12, min: 11601, max: 47150 },
            { rate: 0.22, min: 47151, max: 100525 },
            { rate: 0.24, min: 100526, max: 191950 },
            { rate: 0.32, min: 191951, max: 243725 },
            { rate: 0.35, min: 243726, max: 609350 },
            { rate: 0.37, min: 609351, max: Infinity }
        ],
        married: [
            { rate: 0.10, min: 0, max: 23200 },
            { rate: 0.12, min: 23201, max: 94300 },
            { rate: 0.22, min: 94301, max: 201050 },
            { rate: 0.24, min: 201051, max: 383900 },
            { rate: 0.32, min: 383901, max: 487450 },
            { rate: 0.35, min: 487451, max: 731200 },
            { rate: 0.37, min: 731201, max: Infinity }
        ]
    },
    
    // Industry-specific salary data for African American professionals
    INDUSTRY_SALARIES: {
        technology: {
            entry: 65000,
            mid: 95000,
            senior: 140000,
            executive: 200000
        },
        healthcare: {
            entry: 55000,
            mid: 85000,
            senior: 120000,
            executive: 180000
        },
        finance: {
            entry: 60000,
            mid: 90000,
            senior: 130000,
            executive: 190000
        },
        education: {
            entry: 45000,
            mid: 65000,
            senior: 85000,
            executive: 120000
        },
        government: {
            entry: 50000,
            mid: 75000,
            senior: 100000,
            executive: 150000
        },
        entrepreneurship: {
            entry: 40000,
            mid: 80000,
            senior: 150000,
            executive: 300000
        }
    },
    
    // Regional cost of living adjustments
    COST_OF_LIVING: {
        'new-york': 1.5,
        'los-angeles': 1.4,
        'chicago': 1.2,
        'atlanta': 1.1,
        'houston': 1.0,
        'philadelphia': 1.1,
        'detroit': 0.9,
        'baltimore': 1.0,
        'washington-dc': 1.3,
        'boston': 1.3,
        'miami': 1.2,
        'dallas': 1.0,
        'phoenix': 1.0,
        'denver': 1.2,
        'seattle': 1.3
    },
    
    // Wealth gap adjustment factors
    WEALTH_GAP_FACTORS: {
        salary_negotiation: 0.85, // African Americans often negotiate less aggressively
        promotion_rate: 0.90,     // Slower promotion rates
        network_access: 0.80,     // Limited access to high-paying networks
        mentorship: 0.75,         // Limited access to mentors
        bias_adjustment: 0.88     // Systemic bias adjustment
    }
};

class FinancialCalculator {
    constructor() {
        this.cache = new Map();
        this.calculationHistory = [];
    }

    /**
     * Calculate salary comparison with equity considerations
     */
    calculateSalaryComparison(data) {
        const {
            currentSalary,
            targetIndustry,
            targetRole,
            experience,
            location,
            education,
            certifications,
            networkStrength,
            negotiationSkills
        } = data;

        // Get base salary for target role
        const baseSalary = this.getBaseSalary(targetIndustry, targetRole, experience);
        
        // Apply location adjustment
        const locationAdjustedSalary = this.applyLocationAdjustment(baseSalary, location);
        
        // Apply equity adjustments
        const equityAdjustedSalary = this.applyEquityAdjustments(locationAdjustedSalary, {
            education,
            certifications,
            networkStrength,
            negotiationSkills
        });

        // Calculate tax implications
        const taxAnalysis = this.calculateTaxImplications(equityAdjustedSalary, 'single');
        
        // Calculate wealth building potential
        const wealthBuilding = this.calculateWealthBuildingPotential(equityAdjustedSalary, currentSalary);
        
        // Calculate career advancement timeline
        const careerTimeline = this.calculateCareerTimeline(targetIndustry, targetRole, experience);

        return {
            currentSalary: parseFloat(currentSalary),
            targetSalary: equityAdjustedSalary,
            salaryIncrease: equityAdjustedSalary - currentSalary,
            percentageIncrease: ((equityAdjustedSalary - currentSalary) / currentSalary) * 100,
            taxAnalysis,
            wealthBuilding,
            careerTimeline,
            equityFactors: this.getEquityFactors(data),
            recommendations: this.generateRecommendations(data, equityAdjustedSalary)
        };
    }

    /**
     * Get base salary for industry and role
     */
    getBaseSalary(industry, role, experience) {
        const industryData = FINANCIAL_CONSTANTS.INDUSTRY_SALARIES[industry];
        if (!industryData) {
            return 60000; // Default salary
        }

        let baseSalary;
        if (experience < 2) {
            baseSalary = industryData.entry;
        } else if (experience < 5) {
            baseSalary = industryData.mid;
        } else if (experience < 10) {
            baseSalary = industryData.senior;
        } else {
            baseSalary = industryData.executive;
        }

        // Apply experience multiplier
        const experienceMultiplier = 1 + (experience * 0.05);
        return baseSalary * experienceMultiplier;
    }

    /**
     * Apply location-based cost of living adjustment
     */
    applyLocationAdjustment(salary, location) {
        const costOfLiving = FINANCIAL_CONSTANTS.COST_OF_LIVING[location] || 1.0;
        return salary * costOfLiving;
    }

    /**
     * Apply equity-based adjustments
     */
    applyEquityAdjustments(salary, factors) {
        let adjustedSalary = salary;
        
        // Education bonus
        if (factors.education === 'masters') {
            adjustedSalary *= 1.15;
        } else if (factors.education === 'phd') {
            adjustedSalary *= 1.25;
        }

        // Certification bonus
        if (factors.certifications && factors.certifications.length > 0) {
            adjustedSalary *= (1 + (factors.certifications.length * 0.05));
        }

        // Network strength adjustment
        const networkMultiplier = 1 + (factors.networkStrength * 0.1);
        adjustedSalary *= networkMultiplier;

        // Negotiation skills adjustment
        const negotiationMultiplier = 1 + (factors.negotiationSkills * 0.15);
        adjustedSalary *= negotiationMultiplier;

        // Apply wealth gap factors
        adjustedSalary *= FINANCIAL_CONSTANTS.WEALTH_GAP_FACTORS.bias_adjustment;

        return Math.round(adjustedSalary);
    }

    /**
     * Calculate tax implications
     */
    calculateTaxImplications(salary, filingStatus) {
        const brackets = FINANCIAL_CONSTANTS.TAX_BRACKETS[filingStatus];
        let totalTax = 0;
        let remainingIncome = salary;

        for (const bracket of brackets) {
            if (remainingIncome <= 0) break;

            const taxableInBracket = Math.min(
                remainingIncome,
                bracket.max - bracket.min + 1
            );

            totalTax += taxableInBracket * bracket.rate;
            remainingIncome -= taxableInBracket;
        }

        const effectiveTaxRate = (totalTax / salary) * 100;
        const takeHomePay = salary - totalTax;

        return {
            grossSalary: salary,
            totalTax: Math.round(totalTax),
            effectiveTaxRate: Math.round(effectiveTaxRate * 100) / 100,
            takeHomePay: Math.round(takeHomePay),
            monthlyTakeHome: Math.round(takeHomePay / 12)
        };
    }

    /**
     * Calculate wealth building potential
     */
    calculateWealthBuildingPotential(newSalary, currentSalary) {
        const salaryIncrease = newSalary - currentSalary;
        const monthlyIncrease = salaryIncrease / 12;

        // Conservative investment strategy (common among African American professionals)
        const investmentRate = 0.15; // 15% of increase
        const monthlyInvestment = monthlyIncrease * investmentRate;
        
        // Compound interest calculation (7% annual return)
        const annualReturn = 0.07;
        const monthlyReturn = annualReturn / 12;

        // Calculate 10-year wealth building potential
        let totalWealth = 0;
        for (let month = 1; month <= 120; month++) {
            totalWealth = (totalWealth + monthlyInvestment) * (1 + monthlyReturn);
        }

        return {
            monthlyInvestment: Math.round(monthlyInvestment),
            annualInvestment: Math.round(monthlyInvestment * 12),
            tenYearWealth: Math.round(totalWealth),
            investmentStrategy: this.getInvestmentStrategy(monthlyInvestment)
        };
    }

    /**
     * Calculate career advancement timeline
     */
    calculateCareerTimeline(industry, role, experience) {
        const timelines = {
            technology: { entry: 2, mid: 3, senior: 4, executive: 5 },
            healthcare: { entry: 3, mid: 4, senior: 5, executive: 6 },
            finance: { entry: 2, mid: 3, senior: 4, executive: 5 },
            education: { entry: 4, mid: 5, senior: 6, executive: 7 },
            government: { entry: 3, mid: 4, senior: 5, executive: 6 },
            entrepreneurship: { entry: 1, mid: 2, senior: 3, executive: 4 }
        };

        const industryTimeline = timelines[industry] || timelines.technology;
        
        // Apply equity adjustment (longer timelines due to systemic barriers)
        const equityAdjustment = 1.2; // 20% longer timeline

        let nextPromotion;
        if (experience < 2) {
            nextPromotion = industryTimeline.entry * equityAdjustment;
        } else if (experience < 5) {
            nextPromotion = industryTimeline.mid * equityAdjustment;
        } else if (experience < 10) {
            nextPromotion = industryTimeline.senior * equityAdjustment;
        } else {
            nextPromotion = industryTimeline.executive * equityAdjustment;
        }

        return {
            currentLevel: this.getCurrentLevel(experience),
            nextLevel: this.getNextLevel(experience),
            timeToNextPromotion: Math.round(nextPromotion),
            accelerationStrategies: this.getAccelerationStrategies(industry, role)
        };
    }

    /**
     * Get equity factors affecting salary
     */
    getEquityFactors(data) {
        return {
            educationGap: this.calculateEducationGap(data.education),
            networkGap: this.calculateNetworkGap(data.networkStrength),
            negotiationGap: this.calculateNegotiationGap(data.negotiationSkills),
            biasImpact: this.calculateBiasImpact(data),
            systemicBarriers: this.identifySystemicBarriers(data)
        };
    }

    /**
     * Generate personalized recommendations
     */
    generateRecommendations(data, targetSalary) {
        const recommendations = [];

        // Education recommendations
        if (data.education === 'bachelors') {
            recommendations.push({
                category: 'education',
                priority: 'high',
                title: 'Consider Advanced Degree',
                description: 'Masters degree could increase earning potential by 15-25%',
                impact: '15-25% salary increase',
                timeline: '2-3 years',
                cost: '$30,000-$60,000'
            });
        }

        // Certification recommendations
        if (!data.certifications || data.certifications.length < 2) {
            recommendations.push({
                category: 'certifications',
                priority: 'medium',
                title: 'Obtain Industry Certifications',
                description: 'Professional certifications can increase marketability',
                impact: '5-10% salary increase',
                timeline: '6-12 months',
                cost: '$1,000-$5,000'
            });
        }

        // Network recommendations
        if (data.networkStrength < 0.7) {
            recommendations.push({
                category: 'networking',
                priority: 'high',
                title: 'Build Professional Network',
                description: 'Strong networks lead to better opportunities and higher salaries',
                impact: '10-20% salary increase',
                timeline: '1-2 years',
                cost: '$500-$2,000 annually'
            });
        }

        // Negotiation recommendations
        if (data.negotiationSkills < 0.8) {
            recommendations.push({
                category: 'negotiation',
                priority: 'high',
                title: 'Improve Negotiation Skills',
                description: 'Effective negotiation can significantly impact salary outcomes',
                impact: '10-15% salary increase',
                timeline: '3-6 months',
                cost: '$200-$1,000'
            });
        }

        return recommendations;
    }

    /**
     * Helper methods
     */
    getCurrentLevel(experience) {
        if (experience < 2) return 'Entry Level';
        if (experience < 5) return 'Mid Level';
        if (experience < 10) return 'Senior Level';
        return 'Executive Level';
    }

    getNextLevel(experience) {
        if (experience < 2) return 'Mid Level';
        if (experience < 5) return 'Senior Level';
        if (experience < 10) return 'Executive Level';
        return 'C-Suite';
    }

    getInvestmentStrategy(monthlyInvestment) {
        if (monthlyInvestment >= 1000) {
            return 'Aggressive - Consider real estate and business investments';
        } else if (monthlyInvestment >= 500) {
            return 'Moderate - Focus on index funds and retirement accounts';
        } else {
            return 'Conservative - Start with emergency fund and 401(k)';
        }
    }

    getAccelerationStrategies(industry, role) {
        const strategies = {
            technology: ['Mentorship programs', 'Open source contributions', 'Technical certifications'],
            healthcare: ['Specialized certifications', 'Leadership training', 'Research involvement'],
            finance: ['CFA/CPA certifications', 'Networking events', 'Industry conferences'],
            education: ['Advanced degrees', 'Administrative certifications', 'Policy involvement'],
            government: ['Leadership programs', 'Policy expertise', 'Cross-agency experience'],
            entrepreneurship: ['Business incubators', 'Mentorship networks', 'Industry partnerships']
        };

        return strategies[industry] || strategies.technology;
    }

    calculateEducationGap(education) {
        const gaps = {
            'high-school': 0.25,
            'associates': 0.15,
            'bachelors': 0.10,
            'masters': 0.05,
            'phd': 0.02
        };
        return gaps[education] || 0.10;
    }

    calculateNetworkGap(networkStrength) {
        return (1 - networkStrength) * 0.20;
    }

    calculateNegotiationGap(negotiationSkills) {
        return (1 - negotiationSkills) * 0.15;
    }

    calculateBiasImpact(data) {
        // Calculate potential bias impact based on various factors
        let biasScore = 0.12; // Base bias impact
        
        // Adjust based on industry
        const industryBias = {
            technology: 0.15,
            healthcare: 0.10,
            finance: 0.18,
            education: 0.08,
            government: 0.05,
            entrepreneurship: 0.20
        };
        
        biasScore += industryBias[data.targetIndustry] || 0.12;
        
        return biasScore;
    }

    identifySystemicBarriers(data) {
        const barriers = [];
        
        if (data.education === 'bachelors' || data.education === 'high-school') {
            barriers.push('Limited access to advanced education');
        }
        
        if (data.networkStrength < 0.6) {
            barriers.push('Limited access to professional networks');
        }
        
        if (data.negotiationSkills < 0.7) {
            barriers.push('Cultural barriers to salary negotiation');
        }
        
        barriers.push('Systemic bias in hiring and promotion');
        barriers.push('Limited access to mentorship opportunities');
        
        return barriers;
    }
}

// Initialize calculator
const calculator = new FinancialCalculator();

// Handle messages from main thread
self.addEventListener('message', (event) => {
    const { type, data, id } = event.data;
    
    try {
        let result;
        
        switch (type) {
            case 'salary-comparison':
                result = calculator.calculateSalaryComparison(data);
                break;
                
            case 'tax-calculation':
                result = calculator.calculateTaxImplications(data.salary, data.filingStatus);
                break;
                
            case 'wealth-building':
                result = calculator.calculateWealthBuildingPotential(data.newSalary, data.currentSalary);
                break;
                
            case 'career-timeline':
                result = calculator.calculateCareerTimeline(data.industry, data.role, data.experience);
                break;
                
            default:
                throw new Error(`Unknown calculation type: ${type}`);
        }
        
        // Send result back to main thread
        self.postMessage({
            id,
            type: 'result',
            data: result,
            success: true
        });
        
    } catch (error) {
        // Send error back to main thread
        self.postMessage({
            id,
            type: 'error',
            error: error.message,
            success: false
        });
    }
});

// Handle errors
self.addEventListener('error', (error) => {
    self.postMessage({
        type: 'error',
        error: error.message,
        success: false
    });
});
