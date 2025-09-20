import React from 'react';
import { CheckCircle, MapPin, Car, Gauge, ArrowRight, ExternalLink } from 'lucide-react';

export interface VehicleSetupSuccessData {
  vehicle_id: number;
  message: string;
  msa_info: {
    msa: string;
    pricing_multiplier: number;
  };
  vehicle_data: {
    year: number;
    make: string;
    model: string;
    trim?: string;
    current_mileage: number;
    monthly_miles: number;
    zipcode: string;
  };
}

interface VehicleSetupSuccessProps {
  data: VehicleSetupSuccessData;
  onClose: () => void;
  onGoToDashboard: () => void;
  onAddAnotherVehicle: () => void;
}

const VehicleSetupSuccess: React.FC<VehicleSetupSuccessProps> = ({
  data,
  onClose,
  onGoToDashboard,
  onAddAnotherVehicle
}) => {
  const { vehicle_data, msa_info } = data;
  
  const formatPricingMultiplier = (multiplier: number) => {
    if (multiplier > 1) {
      return `+${Math.round((multiplier - 1) * 100)}% above national average`;
    } else if (multiplier < 1) {
      return `${Math.round((1 - multiplier) * 100)}% below national average`;
    } else {
      return 'National average pricing';
    }
  };

  const getPricingColor = (multiplier: number) => {
    if (multiplier > 1.1) return 'text-red-400';
    if (multiplier < 0.9) return 'text-green-400';
    return 'text-yellow-400';
  };

  return (
    <div className="space-y-6">
      {/* Success Header */}
      <div className="text-center">
        <div className="mx-auto w-16 h-16 bg-green-500 bg-opacity-20 rounded-full flex items-center justify-center mb-4">
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
        <h3 className="text-2xl font-bold text-white mb-2">
          Vehicle Setup Complete!
        </h3>
        <p className="text-gray-400">
          Your vehicle has been successfully added to your Mingus account
        </p>
      </div>

      {/* Vehicle Summary */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center space-x-3 mb-4">
          <Car className="w-6 h-6 text-violet-400" />
          <h4 className="text-lg font-semibold text-white">Vehicle Details</h4>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-400">Vehicle</p>
            <p className="text-white font-medium">
              {vehicle_data.year} {vehicle_data.make} {vehicle_data.model}
              {vehicle_data.trim && ` ${vehicle_data.trim}`}
            </p>
          </div>
          
          <div>
            <p className="text-sm text-gray-400">Current Mileage</p>
            <p className="text-white font-medium">
              {vehicle_data.current_mileage.toLocaleString()} miles
            </p>
          </div>
          
          <div>
            <p className="text-sm text-gray-400">Monthly Usage</p>
            <p className="text-white font-medium">
              {vehicle_data.monthly_miles.toLocaleString()} miles/month
            </p>
          </div>
          
          <div>
            <p className="text-sm text-gray-400">Location</p>
            <p className="text-white font-medium">
              {vehicle_data.zipcode}
            </p>
          </div>
        </div>
      </div>

      {/* MSA Information */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center space-x-3 mb-4">
          <MapPin className="w-6 h-6 text-violet-400" />
          <h4 className="text-lg font-semibold text-white">Regional Pricing</h4>
        </div>
        
        <div className="space-y-3">
          <div>
            <p className="text-sm text-gray-400">Pricing Region</p>
            <p className="text-white font-medium text-lg">
              {msa_info.msa}
            </p>
          </div>
          
          <div>
            <p className="text-sm text-gray-400">Cost Adjustment</p>
            <p className={`font-medium ${getPricingColor(msa_info.pricing_multiplier)}`}>
              {formatPricingMultiplier(msa_info.pricing_multiplier)}
            </p>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-3">
            <p className="text-xs text-gray-400">
              Maintenance costs will be adjusted based on your location. 
              {msa_info.pricing_multiplier > 1.1 
                ? ' You\'re in a higher-cost area, so we\'ll factor that into your financial planning.'
                : msa_info.pricing_multiplier < 0.9
                ? ' You\'re in a lower-cost area, which means more affordable maintenance costs.'
                : ' Your area has average maintenance costs compared to the national average.'
              }
            </p>
          </div>
        </div>
      </div>

      {/* Usage Analysis */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center space-x-3 mb-4">
          <Gauge className="w-6 h-6 text-violet-400" />
          <h4 className="text-lg font-semibold text-white">Usage Analysis</h4>
        </div>
        
        <div className="space-y-3">
          {vehicle_data.monthly_miles < 500 ? (
            <div className="bg-blue-500 bg-opacity-10 border border-blue-500 rounded-lg p-3">
              <p className="text-blue-400 text-sm font-medium">Low Usage Vehicle</p>
              <p className="text-blue-300 text-xs mt-1">
                Your vehicle is driven less than 500 miles per month. This typically means lower maintenance costs and longer service intervals.
              </p>
            </div>
          ) : vehicle_data.monthly_miles > 1500 ? (
            <div className="bg-orange-500 bg-opacity-10 border border-orange-500 rounded-lg p-3">
              <p className="text-orange-400 text-sm font-medium">High Usage Vehicle</p>
              <p className="text-orange-300 text-xs mt-1">
                Your vehicle is driven more than 1,500 miles per month. This means more frequent maintenance and higher overall costs.
              </p>
            </div>
          ) : (
            <div className="bg-green-500 bg-opacity-10 border border-green-500 rounded-lg p-3">
              <p className="text-green-400 text-sm font-medium">Average Usage Vehicle</p>
              <p className="text-green-300 text-xs mt-1">
                Your vehicle usage is within the normal range. Maintenance costs will be predictable and manageable.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Next Steps */}
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-white mb-3">What's Next?</h4>
        <div className="space-y-2 text-sm text-violet-100">
          <p>• View your personalized maintenance schedule</p>
          <p>• Set up maintenance cost tracking</p>
          <p>• Get insights on fuel costs and efficiency</p>
          <p>• Plan for future vehicle expenses</p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={onGoToDashboard}
          className="flex-1 flex items-center justify-center space-x-2 bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-900"
        >
          <span>Go to Dashboard</span>
          <ArrowRight className="w-4 h-4" />
        </button>
        
        <button
          onClick={onAddAnotherVehicle}
          className="flex-1 flex items-center justify-center space-x-2 bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900"
        >
          <span>Add Another Vehicle</span>
          <Car className="w-4 h-4" />
        </button>
      </div>

      {/* Additional Resources */}
      <div className="text-center">
        <p className="text-gray-400 text-sm mb-3">Need help getting started?</p>
        <div className="flex justify-center space-x-4">
          <button className="text-violet-400 hover:text-violet-300 text-sm font-medium flex items-center space-x-1">
            <ExternalLink className="w-4 h-4" />
            <span>View Tutorial</span>
          </button>
          <button className="text-violet-400 hover:text-violet-300 text-sm font-medium flex items-center space-x-1">
            <ExternalLink className="w-4 h-4" />
            <span>Contact Support</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default VehicleSetupSuccess;
