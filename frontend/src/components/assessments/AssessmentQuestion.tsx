import React, { useState, useRef, useEffect } from 'react';

// Types
interface QuestionOption {
  value: string;
  label: string;
}

interface Question {
  id: string;
  type: 'text' | 'select' | 'multi_select' | 'radio' | 'number' | 'email';
  text: string;
  required: boolean;
  options?: QuestionOption[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
  skip_logic?: {
    condition: string;
    value: string;
    skip_to: string;
  };
}

interface AssessmentQuestionProps {
  question: Question;
  value: any;
  error?: string;
  onChange: (value: any) => void;
}

const AssessmentQuestion: React.FC<AssessmentQuestionProps> = ({
  question,
  value,
  error,
  onChange,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(null);

  // Auto-focus on mount for better UX
  useEffect(() => {
    if (inputRef.current && question.type !== 'multi_select' && question.type !== 'radio') {
      inputRef.current.focus();
    }
  }, [question.id, question.type]);

  // Handle text input
  const renderTextInput = () => (
    <input
      ref={inputRef as React.RefObject<HTMLInputElement>}
      type={question.type === 'email' ? 'email' : 'text'}
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      className={`w-full px-4 py-3 border rounded-lg text-lg transition-all duration-200 ${
        error
          ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
          : isFocused
          ? 'border-purple-500 focus:border-purple-500 focus:ring-purple-500'
          : 'border-gray-300 focus:border-purple-500 focus:ring-purple-500'
      } focus:ring-2 focus:ring-opacity-20 focus:outline-none`}
      placeholder={`Enter your ${question.type === 'email' ? 'email address' : 'answer'}...`}
      aria-describedby={error ? `${question.id}-error` : undefined}
      aria-invalid={!!error}
      minHeight="44px"
    />
  );

  // Handle number input
  const renderNumberInput = () => (
    <input
      ref={inputRef as React.RefObject<HTMLInputElement>}
      type="number"
      value={value || ''}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : '')}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      min={question.validation?.min}
      max={question.validation?.max}
      className={`w-full px-4 py-3 border rounded-lg text-lg transition-all duration-200 ${
        error
          ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
          : isFocused
          ? 'border-purple-500 focus:border-purple-500 focus:ring-purple-500'
          : 'border-gray-300 focus:border-purple-500 focus:ring-purple-500'
      } focus:ring-2 focus:ring-opacity-20 focus:outline-none`}
      placeholder="Enter a number..."
      aria-describedby={error ? `${question.id}-error` : undefined}
      aria-invalid={!!error}
      minHeight="44px"
    />
  );

  // Handle select dropdown
  const renderSelect = () => (
    <div className="relative">
      <select
        ref={inputRef as React.RefObject<HTMLSelectElement>}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        className={`w-full px-4 py-3 border rounded-lg text-lg appearance-none transition-all duration-200 ${
          error
            ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
            : isFocused
            ? 'border-purple-500 focus:border-purple-500 focus:ring-purple-500'
            : 'border-gray-300 focus:border-purple-500 focus:ring-purple-500'
        } focus:ring-2 focus:ring-opacity-20 focus:outline-none bg-white`}
        aria-describedby={error ? `${question.id}-error` : undefined}
        aria-invalid={!!error}
        minHeight="44px"
      >
        <option value="">Select an option...</option>
        {question.options?.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {/* Custom dropdown arrow */}
      <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );

  // Handle radio buttons
  const renderRadioButtons = () => (
    <div className="space-y-3" role="radiogroup" aria-labelledby={`${question.id}-label`}>
      {question.options?.map((option) => (
        <label
          key={option.value}
          className={`flex items-center p-4 border rounded-lg cursor-pointer transition-all duration-200 min-h-[44px] ${
            value === option.value
              ? 'border-purple-500 bg-purple-50'
              : 'border-gray-300 hover:border-purple-300 hover:bg-gray-50'
          }`}
        >
          <input
            type="radio"
            name={question.id}
            value={option.value}
            checked={value === option.value}
            onChange={(e) => onChange(e.target.value)}
            className="sr-only"
            aria-describedby={error ? `${question.id}-error` : undefined}
          />
          <div className={`w-5 h-5 border-2 rounded-full mr-3 flex items-center justify-center ${
            value === option.value
              ? 'border-purple-500 bg-purple-500'
              : 'border-gray-300'
          }`}>
            {value === option.value && (
              <div className="w-2 h-2 bg-white rounded-full"></div>
            )}
          </div>
          <span className="text-lg text-gray-900">{option.label}</span>
        </label>
      ))}
    </div>
  );

  // Handle multi-select checkboxes
  const renderMultiSelect = () => {
    const selectedValues = Array.isArray(value) ? value : [];
    
    const handleOptionChange = (optionValue: string, checked: boolean) => {
      if (checked) {
        onChange([...selectedValues, optionValue]);
      } else {
        onChange(selectedValues.filter(v => v !== optionValue));
      }
    };

    return (
      <div className="space-y-3" role="group" aria-labelledby={`${question.id}-label`}>
        {question.options?.map((option) => (
          <label
            key={option.value}
            className={`flex items-center p-4 border rounded-lg cursor-pointer transition-all duration-200 min-h-[44px] ${
              selectedValues.includes(option.value)
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-300 hover:border-purple-300 hover:bg-gray-50'
            }`}
          >
            <input
              type="checkbox"
              value={option.value}
              checked={selectedValues.includes(option.value)}
              onChange={(e) => handleOptionChange(option.value, e.target.checked)}
              className="sr-only"
              aria-describedby={error ? `${question.id}-error` : undefined}
            />
            <div className={`w-5 h-5 border-2 rounded mr-3 flex items-center justify-center ${
              selectedValues.includes(option.value)
                ? 'border-purple-500 bg-purple-500'
                : 'border-gray-300'
            }`}>
              {selectedValues.includes(option.value) && (
                <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <span className="text-lg text-gray-900">{option.label}</span>
          </label>
        ))}
      </div>
    );
  };

  // Render appropriate input based on question type
  const renderInput = () => {
    switch (question.type) {
      case 'text':
      case 'email':
        return renderTextInput();
      case 'number':
        return renderNumberInput();
      case 'select':
        return renderSelect();
      case 'radio':
        return renderRadioButtons();
      case 'multi_select':
        return renderMultiSelect();
      default:
        return renderTextInput();
    }
  };

  return (
    <div className="space-y-4">
      {/* Question Text */}
      <div>
        <h2 
          id={`${question.id}-label`}
          className="text-2xl font-semibold text-gray-900 mb-2"
        >
          {question.text}
          {question.required && <span className="text-red-500 ml-1">*</span>}
        </h2>
        
        {/* Question Type Indicator */}
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <span className="capitalize">{question.type.replace('_', ' ')}</span>
          {question.required && <span>• Required</span>}
        </div>
      </div>

      {/* Input Field */}
      <div>
        {renderInput()}
        
        {/* Error Message */}
        {error && (
          <div 
            id={`${question.id}-error`}
            className="mt-2 text-sm text-red-600 flex items-center"
            role="alert"
          >
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}

        {/* Help Text */}
        {question.validation?.message && !error && (
          <div className="mt-2 text-sm text-gray-500">
            {question.validation.message}
          </div>
        )}
      </div>

      {/* Character Count (for text inputs) */}
      {(question.type === 'text' || question.type === 'email') && value && (
        <div className="text-sm text-gray-500 text-right">
          {value.length} characters
        </div>
      )}

      {/* Selected Count (for multi-select) */}
      {question.type === 'multi_select' && Array.isArray(value) && value.length > 0 && (
        <div className="text-sm text-purple-600 font-medium">
          {value.length} option{value.length !== 1 ? 's' : ''} selected
        </div>
      )}
    </div>
  );
};

export default AssessmentQuestion;
