import React, { useState, useEffect, useRef } from 'react';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import './FinancialForm.css';

/**
 * Accessible Financial Form Component
 * Implements WCAG 2.1 AA standards with comprehensive screen reader support
 * Compatible with NVDA, JAWS, VoiceOver, and TalkBack
 */

const FinancialForm = ({ onSubmit, initialValues = {}, title = "Financial Information" }) => {
    const [isCalculating, setIsCalculating] = useState(false);
    const [calculationResult, setCalculationResult] = useState(null);
    const [announcements, setAnnouncements] = useState([]);
    
    // Refs for accessibility
    const formRef = useRef(null);
    const liveRegionRef = useRef(null);
    const errorSummaryRef = useRef(null);
    
    // Validation schema
    const validationSchema = Yup.object({
        annualIncome: Yup.number()
            .required('Annual income is required')
            .positive('Income must be positive')
            .max(10000000, 'Income cannot exceed $10,000,000'),
        monthlyExpenses: Yup.number()
            .required('Monthly expenses are required')
            .positive('Expenses must be positive')
            .max(1000000, 'Expenses cannot exceed $1,000,000'),
        savingsRate: Yup.number()
            .required('Savings rate is required')
            .min(0, 'Savings rate cannot be negative')
            .max(100, 'Savings rate cannot exceed 100%'),
        investmentAmount: Yup.number()
            .min(0, 'Investment amount cannot be negative')
            .max(10000000, 'Investment amount cannot exceed $10,000,000'),
        debtAmount: Yup.number()
            .min(0, 'Debt amount cannot be negative')
            .max(10000000, 'Debt amount cannot exceed $10,000,000'),
        creditScore: Yup.number()
            .min(300, 'Credit score must be at least 300')
            .max(850, 'Credit score cannot exceed 850')
    });

    // Formik setup
    const formik = useFormik({
        initialValues: {
            annualIncome: initialValues.annualIncome || '',
            monthlyExpenses: initialValues.monthlyExpenses || '',
            savingsRate: initialValues.savingsRate || '',
            investmentAmount: initialValues.investmentAmount || '',
            debtAmount: initialValues.debtAmount || '',
            creditScore: initialValues.creditScore || '',
            ...initialValues
        },
        validationSchema,
        onSubmit: async (values) => {
            setIsCalculating(true);
            
            // Announce calculation start
            announceToScreenReader('Starting financial calculation...', 'polite');
            
            try {
                const result = await onSubmit(values);
                setCalculationResult(result);
                
                // Announce successful calculation
                announceToScreenReader('Financial calculation completed successfully', 'polite');
                
                // Announce key results
                if (result.monthlySavings) {
                    announceToScreenReader(`Monthly savings calculated: ${formatCurrency(result.monthlySavings)}`, 'polite');
                }
                if (result.debtToIncomeRatio) {
                    announceToScreenReader(`Debt to income ratio: ${(result.debtToIncomeRatio * 100).toFixed(1)}%`, 'polite');
                }
                
            } catch (error) {
                announceToScreenReader(`Calculation error: ${error.message}`, 'assertive');
            } finally {
                setIsCalculating(false);
            }
        }
    });

    // Screen reader announcements
    const announceToScreenReader = (message, priority = 'polite') => {
        const newAnnouncement = {
            id: Date.now(),
            message,
            priority,
            timestamp: new Date().toISOString()
        };
        
        setAnnouncements(prev => [...prev, newAnnouncement]);
        
        // Clear announcement after 5 seconds
        setTimeout(() => {
            setAnnouncements(prev => prev.filter(a => a.id !== newAnnouncement.id));
        }, 5000);
    };

    // Real-time calculations and announcements
    useEffect(() => {
        const { annualIncome, monthlyExpenses, savingsRate } = formik.values;
        
        if (annualIncome && monthlyExpenses && savingsRate) {
            const monthlyIncome = annualIncome / 12;
            const monthlySavings = monthlyIncome * (savingsRate / 100);
            const remainingBudget = monthlyIncome - monthlyExpenses - monthlySavings;
            
            if (remainingBudget < 0) {
                announceToScreenReader('Warning: Your expenses and savings exceed your monthly income', 'assertive');
            } else if (remainingBudget < monthlyIncome * 0.1) {
                announceToScreenReader('Notice: Your remaining budget is less than 10% of your income', 'polite');
            }
        }
    }, [formik.values.annualIncome, formik.values.monthlyExpenses, formik.values.savingsRate]);

    // Format currency for screen readers
    const formatCurrencyForScreenReader = (amount) => {
        const num = parseFloat(amount);
        if (isNaN(num)) return amount;
        
        const dollars = Math.floor(num);
        const cents = Math.round((num - dollars) * 100);
        
        if (cents === 0) {
            return `${dollars} dollars`;
        } else {
            return `${dollars} dollars and ${cents} cents`;
        }
    };

    // Handle field focus for screen reader announcements
    const handleFieldFocus = (fieldName, fieldValue) => {
        if (fieldValue) {
            announceToScreenReader(`Focused on ${fieldName}: ${fieldValue}`, 'polite');
        }
    };

    // Handle field change with announcements
    const handleFieldChange = (e, fieldName) => {
        const value = e.target.value;
        formik.handleChange(e);
        
        // Announce significant changes
        if (value && fieldName === 'annualIncome') {
            const monthlyIncome = parseFloat(value) / 12;
            announceToScreenReader(`Monthly income updated to ${formatCurrencyForScreenReader(monthlyIncome)}`, 'polite');
        } else if (value && fieldName === 'savingsRate') {
            announceToScreenReader(`Savings rate updated to ${value}%`, 'polite');
        }
    };

    return (
        <div className="financial-form-container" role="main" aria-labelledby="financial-form-title">
            {/* Live Region for Screen Reader Announcements */}
            <div 
                ref={liveRegionRef}
                id="financial-live-region"
                aria-live="polite"
                aria-atomic="true"
                className="sr-only"
                aria-label="Financial form announcements"
            >
                {announcements.map(announcement => (
                    <div key={announcement.id} className={`announcement ${announcement.priority}`}>
                        {announcement.message}
                    </div>
                ))}
            </div>

            {/* Error Summary for Screen Readers */}
            {Object.keys(formik.errors).length > 0 && (
                <div 
                    ref={errorSummaryRef}
                    role="alert"
                    aria-live="assertive"
                    className="error-summary"
                    aria-labelledby="error-summary-title"
                >
                    <h3 id="error-summary-title">Form Errors</h3>
                    <ul>
                        {Object.entries(formik.errors).map(([field, error]) => (
                            <li key={field}>
                                <a href={`#${field}`} onClick={(e) => {
                                    e.preventDefault();
                                    document.getElementById(field)?.focus();
                                }}>
                                    {getFieldLabel(field)}: {error}
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <form 
                ref={formRef}
                onSubmit={formik.handleSubmit}
                className="financial-form"
                aria-labelledby="financial-form-title"
                noValidate
            >
                <h1 id="financial-form-title">{title}</h1>
                
                {/* Income Section */}
                <fieldset className="form-section">
                    <legend className="section-legend">Income Information</legend>
                    
                    <div className="form-group">
                        <label htmlFor="annualIncome" className="form-label required">
                            Annual Income
                            <span className="required-indicator" aria-label="required field">*</span>
                        </label>
                        <div className="currency-input">
                            <span className="currency-symbol" aria-hidden="true">$</span>
                            <input
                                type="number"
                                id="annualIncome"
                                name="annualIncome"
                                className={`form-input ${formik.touched.annualIncome && formik.errors.annualIncome ? 'error' : ''}`}
                                value={formik.values.annualIncome}
                                onChange={(e) => handleFieldChange(e, 'annualIncome')}
                                onBlur={formik.handleBlur}
                                onFocus={() => handleFieldFocus('annual income', formik.values.annualIncome)}
                                placeholder="50000"
                                min="0"
                                step="1000"
                                aria-describedby="annualIncome-help annualIncome-error"
                                aria-label="Annual income in dollars before taxes"
                                required
                            />
                        </div>
                        <div id="annualIncome-help" className="form-help">
                            Enter your gross annual income before any deductions or taxes
                        </div>
                        {formik.touched.annualIncome && formik.errors.annualIncome && (
                            <div id="annualIncome-error" className="form-error" role="alert">
                                {formik.errors.annualIncome}
                            </div>
                        )}
                    </div>
                </fieldset>

                {/* Expenses Section */}
                <fieldset className="form-section">
                    <legend className="section-legend">Monthly Expenses</legend>
                    
                    <div className="form-group">
                        <label htmlFor="monthlyExpenses" className="form-label required">
                            Monthly Expenses
                            <span className="required-indicator" aria-label="required field">*</span>
                        </label>
                        <div className="currency-input">
                            <span className="currency-symbol" aria-hidden="true">$</span>
                            <input
                                type="number"
                                id="monthlyExpenses"
                                name="monthlyExpenses"
                                className={`form-input ${formik.touched.monthlyExpenses && formik.errors.monthlyExpenses ? 'error' : ''}`}
                                value={formik.values.monthlyExpenses}
                                onChange={(e) => handleFieldChange(e, 'monthlyExpenses')}
                                onBlur={formik.handleBlur}
                                onFocus={() => handleFieldFocus('monthly expenses', formik.values.monthlyExpenses)}
                                placeholder="3000"
                                min="0"
                                step="100"
                                aria-describedby="monthlyExpenses-help monthlyExpenses-error"
                                aria-label="Total monthly expenses in dollars"
                                required
                            />
                        </div>
                        <div id="monthlyExpenses-help" className="form-help">
                            Include housing, transportation, food, utilities, and other monthly costs
                        </div>
                        {formik.touched.monthlyExpenses && formik.errors.monthlyExpenses && (
                            <div id="monthlyExpenses-error" className="form-error" role="alert">
                                {formik.errors.monthlyExpenses}
                            </div>
                        )}
                    </div>

                    <div className="form-group">
                        <label htmlFor="savingsRate" className="form-label required">
                            Monthly Savings Rate
                            <span className="required-indicator" aria-label="required field">*</span>
                        </label>
                        <div className="percentage-input">
                            <input
                                type="number"
                                id="savingsRate"
                                name="savingsRate"
                                className={`form-input ${formik.touched.savingsRate && formik.errors.savingsRate ? 'error' : ''}`}
                                value={formik.values.savingsRate}
                                onChange={(e) => handleFieldChange(e, 'savingsRate')}
                                onBlur={formik.handleBlur}
                                onFocus={() => handleFieldFocus('savings rate', formik.values.savingsRate)}
                                placeholder="20"
                                min="0"
                                max="100"
                                step="0.1"
                                aria-describedby="savingsRate-help savingsRate-error"
                                aria-label="Monthly savings rate as percentage of income"
                                required
                            />
                            <span className="percentage-symbol" aria-hidden="true">%</span>
                        </div>
                        <div id="savingsRate-help" className="form-help">
                            Recommended: 20% of your monthly income for savings and investments
                        </div>
                        {formik.touched.savingsRate && formik.errors.savingsRate && (
                            <div id="savingsRate-error" className="form-error" role="alert">
                                {formik.errors.savingsRate}
                            </div>
                        )}
                    </div>
                </fieldset>

                {/* Assets and Debt Section */}
                <fieldset className="form-section">
                    <legend className="section-legend">Assets and Debt</legend>
                    
                    <div className="form-group">
                        <label htmlFor="investmentAmount" className="form-label">
                            Current Investment Amount
                        </label>
                        <div className="currency-input">
                            <span className="currency-symbol" aria-hidden="true">$</span>
                            <input
                                type="number"
                                id="investmentAmount"
                                name="investmentAmount"
                                className={`form-input ${formik.touched.investmentAmount && formik.errors.investmentAmount ? 'error' : ''}`}
                                value={formik.values.investmentAmount}
                                onChange={formik.handleChange}
                                onBlur={formik.handleBlur}
                                onFocus={() => handleFieldFocus('investment amount', formik.values.investmentAmount)}
                                placeholder="10000"
                                min="0"
                                step="1000"
                                aria-describedby="investmentAmount-help investmentAmount-error"
                                aria-label="Current total investment amount in dollars"
                            />
                        </div>
                        <div id="investmentAmount-help" className="form-help">
                            Include retirement accounts, stocks, bonds, and other investments
                        </div>
                        {formik.touched.investmentAmount && formik.errors.investmentAmount && (
                            <div id="investmentAmount-error" className="form-error" role="alert">
                                {formik.errors.investmentAmount}
                            </div>
                        )}
                    </div>

                    <div className="form-group">
                        <label htmlFor="debtAmount" className="form-label">
                            Total Debt Amount
                        </label>
                        <div className="currency-input">
                            <span className="currency-symbol" aria-hidden="true">$</span>
                            <input
                                type="number"
                                id="debtAmount"
                                name="debtAmount"
                                className={`form-input ${formik.touched.debtAmount && formik.errors.debtAmount ? 'error' : ''}`}
                                value={formik.values.debtAmount}
                                onChange={formik.handleChange}
                                onBlur={formik.handleBlur}
                                onFocus={() => handleFieldFocus('debt amount', formik.values.debtAmount)}
                                placeholder="25000"
                                min="0"
                                step="1000"
                                aria-describedby="debtAmount-help debtAmount-error"
                                aria-label="Total debt amount in dollars including loans and credit cards"
                            />
                        </div>
                        <div id="debtAmount-help" className="form-help">
                            Include credit cards, student loans, car loans, and other debts
                        </div>
                        {formik.touched.debtAmount && formik.errors.debtAmount && (
                            <div id="debtAmount-error" className="form-error" role="alert">
                                {formik.errors.debtAmount}
                            </div>
                        )}
                    </div>

                    <div className="form-group">
                        <label htmlFor="creditScore" className="form-label">
                            Credit Score
                        </label>
                        <input
                            type="number"
                            id="creditScore"
                            name="creditScore"
                            className={`form-input ${formik.touched.creditScore && formik.errors.creditScore ? 'error' : ''}`}
                            value={formik.values.creditScore}
                            onChange={formik.handleChange}
                            onBlur={formik.handleBlur}
                            onFocus={() => handleFieldFocus('credit score', formik.values.creditScore)}
                            placeholder="750"
                            min="300"
                            max="850"
                            step="1"
                            aria-describedby="creditScore-help creditScore-error"
                            aria-label="Your current credit score between 300 and 850"
                        />
                        <div id="creditScore-help" className="form-help">
                            Your FICO or VantageScore credit score (300-850 range)
                        </div>
                        {formik.touched.creditScore && formik.errors.creditScore && (
                            <div id="creditScore-error" className="form-error" role="alert">
                                {formik.errors.creditScore}
                            </div>
                        )}
                    </div>
                </fieldset>

                {/* Submit Button */}
                <div className="form-actions">
                    <button
                        type="submit"
                        className="btn-submit"
                        disabled={isCalculating || !formik.isValid}
                        aria-describedby="submit-help"
                        aria-busy={isCalculating}
                    >
                        {isCalculating ? 'Calculating...' : 'Calculate Financial Plan'}
                    </button>
                    <div id="submit-help" className="form-help">
                        Click to calculate your personalized financial plan and recommendations
                    </div>
                </div>
            </form>

            {/* Calculation Results */}
            {calculationResult && (
                <div 
                    className="calculation-results"
                    role="region"
                    aria-labelledby="results-title"
                    aria-live="polite"
                >
                    <h2 id="results-title">Financial Analysis Results</h2>
                    
                    <div className="results-grid">
                        <div className="result-card">
                            <h3>Monthly Budget Breakdown</h3>
                            <div className="result-item">
                                <span className="result-label">Monthly Income:</span>
                                <span className="result-value">{formatCurrency(calculationResult.monthlyIncome)}</span>
                            </div>
                            <div className="result-item">
                                <span className="result-label">Monthly Expenses:</span>
                                <span className="result-value">{formatCurrency(calculationResult.monthlyExpenses)}</span>
                            </div>
                            <div className="result-item">
                                <span className="result-label">Monthly Savings:</span>
                                <span className="result-value">{formatCurrency(calculationResult.monthlySavings)}</span>
                            </div>
                            <div className="result-item">
                                <span className="result-label">Remaining Budget:</span>
                                <span className={`result-value ${calculationResult.remainingBudget < 0 ? 'negative' : ''}`}>
                                    {formatCurrency(calculationResult.remainingBudget)}
                                </span>
                            </div>
                        </div>

                        <div className="result-card">
                            <h3>Financial Health Metrics</h3>
                            <div className="result-item">
                                <span className="result-label">Debt-to-Income Ratio:</span>
                                <span className="result-value">{(calculationResult.debtToIncomeRatio * 100).toFixed(1)}%</span>
                            </div>
                            <div className="result-item">
                                <span className="result-label">Savings Rate:</span>
                                <span className="result-value">{calculationResult.savingsRate}%</span>
                            </div>
                            <div className="result-item">
                                <span className="result-label">Emergency Fund Status:</span>
                                <span className={`result-value ${calculationResult.emergencyFundStatus === 'Good' ? 'positive' : 'warning'}`}>
                                    {calculationResult.emergencyFundStatus}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Progress Bar for Savings Goal */}
                    <div className="progress-section">
                        <label htmlFor="savings-progress" className="progress-label">
                            Progress Toward Emergency Fund Goal
                        </label>
                        <div 
                            className="progress-bar"
                            role="progressbar"
                            aria-valuenow={calculationResult.emergencyFundProgress}
                            aria-valuemin="0"
                            aria-valuemax="100"
                            aria-describedby="progress-description"
                        >
                            <div 
                                className="progress-fill"
                                style={{ width: `${calculationResult.emergencyFundProgress}%` }}
                            ></div>
                            <span className="progress-text">
                                {calculationResult.emergencyFundProgress}%
                            </span>
                        </div>
                        <div id="progress-description" className="progress-description">
                            Shows your progress toward building a 6-month emergency fund
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Helper function to get field labels
const getFieldLabel = (fieldName) => {
    const labels = {
        annualIncome: 'Annual Income',
        monthlyExpenses: 'Monthly Expenses',
        savingsRate: 'Savings Rate',
        investmentAmount: 'Investment Amount',
        debtAmount: 'Debt Amount',
        creditScore: 'Credit Score'
    };
    return labels[fieldName] || fieldName;
};

// Helper function to format currency
const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount);
};

export default FinancialForm;
