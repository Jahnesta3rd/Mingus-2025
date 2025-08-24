// components/forms/FormSection.tsx
import React from 'react';
import { FormField } from './FormField';
import { FormField as FormFieldType } from '../../types/user';

interface FormSectionProps {
  title: string;
  subtitle?: string;
  fields: FormFieldType[];
  data: Record<string, any>;
  onChange: (name: string, value: any) => void;
  errors?: Record<string, string>;
  disabled?: boolean;
  className?: string;
}

export const FormSection: React.FC<FormSectionProps> = ({
  title,
  subtitle,
  fields,
  data,
  onChange,
  errors = {},
  disabled = false,
  className = ''
}) => {
  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
        {subtitle && (
          <p className="mt-1 text-sm text-gray-600">{subtitle}</p>
        )}
      </div>
      
      <div className="space-y-6">
        {fields.map((field) => (
          <FormField
            key={field.name}
            field={field}
            value={data[field.name]}
            onChange={onChange}
            error={errors[field.name]}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
}; 