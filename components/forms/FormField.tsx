// components/forms/FormField.tsx
import React, { useState, useEffect } from 'react';
import { FormField as FormFieldType } from '../../types/user';

interface FormFieldProps {
  field: FormFieldType;
  value: any;
  onChange: (name: string, value: any) => void;
  error?: string;
  disabled?: boolean;
  className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({ 
  field, 
  value, 
  onChange, 
  error, 
  disabled = false,
  className = ''
}) => {
  const [localValue, setLocalValue] = useState(value);
  const [isFocused, setIsFocused] = useState(false);

  // Update local value when prop changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    let newValue: any = e.target.value;
    
    // Handle different field types
    switch (field.type) {
      case 'number':
      case 'currency':
        newValue = newValue === '' ? null : parseFloat(newValue);
        if (isNaN(newValue)) newValue = null;
        break;
      
      case 'checkbox':
        newValue = (e.target as HTMLInputElement).checked;
        break;
      
      case 'date':
        newValue = newValue || null;
        break;
      
      default:
        newValue = newValue || '';
    }
    
    setLocalValue(newValue);
    onChange(field.name, newValue);
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(e.target.value);
    setLocalValue(newValue);
    onChange(field.name, newValue);
  };

  const handleRadioChange = (optionValue: string) => {
    setLocalValue(optionValue);
    onChange(field.name, optionValue);
  };

  const getInputClassName = (baseClass: string = '') => {
    const classes = [
      'w-full p-3 border rounded-lg transition-all duration-200',
      'focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
      'disabled:bg-gray-100 disabled:cursor-not-allowed',
      'placeholder-gray-400'
    ];

    if (error) {
      classes.push('border-red-300 focus:ring-red-500 focus:border-red-500');
    } else if (isFocused) {
      classes.push('border-blue-300');
    } else {
      classes.push('border-gray-300');
    }

    if (baseClass) {
      classes.push(baseClass);
    }

    return classes.join(' ');
  };

  const renderInput = () => {
    switch (field.type) {
      case 'select':
        return (
          <select
            id={field.name}
            value={localValue || ''}
            onChange={handleChange}
            className={getInputClassName()}
            required={field.required}
            disabled={disabled}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          >
            <option value="">Select an option...</option>
            {field.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'currency':
        return (
          <div className="relative">
            <span className="absolute left-3 top-3 text-gray-500 pointer-events-none">$</span>
            <input
              type="number"
              id={field.name}
              value={localValue || ''}
              onChange={handleChange}
              placeholder={field.placeholder?.replace('$', '') || '0.00'}
              className={getInputClassName('pl-8')}
              required={field.required}
              disabled={disabled}
              min={field.validation?.min}
              max={field.validation?.max}
              step="0.01"
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
            />
          </div>
        );

      case 'slider':
        const min = field.validation?.min || 1;
        const max = field.validation?.max || 10;
        const currentValue = localValue || min;
        
        return (
          <div className="space-y-3">
            <div className="relative">
              <input
                type="range"
                id={field.name}
                value={currentValue}
                onChange={handleSliderChange}
                min={min}
                max={max}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                disabled={disabled}
              />
              <style jsx>{`
                .slider::-webkit-slider-thumb {
                  appearance: none;
                  height: 20px;
                  width: 20px;
                  border-radius: 50%;
                  background: #3b82f6;
                  cursor: pointer;
                  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }
                .slider::-moz-range-thumb {
                  height: 20px;
                  width: 20px;
                  border-radius: 50%;
                  background: #3b82f6;
                  cursor: pointer;
                  border: none;
                  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }
              `}</style>
            </div>
            <div className="flex justify-between text-sm text-gray-500">
              <span>{min}</span>
              <span className="font-medium text-blue-600">{currentValue}</span>
              <span>{max}</span>
            </div>
          </div>
        );

      case 'radio':
        return (
          <div className="space-y-2">
            {field.options?.map((option) => (
              <label key={option.value} className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name={field.name}
                  value={option.value}
                  checked={localValue === option.value}
                  onChange={() => handleRadioChange(option.value)}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  disabled={disabled}
                />
                <span className="text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        );

      case 'checkbox':
        return (
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              id={field.name}
              checked={localValue || false}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              disabled={disabled}
            />
            <span className="text-gray-700">{field.subtitle || field.label}</span>
          </label>
        );

      case 'textarea':
        return (
          <textarea
            id={field.name}
            value={localValue || ''}
            onChange={handleChange}
            placeholder={field.placeholder}
            className={getInputClassName('resize-none')}
            required={field.required}
            disabled={disabled}
            rows={4}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          />
        );

      case 'tel':
        return (
          <input
            type="tel"
            id={field.name}
            value={localValue || ''}
            onChange={handleChange}
            placeholder={field.placeholder || '(555) 123-4567'}
            className={getInputClassName()}
            required={field.required}
            disabled={disabled}
            pattern="[\+]?[1-9][\d]{0,15}"
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          />
        );

      case 'date':
        return (
          <input
            type="date"
            id={field.name}
            value={localValue || ''}
            onChange={handleChange}
            className={getInputClassName()}
            required={field.required}
            disabled={disabled}
            max={new Date().toISOString().split('T')[0]} // Prevent future dates
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          />
        );

      case 'email':
        return (
          <input
            type="email"
            id={field.name}
            value={localValue || ''}
            onChange={handleChange}
            placeholder={field.placeholder || 'your@email.com'}
            className={getInputClassName()}
            required={field.required}
            disabled={disabled}
            pattern={field.validation?.pattern}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            id={field.name}
            value={localValue || ''}
            onChange={handleChange}
            placeholder={field.placeholder}
            className={getInputClassName()}
            required={field.required}
            disabled={disabled}
            min={field.validation?.min}
            max={field.validation?.max}
            step={field.validation?.step || 1}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          />
        );

      default:
        return (
          <input
            type={field.type}
            id={field.name}
            value={localValue || ''}
            onChange={handleChange}
            placeholder={field.placeholder}
            className={getInputClassName()}
            required={field.required}
            disabled={disabled}
            pattern={field.validation?.pattern}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          />
        );
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {field.type !== 'checkbox' && (
        <label htmlFor={field.name} className="block text-lg font-medium text-gray-900">
          {field.label}
          {field.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      {field.subtitle && field.type !== 'checkbox' && (
        <p className="text-sm text-gray-600">{field.subtitle}</p>
      )}
      
      {renderInput()}
      
      {error && (
        <div className="flex items-center space-x-2 text-sm text-red-600">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span>{error}</span>
        </div>
      )}
      
      {field.validation?.message && !error && (
        <p className="text-xs text-gray-500">{field.validation.message}</p>
      )}
    </div>
  );
}; 