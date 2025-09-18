import React, { useState } from 'react';
import { Car, Plus } from 'lucide-react';
import VehicleSetup, { VehicleSetupData } from './VehicleSetup';

const VehicleSetupExample: React.FC = () => {
  const [isVehicleSetupOpen, setIsVehicleSetupOpen] = useState(false);
  const [vehicles, setVehicles] = useState<VehicleSetupData[]>([]);

  const handleVehicleSubmit = (data: VehicleSetupData) => {
    console.log('Vehicle submitted:', data);
    setVehicles(prev => [...prev, data]);
  };

  const handleGoToDashboard = () => {
    console.log('Navigate to dashboard');
    // In a real app, this would navigate to the dashboard
    window.location.href = '/dashboard';
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">
            Mingus Vehicle Management
          </h1>
          <p className="text-gray-400 text-lg">
            Track your vehicles and optimize your transportation costs
          </p>
        </div>

        {/* Add Vehicle Button */}
        <div className="text-center mb-8">
          <button
            onClick={() => setIsVehicleSetupOpen(true)}
            className="inline-flex items-center space-x-2 bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
          >
            <Plus className="w-6 h-6" />
            <span>Add Vehicle</span>
          </button>
        </div>

        {/* Vehicles List */}
        {vehicles.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white mb-4">Your Vehicles</h2>
            {vehicles.map((vehicle, index) => (
              <div
                key={index}
                className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors duration-200"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-violet-500 bg-opacity-20 rounded-lg flex items-center justify-center">
                    <Car className="w-6 h-6 text-violet-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white">
                      {vehicle.year} {vehicle.make} {vehicle.model}
                      {vehicle.trim && ` ${vehicle.trim}`}
                    </h3>
                    <div className="flex items-center space-x-6 text-sm text-gray-400 mt-1">
                      <span>{vehicle.currentMileage.toLocaleString()} miles</span>
                      <span>{vehicle.monthlyMiles.toLocaleString()} miles/month</span>
                      <span>{vehicle.zipcode}</span>
                      {vehicle.msa && <span>{vehicle.msa}</span>}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-400">Status</div>
                    <div className="text-green-400 font-medium">Active</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {vehicles.length === 0 && (
          <div className="text-center py-12">
            <div className="w-24 h-24 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <Car className="w-12 h-12 text-gray-600" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              No vehicles added yet
            </h3>
            <p className="text-gray-400 mb-6">
              Add your first vehicle to start tracking maintenance costs and optimizing your transportation budget.
            </p>
            <button
              onClick={() => setIsVehicleSetupOpen(true)}
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
            >
              <Plus className="w-5 h-5" />
              <span>Add Your First Vehicle</span>
            </button>
          </div>
        )}

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="w-12 h-12 bg-blue-500 bg-opacity-20 rounded-lg flex items-center justify-center mb-4">
              <Car className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Maintenance Tracking
            </h3>
            <p className="text-gray-400 text-sm">
              Get personalized maintenance schedules and cost predictions based on your vehicle and usage.
            </p>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="w-12 h-12 bg-green-500 bg-opacity-20 rounded-lg flex items-center justify-center mb-4">
              <Car className="w-6 h-6 text-green-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Regional Pricing
            </h3>
            <p className="text-gray-400 text-sm">
              Accurate cost estimates based on your location and regional pricing differences.
            </p>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="w-12 h-12 bg-purple-500 bg-opacity-20 rounded-lg flex items-center justify-center mb-4">
              <Car className="w-6 h-6 text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Financial Planning
            </h3>
            <p className="text-gray-400 text-sm">
              Integrate vehicle costs into your overall financial planning and budgeting.
            </p>
          </div>
        </div>
      </div>

      {/* Vehicle Setup Modal */}
      <VehicleSetup
        isOpen={isVehicleSetupOpen}
        onClose={() => setIsVehicleSetupOpen(false)}
        onSubmit={handleVehicleSubmit}
        onGoToDashboard={handleGoToDashboard}
      />
    </div>
  );
};

export default VehicleSetupExample;
