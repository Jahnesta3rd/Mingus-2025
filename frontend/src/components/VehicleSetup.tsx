import React, { useState, useCallback, useEffect, useRef } from 'react';
import { X, ArrowLeft, ArrowRight, Check, Car, MapPin, Gauge, AlertCircle, Loader2 } from 'lucide-react';
import { InputValidator } from '../utils/validation';
import { Sanitizer } from '../utils/sanitize';
import VehicleSetupSuccess, { VehicleSetupSuccessData } from './VehicleSetupSuccess';

// Types
export interface VehicleSetupData {
  vin?: string;
  year: number;
  make: string;
  model: string;
  trim?: string;
  currentMileage: number;
  monthlyMiles: number;
  zipcode: string;
  msa?: string;
  useVinLookup: boolean;
}

export interface VehicleInfo {
  vin: string;
  year: number;
  make: string;
  model: string;
  trim?: string;
  engine?: string;
  fuelType?: string;
  bodyClass?: string;
  driveType?: string;
  transmission?: string;
  doors?: number;
  windows?: number;
  series?: string;
  plantCity?: string;
  plantState?: string;
  plantCountry?: string;
  manufacturer?: string;
  modelYear?: number;
  vehicleType?: string;
  source?: string;
  lookupTimestamp?: string;
  errorCode?: string;
  errorText?: string;
}

export interface MSAInfo {
  msa: string;
  distance: number;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  error?: string;
}

interface VehicleSetupProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: VehicleSetupData) => void;
  onGoToDashboard?: () => void;
  className?: string;
}

// Popular vehicle data for target demographic
const POPULAR_MAKES = [
  'Honda', 'Toyota', 'Nissan', 'Ford', 'Chevrolet', 'BMW', 'Mercedes-Benz', 
  'Audi', 'Lexus', 'Acura', 'Infiniti', 'Hyundai', 'Kia', 'Mazda', 'Subaru'
];

const POPULAR_MODELS: Record<string, string[]> = {
  'Honda': ['Civic', 'Accord', 'CR-V', 'Pilot', 'HR-V', 'Passport'],
  'Toyota': ['Camry', 'Corolla', 'RAV4', 'Highlander', 'Prius', '4Runner'],
  'Nissan': ['Altima', 'Sentra', 'Rogue', 'Murano', 'Pathfinder', 'Maxima'],
  'Ford': ['F-150', 'Explorer', 'Escape', 'Mustang', 'Edge', 'Expedition'],
  'Chevrolet': ['Silverado', 'Equinox', 'Malibu', 'Tahoe', 'Suburban', 'Camaro'],
  'BMW': ['3 Series', '5 Series', 'X3', 'X5', 'X1', '7 Series'],
  'Mercedes-Benz': ['C-Class', 'E-Class', 'GLC', 'GLE', 'A-Class', 'S-Class'],
  'Audi': ['A4', 'A6', 'Q5', 'Q7', 'A3', 'Q3'],
  'Lexus': ['ES', 'RX', 'IS', 'NX', 'GX', 'LS'],
  'Acura': ['TLX', 'RDX', 'MDX', 'ILX', 'NSX', 'RLX'],
  'Infiniti': ['Q50', 'QX60', 'QX80', 'Q60', 'QX50', 'G37'],
  'Hyundai': ['Elantra', 'Sonata', 'Tucson', 'Santa Fe', 'Palisade', 'Veloster'],
  'Kia': ['Optima', 'Sorento', 'Sportage', 'Telluride', 'Forte', 'Stinger'],
  'Mazda': ['CX-5', 'Mazda3', 'CX-9', 'Mazda6', 'CX-3', 'MX-5 Miata'],
  'Subaru': ['Outback', 'Forester', 'Impreza', 'Legacy', 'Ascent', 'WRX']
};

const YEARS = Array.from({ length: 25 }, (_, i) => new Date().getFullYear() - i);

// Step configurations
const STEPS = [
  {
    id: 'identification',
    title: 'Vehicle Identification',
    description: 'Enter your vehicle details or use VIN lookup',
    icon: <Car className="w-6 h-6" />
  },
  {
    id: 'status',
    title: 'Current Status',
    description: 'Tell us about your vehicle usage',
    icon: <Gauge className="w-6 h-6" />
  },
  {
    id: 'location',
    title: 'Location Information',
    description: 'Help us determine regional pricing',
    icon: <MapPin className="w-6 h-6" />
  }
];

// Loading Skeleton Component
const LoadingSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="h-8 bg-gray-700 rounded w-3/4 mb-4"></div>
    <div className="space-y-3">
      <div className="h-4 bg-gray-700 rounded w-full"></div>
      <div className="h-4 bg-gray-700 rounded w-5/6"></div>
      <div className="h-4 bg-gray-700 rounded w-4/6"></div>
    </div>
  </div>
);

// Main VehicleSetup Component
const VehicleSetup: React.FC<VehicleSetupProps> = ({
  isOpen,
  onClose,
  onSubmit,
  onGoToDashboard,
  className = ''
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<VehicleSetupData>({
    year: new Date().getFullYear(),
    make: '',
    model: '',
    currentMileage: 0,
    monthlyMiles: 0,
    zipcode: '',
    useVinLookup: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [vinLookupData, setVinLookupData] = useState<VehicleInfo | null>(null);
  const [msaInfo, setMsaInfo] = useState<MSAInfo | null>(null);
  const [vinValidationError, setVinValidationError] = useState<string | null>(null);
  const [zipcodeValidationError, setZipcodeValidationError] = useState<string | null>(null);
  const [vinLookupLoading, setVinLookupLoading] = useState(false);
  const [zipcodeLookupLoading, setZipcodeLookupLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [successData, setSuccessData] = useState<VehicleSetupSuccessData | null>(null);
  
  const modalRef = useRef<HTMLDivElement>(null);

  const currentStepConfig = STEPS[currentStep];
  const totalSteps = STEPS.length;

  // Handle modal visibility
  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      setCurrentStep(0);
      setFormData({
        year: new Date().getFullYear(),
        make: '',
        model: '',
        currentMileage: 0,
        monthlyMiles: 0,
        zipcode: '',
        useVinLookup: false
      });
      setError(null);
      setVinLookupData(null);
      setMsaInfo(null);
      setVinValidationError(null);
      setZipcodeValidationError(null);
      setShowSuccess(false);
      setSuccessData(null);
    } else {
      setIsVisible(false);
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  // VIN validation
  const validateVIN = (vin: string): boolean => {
    if (!vin || vin.length !== 17) {
      setVinValidationError('VIN must be exactly 17 characters');
      return false;
    }
    
    const vinRegex = /^[A-HJ-NPR-Z0-9]{17}$/;
    if (!vinRegex.test(vin)) {
      setVinValidationError('VIN contains invalid characters');
      return false;
    }
    
    setVinValidationError(null);
    return true;
  };

  // VIN lookup
  const lookupVIN = useCallback(async (vin: string) => {
    if (!validateVIN(vin)) return;

    setVinLookupLoading(true);
    setVinValidationError(null);

    try {
      const response = await fetch('/api/vehicle-setup/vin-lookup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({ vin, use_cache: true })
      });

      if (!response.ok) {
        throw new Error('VIN lookup failed');
      }

      const data = await response.json();
      
      if (data.success && data.vehicle_info) {
        const vehicleInfo: VehicleInfo = data.vehicle_info;
        setVinLookupData(vehicleInfo);
        
        // Auto-populate form with VIN data
        setFormData(prev => ({
          ...prev,
          year: vehicleInfo.year,
          make: vehicleInfo.make,
          model: vehicleInfo.model,
          trim: vehicleInfo.trim || '',
          vin: vehicleInfo.vin
        }));
      } else {
        setVinValidationError('VIN lookup failed - please enter vehicle details manually');
      }
    } catch (err) {
      setVinValidationError('VIN lookup service unavailable - please enter vehicle details manually');
    } finally {
      setVinLookupLoading(false);
    }
  }, []);

  // ZIP code to MSA lookup
  const lookupMSA = useCallback(async (zipcode: string) => {
    if (!zipcode || zipcode.length !== 5) {
      setZipcodeValidationError('Please enter a valid 5-digit ZIP code');
      return;
    }

    setZipcodeLookupLoading(true);
    setZipcodeValidationError(null);

    try {
      const response = await fetch('/api/vehicle-setup/zipcode-to-msa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({ zipcode })
      });

      if (!response.ok) {
        throw new Error('MSA lookup failed');
      }

      const data = await response.json();
      
      if (data.success && data.msa_info) {
        const msaData: MSAInfo = data.msa_info;
        setMsaInfo(msaData);
        
        // Update form data with MSA
        setFormData(prev => ({
          ...prev,
          msa: msaData.msa
        }));
      } else {
        setZipcodeValidationError('Unable to determine MSA - using national average pricing');
        setMsaInfo({
          msa: 'National Average',
          distance: 999,
          error: 'MSA lookup failed'
        });
      }
    } catch (err) {
      setZipcodeValidationError('MSA lookup service unavailable - using national average pricing');
      setMsaInfo({
        msa: 'National Average',
        distance: 999,
        error: 'Service unavailable'
      });
    } finally {
      setZipcodeLookupLoading(false);
    }
  }, []);

  // Handle form data changes
  const handleFormChange = useCallback((field: keyof VehicleSetupData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear related errors
    if (field === 'vin') {
      setVinValidationError(null);
    } else if (field === 'zipcode') {
      setZipcodeValidationError(null);
    }
  }, []);

  // Handle VIN input with debounced lookup
  const handleVINChange = useCallback((vin: string) => {
    const sanitizedVin = Sanitizer.sanitizeString(vin).toUpperCase();
    handleFormChange('vin', sanitizedVin);
    
    if (sanitizedVin.length === 17) {
      // Debounce VIN lookup
      const timeoutId = setTimeout(() => {
        lookupVIN(sanitizedVin);
      }, 500);
      
      return () => clearTimeout(timeoutId);
    }
  }, [handleFormChange, lookupVIN]);

  // Handle ZIP code input with debounced MSA lookup
  const handleZipcodeChange = useCallback((zipcode: string) => {
    const sanitizedZipcode = Sanitizer.sanitizeString(zipcode).replace(/\D/g, '');
    handleFormChange('zipcode', sanitizedZipcode);
    
    if (sanitizedZipcode.length === 5) {
      // Debounce MSA lookup
      const timeoutId = setTimeout(() => {
        lookupMSA(sanitizedZipcode);
      }, 500);
      
      return () => clearTimeout(timeoutId);
    }
  }, [handleFormChange, lookupMSA]);

  // Handle next step
  const handleNext = useCallback(() => {
    // Validate current step
    let stepValid = true;
    
    if (currentStep === 0) {
      // Vehicle identification step
      if (formData.useVinLookup) {
        if (!formData.vin || vinValidationError) {
          stepValid = false;
          setError('Please enter a valid VIN or switch to manual entry');
        }
      } else {
        if (!formData.year || !formData.make || !formData.model) {
          stepValid = false;
          setError('Please fill in all required vehicle details');
        }
      }
    } else if (currentStep === 1) {
      // Status step
      if (!formData.currentMileage || formData.currentMileage < 0) {
        stepValid = false;
        setError('Please enter a valid current mileage');
      } else if (!formData.monthlyMiles || formData.monthlyMiles < 0) {
        stepValid = false;
        setError('Please enter a valid monthly mileage');
      }
    } else if (currentStep === 2) {
      // Location step
      if (!formData.zipcode || formData.zipcode.length !== 5) {
        stepValid = false;
        setError('Please enter a valid 5-digit ZIP code');
      }
    }

    if (!stepValid) {
      return;
    }

    if (currentStep < totalSteps - 1) {
      setCurrentStep(prev => prev + 1);
      setError(null);
    } else {
      handleSubmit();
    }
  }, [currentStep, totalSteps, formData, vinValidationError]);

  // Handle previous step
  const handlePrevious = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
      setError(null);
    }
  }, [currentStep]);

  // Handle form submission
  const handleSubmit = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Final validation
      const validation = InputValidator.validateAssessmentAnswers(formData as any);
      if (!validation.isValid) {
        setError(`Validation failed: ${validation.errors.join(', ')}`);
        setLoading(false);
        return;
      }

      // Submit to API
      const response = await fetch('/api/vehicle-setup/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to submit vehicle setup');
      }

      const result = await response.json();
      
      if (result.success) {
        // Prepare success data
        const successData: VehicleSetupSuccessData = {
          vehicle_id: result.vehicle_id,
          message: result.message,
          msa_info: result.msa_info,
          vehicle_data: {
            year: formData.year,
            make: formData.make,
            model: formData.model,
            trim: formData.trim,
            current_mileage: formData.current_mileage,
            monthly_miles: formData.monthly_miles,
            zipcode: formData.zipcode
          }
        };

        setSuccessData(successData);
        setShowSuccess(true);
        
        // Also call the original onSubmit callback
        onSubmit(formData);
      } else {
        throw new Error(result.error || 'Failed to submit vehicle setup');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save vehicle setup. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [formData, onSubmit]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleNext();
    }
  }, [handleNext]);

  // Handle success flow actions
  const handleGoToDashboard = useCallback(() => {
    if (onGoToDashboard) {
      onGoToDashboard();
    } else {
      // Default behavior - close modal and redirect
      onClose();
      window.location.href = '/dashboard';
    }
  }, [onGoToDashboard, onClose]);

  const handleAddAnotherVehicle = useCallback(() => {
    setShowSuccess(false);
    setSuccessData(null);
    setCurrentStep(0);
    setFormData({
      year: new Date().getFullYear(),
      make: '',
      model: '',
      currentMileage: 0,
      monthlyMiles: 0,
      zipcode: '',
      useVinLookup: false
    });
    setError(null);
    setVinLookupData(null);
    setMsaInfo(null);
    setVinValidationError(null);
    setZipcodeValidationError(null);
  }, []);

  if (!isOpen) return null;

  // Show success screen if setup is complete
  if (showSuccess && successData) {
    return (
      <div 
        className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 transition-all duration-300 ${
          isVisible ? 'opacity-100' : 'opacity-0'
        } ${className}`}
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <div 
          ref={modalRef}
          className={`bg-gray-900 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden transition-all duration-300 ${
            isVisible ? 'scale-100' : 'scale-95'
          }`}
        >
          {/* Success Header */}
          <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-6 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="text-green-200">
                  <Check className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">Setup Complete!</h2>
                  <p className="text-green-100 text-sm">Your vehicle has been added successfully</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-green-200 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-green-600 rounded p-1"
                aria-label="Close vehicle setup"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Success Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
            <VehicleSetupSuccess
              data={successData}
              onClose={onClose}
              onGoToDashboard={handleGoToDashboard}
              onAddAnotherVehicle={handleAddAnotherVehicle}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 transition-all duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      } ${className}`}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div 
        ref={modalRef}
        className={`bg-gray-900 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden transition-all duration-300 ${
          isVisible ? 'scale-100' : 'scale-95'
        }`}
        onKeyDown={handleKeyDown}
        tabIndex={-1}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="text-violet-200">
                {currentStepConfig.icon}
              </div>
              <div>
                <h2 className="text-xl font-bold">Vehicle Setup</h2>
                <p className="text-violet-100 text-sm">{currentStepConfig.description}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-violet-200 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-violet-600 rounded p-1"
              aria-label="Close vehicle setup"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-violet-400 bg-opacity-30 rounded-full h-3 mb-2">
            <div 
              className="bg-white h-3 rounded-full transition-all duration-500 ease-out shadow-lg"
              style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
            />
          </div>
          <div className="flex items-center justify-between">
            <p className="text-violet-100 text-sm font-medium">
              Step {currentStep + 1} of {totalSteps}
            </p>
            <p className="text-violet-200 text-xs">
              {currentStepConfig.title}
            </p>
          </div>
          <div className="mt-1 text-xs text-violet-200">
            {Math.round(((currentStep + 1) / totalSteps) * 100)}% Complete
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {loading ? (
            <LoadingSkeleton />
          ) : (
            <div className="space-y-6">
              {/* Step Progress Indicator */}
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-violet-300">
                    Step {currentStep + 1} of {totalSteps}
                  </span>
                  <span className="text-xs text-gray-400">
                    {Math.round(((currentStep + 1) / totalSteps) * 100)}% Complete
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div 
                    className="bg-gradient-to-r from-violet-500 to-purple-500 h-1.5 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
                  />
                </div>
              </div>

              {/* Step 1: Vehicle Identification */}
              {currentStep === 0 && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">
                      How would you like to identify your vehicle?
                    </h3>
                    <p className="text-gray-400 text-sm mb-4">
                      You can use VIN lookup for automatic details or enter them manually
                    </p>
                  </div>

                  {/* VIN Lookup Option */}
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <input
                        type="radio"
                        id="vin-lookup"
                        name="identification-method"
                        checked={formData.useVinLookup}
                        onChange={(e) => handleFormChange('useVinLookup', e.target.checked)}
                        className="w-4 h-4 text-violet-600 bg-gray-800 border-gray-600 focus:ring-violet-400 focus:ring-2"
                      />
                      <label htmlFor="vin-lookup" className="text-white font-medium">
                        Use VIN Lookup (Recommended)
                      </label>
                    </div>

                    {formData.useVinLookup && (
                      <div className="ml-7 space-y-3">
                        <div>
                          <label htmlFor="vin-input" className="block text-sm font-medium text-white mb-2">
                            Vehicle Identification Number (VIN)
                          </label>
                          <div className="relative">
                            <input
                              id="vin-input"
                              type="text"
                              value={formData.vin || ''}
                              onChange={(e) => handleVINChange(e.target.value)}
                              placeholder="Enter 17-character VIN"
                              maxLength={17}
                              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900 font-mono text-sm"
                            />
                            {vinLookupLoading && (
                              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                                <Loader2 className="w-5 h-5 text-violet-400 animate-spin" />
                              </div>
                            )}
                          </div>
                          {vinValidationError && (
                            <p className="text-red-400 text-sm mt-1 flex items-center">
                              <AlertCircle className="w-4 h-4 mr-1" />
                              {vinValidationError}
                            </p>
                          )}
                          {vinLookupData && (
                            <div className="mt-3 p-3 bg-green-500 bg-opacity-10 border border-green-500 rounded-lg">
                              <p className="text-green-400 text-sm font-medium">
                                ✓ VIN lookup successful
                              </p>
                              <p className="text-green-300 text-xs mt-1">
                                {vinLookupData.year} {vinLookupData.make} {vinLookupData.model}
                                {vinLookupData.trim && ` ${vinLookupData.trim}`}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Manual Entry Option */}
                    <div className="flex items-center space-x-3">
                      <input
                        type="radio"
                        id="manual-entry"
                        name="identification-method"
                        checked={!formData.useVinLookup}
                        onChange={(e) => handleFormChange('useVinLookup', !e.target.checked)}
                        className="w-4 h-4 text-violet-600 bg-gray-800 border-gray-600 focus:ring-violet-400 focus:ring-2"
                      />
                      <label htmlFor="manual-entry" className="text-white font-medium">
                        Enter Details Manually
                      </label>
                    </div>

                    {!formData.useVinLookup && (
                      <div className="ml-7 space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label htmlFor="year-select" className="block text-sm font-medium text-white mb-2">
                              Year *
                            </label>
                            <select
                              id="year-select"
                              value={formData.year}
                              onChange={(e) => handleFormChange('year', parseInt(e.target.value))}
                              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                            >
                              <option value="">Select Year</option>
                              {YEARS.map(year => (
                                <option key={year} value={year}>{year}</option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label htmlFor="make-select" className="block text-sm font-medium text-white mb-2">
                              Make *
                            </label>
                            <select
                              id="make-select"
                              value={formData.make}
                              onChange={(e) => {
                                handleFormChange('make', e.target.value);
                                handleFormChange('model', ''); // Reset model when make changes
                              }}
                              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                            >
                              <option value="">Select Make</option>
                              {POPULAR_MAKES.map(make => (
                                <option key={make} value={make}>{make}</option>
                              ))}
                            </select>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label htmlFor="model-select" className="block text-sm font-medium text-white mb-2">
                              Model *
                            </label>
                            <select
                              id="model-select"
                              value={formData.model}
                              onChange={(e) => handleFormChange('model', e.target.value)}
                              disabled={!formData.make}
                              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <option value="">Select Model</option>
                              {formData.make && POPULAR_MODELS[formData.make]?.map(model => (
                                <option key={model} value={model}>{model}</option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label htmlFor="trim-input" className="block text-sm font-medium text-white mb-2">
                              Trim (Optional)
                            </label>
                            <input
                              id="trim-input"
                              type="text"
                              value={formData.trim || ''}
                              onChange={(e) => handleFormChange('trim', e.target.value)}
                              placeholder="e.g., EX, LX, Sport"
                              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Step 2: Current Status */}
              {currentStep === 1 && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Tell us about your vehicle's current status
                    </h3>
                    <p className="text-gray-400 text-sm mb-4">
                      This helps us provide accurate maintenance predictions and cost estimates
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="current-mileage" className="block text-sm font-medium text-white mb-2">
                        Current Mileage *
                      </label>
                      <div className="relative">
                        <input
                          id="current-mileage"
                          type="number"
                          value={formData.currentMileage || ''}
                          onChange={(e) => handleFormChange('currentMileage', parseInt(e.target.value) || 0)}
                          placeholder="e.g., 45000"
                          min="0"
                          max="999999"
                          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                        />
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm">
                          miles
                        </div>
                      </div>
                      <p className="text-gray-400 text-xs mt-1">
                        Current odometer reading
                      </p>
                    </div>

                    <div>
                      <label htmlFor="monthly-miles" className="block text-sm font-medium text-white mb-2">
                        Monthly Driving *
                      </label>
                      <div className="relative">
                        <input
                          id="monthly-miles"
                          type="number"
                          value={formData.monthlyMiles || ''}
                          onChange={(e) => handleFormChange('monthlyMiles', parseInt(e.target.value) || 0)}
                          placeholder="e.g., 1200"
                          min="0"
                          max="10000"
                          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                        />
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm">
                          miles
                        </div>
                      </div>
                      <p className="text-gray-400 text-xs mt-1">
                        Average miles driven per month
                      </p>
                    </div>
                  </div>

                  {/* Usage Guidelines */}
                  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                    <h4 className="text-sm font-medium text-violet-300 mb-2">Usage Guidelines</h4>
                    <div className="text-xs text-gray-400 space-y-1">
                      <p>• <strong>Low usage:</strong> Less than 500 miles/month</p>
                      <p>• <strong>Average usage:</strong> 500-1,500 miles/month</p>
                      <p>• <strong>High usage:</strong> More than 1,500 miles/month</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 3: Location Information */}
              {currentStep === 2 && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Where is your vehicle primarily located?
                    </h3>
                    <p className="text-gray-400 text-sm mb-4">
                      We use your location to determine regional pricing for maintenance and services
                    </p>
                  </div>

                  <div>
                    <label htmlFor="zipcode-input" className="block text-sm font-medium text-white mb-2">
                      ZIP Code *
                    </label>
                    <div className="relative">
                      <input
                        id="zipcode-input"
                        type="text"
                        value={formData.zipcode}
                        onChange={(e) => handleZipcodeChange(e.target.value)}
                        placeholder="Enter 5-digit ZIP code"
                        maxLength={5}
                        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                      />
                      {zipcodeLookupLoading && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                          <Loader2 className="w-5 h-5 text-violet-400 animate-spin" />
                        </div>
                      )}
                    </div>
                    {zipcodeValidationError && (
                      <p className="text-red-400 text-sm mt-1 flex items-center">
                        <AlertCircle className="w-4 h-4 mr-1" />
                        {zipcodeValidationError}
                      </p>
                    )}
                    {msaInfo && (
                      <div className={`mt-3 p-3 rounded-lg border ${
                        msaInfo.error 
                          ? 'bg-yellow-500 bg-opacity-10 border-yellow-500' 
                          : 'bg-green-500 bg-opacity-10 border-green-500'
                      }`}>
                        <p className={`text-sm font-medium ${
                          msaInfo.error ? 'text-yellow-400' : 'text-green-400'
                        }`}>
                          {msaInfo.error ? '⚠️' : '✓'} Pricing Region: {msaInfo.msa}
                        </p>
                        {!msaInfo.error && (
                          <p className="text-green-300 text-xs mt-1">
                            Distance: {msaInfo.distance.toFixed(1)} miles from MSA center
                          </p>
                        )}
                        {msaInfo.error && (
                          <p className="text-yellow-300 text-xs mt-1">
                            Using national average pricing
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* MSA Information */}
                  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                    <h4 className="text-sm font-medium text-violet-300 mb-2">Regional Pricing</h4>
                    <div className="text-xs text-gray-400 space-y-1">
                      <p>• We use your ZIP code to determine the closest Metropolitan Statistical Area (MSA)</p>
                      <p>• Maintenance costs are adjusted based on regional pricing differences</p>
                      <p>• If you're outside our coverage area, we'll use national average pricing</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="bg-red-500 bg-opacity-10 border border-red-500 text-red-300 px-4 py-3 rounded-lg flex items-center">
                  <AlertCircle className="w-5 h-5 mr-2" />
                  {error}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-800 px-6 py-4 flex items-center justify-between">
          <button
            onClick={currentStep > 0 ? handlePrevious : onClose}
            className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800 rounded px-2 py-1"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{currentStep > 0 ? 'Previous' : 'Cancel'}</span>
          </button>

          <button
            onClick={handleNext}
            disabled={loading}
            className="flex items-center space-x-2 bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 disabled:from-gray-600 disabled:to-gray-600 text-white px-6 py-2 rounded-lg font-semibold transition-all duration-200 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-800"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            ) : currentStep === totalSteps - 1 ? (
              <>
                <span>Complete Setup</span>
                <Check className="w-4 h-4" />
              </>
            ) : (
              <>
                <span>Next Step</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default VehicleSetup;
