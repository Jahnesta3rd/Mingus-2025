import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { MapPin, Users, DollarSign, TrendingUp } from 'lucide-react';

const demographicData = [
  {
    rank: 1,
    metro: "Atlanta-Sandy Springs-Alpharetta, GA",
    state: "Georgia",
    population: 285000,
    extended30Mile: 95000,
    percentage: 18.2,
    medianIncome: 58000,
    coordinates: { lat: 33.7490, lng: -84.3880 },
    region: "South",
    extendedAreas: "Rome, Gainesville, LaGrange, Griffin"
  },
  {
    rank: 2,
    metro: "Washington-Arlington-Alexandria, DC-VA-MD",
    state: "DC/VA/MD",
    population: 245000,
    extended30Mile: 75000,
    percentage: 15.8,
    medianIncome: 72000,
    coordinates: { lat: 38.9072, lng: -77.0369 },
    region: "South",
    extendedAreas: "Winchester, Warrenton, Leonardtown"
  },
  {
    rank: 3,
    metro: "Houston-The Woodlands-Sugar Land, TX",
    state: "Texas",
    population: 220000,
    extended30Mile: 88000,
    percentage: 14.1,
    medianIncome: 61000,
    coordinates: { lat: 29.7604, lng: -95.3698 },
    region: "South",
    extendedAreas: "Huntsville, Brenham, Bay City, Cleveland"
  },
  {
    rank: 4,
    metro: "Dallas-Fort Worth-Arlington, TX",
    state: "Texas",
    population: 195000,
    extended30Mile: 72000,
    percentage: 12.5,
    medianIncome: 59000,
    coordinates: { lat: 32.7767, lng: -96.7970 },
    region: "South",
    extendedAreas: "Tyler, Corsicana, Gainesville, Sherman"
  },
  {
    rank: 5,
    metro: "New York-Newark-Jersey City, NY-NJ-PA",
    state: "NY/NJ/PA",
    population: 180000,
    extended30Mile: 65000,
    percentage: 11.6,
    medianIncome: 68000,
    coordinates: { lat: 40.7128, lng: -74.0060 },
    region: "Northeast",
    extendedAreas: "Poughkeepsie, Bridgeport, New Haven"
  },
  {
    rank: 6,
    metro: "Philadelphia-Camden-Wilmington, PA-NJ-DE",
    state: "PA/NJ/DE",
    population: 165000,
    extended30Mile: 58000,
    percentage: 10.6,
    medianIncome: 55000,
    coordinates: { lat: 39.9526, lng: -75.1652 },
    region: "Northeast",
    extendedAreas: "Lancaster, Reading, Atlantic City"
  },
  {
    rank: 7,
    metro: "Miami-Fort Lauderdale-West Palm Beach, FL",
    state: "Florida",
    population: 155000,
    extended30Mile: 42000,
    percentage: 9.9,
    medianIncome: 52000,
    coordinates: { lat: 25.7617, lng: -80.1918 },
    region: "South",
    extendedAreas: "Naples, Key Largo, Okeechobee"
  },
  {
    rank: 8,
    metro: "Chicago-Naperville-Elgin, IL-IN-WI",
    state: "IL/IN/WI",
    population: 148000,
    extended30Mile: 52000,
    percentage: 9.5,
    medianIncome: 63000,
    coordinates: { lat: 41.8781, lng: -87.6298 },
    region: "Midwest",
    extendedAreas: "Milwaukee, Rockford, Kankakee"
  },
  {
    rank: 9,
    metro: "Baltimore-Columbia-Towson, MD",
    state: "Maryland",
    population: 135000,
    extended30Mile: 35000,
    percentage: 8.7,
    medianIncome: 66000,
    coordinates: { lat: 39.2904, lng: -76.6122 },
    region: "South",
    extendedAreas: "York, Easton, Cambridge"
  },
  {
    rank: 10,
    metro: "Charlotte-Concord-Gastonia, NC-SC",
    state: "NC/SC",
    population: 125000,
    extended30Mile: 48000,
    percentage: 8.0,
    medianIncome: 56000,
    coordinates: { lat: 35.2271, lng: -80.8431 },
    region: "South",
    extendedAreas: "Hickory, Shelby, Monroe, Rock Hill"
  }
];

const regionData = [
  { name: 'South', value: 7, color: '#FF6B6B' },
  { name: 'Northeast', value: 2, color: '#4ECDC4' },
  { name: 'Midwest', value: 1, color: '#45B7D1' }
];

const AfricanAmericanDemographics = () => {
  const [selectedView, setSelectedView] = useState('bar');
  const [hoveredArea, setHoveredArea] = useState(null);

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">
            Top 10 US Metropolitan Areas
          </h1>
          <p className="text-xl text-purple-200 mb-2">
            African American Population (Ages 25-40, Income $40K-$100K)
          </p>
          <div className="flex justify-center items-center gap-6 text-purple-300">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              <span>Target Demographics</span>
            </div>
            <div className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              <span>Middle Income Range</span>
            </div>
            <div className="flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              <span>Metropolitan Areas</span>
            </div>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex justify-center mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-2 border border-white/20">
            <button
              onClick={() => setSelectedView('bar')}
              className={`px-4 py-2 rounded-lg transition-all text-sm ${
                selectedView === 'bar'
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'text-purple-200 hover:bg-white/10'
              }`}
            >
              MSA Population
            </button>
            <button
              onClick={() => setSelectedView('extended')}
              className={`px-4 py-2 rounded-lg transition-all text-sm ${
                selectedView === 'extended'
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'text-purple-200 hover:bg-white/10'
              }`}
            >
              30-Mile Extended
            </button>
            <button
              onClick={() => setSelectedView('income')}
              className={`px-4 py-2 rounded-lg transition-all text-sm ${
                selectedView === 'income'
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'text-purple-200 hover:bg-white/10'
              }`}
            >
              Income Analysis
            </button>
            <button
              onClick={() => setSelectedView('regions')}
              className={`px-4 py-2 rounded-lg transition-all text-sm ${
                selectedView === 'regions'
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'text-purple-200 hover:bg-white/10'
              }`}
            >
              Regional Distribution
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Chart Section */}
          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
              {selectedView === 'extended' && (
                <>
                  <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                    <MapPin className="w-6 h-6 text-orange-400" />
                    MSA vs 30-Mile Extended Area Population
                  </h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={demographicData} margin={{ top: 20, right: 30, left: 20, bottom: 100 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis 
                        dataKey="metro" 
                        stroke="#e2e8f0"
                        fontSize={10}
                        angle={-45}
                        textAnchor="end"
                        height={100}
                      />
                      <YAxis stroke="#e2e8f0" />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: 'rgba(30, 41, 59, 0.95)',
                          border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '12px',
                          color: 'white'
                        }}
                        formatter={(value, name) => [
                          formatNumber(value), 
                          name === 'population' ? 'MSA Population' : '30-Mile Extended'
                        ]}
                      />
                      <Bar 
                        dataKey="population" 
                        fill="url(#msaGradient)"
                        radius={[4, 4, 0, 0]}
                        name="population"
                      />
                      <Bar 
                        dataKey="extended30Mile" 
                        fill="url(#extendedGradient)"
                        radius={[4, 4, 0, 0]}
                        name="extended30Mile"
                      />
                      <defs>
                        <linearGradient id="msaGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#8B5CF6" />
                          <stop offset="100%" stopColor="#3B82F6" />
                        </linearGradient>
                        <linearGradient id="extendedGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#F59E0B" />
                          <stop offset="100%" stopColor="#D97706" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="mt-4 flex justify-center gap-6 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-gradient-to-b from-purple-500 to-blue-500 rounded"></div>
                      <span className="text-purple-200">MSA Population</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 bg-gradient-to-b from-amber-500 to-orange-600 rounded"></div>
                      <span className="text-purple-200">30-Mile Extended</span>
                    </div>
                  </div>
                </>
              )}

              {selectedView === 'bar' && (
                <>
                  <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                    <TrendingUp className="w-6 h-6 text-purple-400" />
                    Population by Metropolitan Area
                  </h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={demographicData} margin={{ top: 20, right: 30, left: 20, bottom: 100 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis 
                        dataKey="metro" 
                        stroke="#e2e8f0"
                        fontSize={10}
                        angle={-45}
                        textAnchor="end"
                        height={100}
                      />
                      <YAxis stroke="#e2e8f0" />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: 'rgba(30, 41, 59, 0.95)',
                          border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '12px',
                          color: 'white'
                        }}
                        formatter={(value) => [formatNumber(value), 'Population']}
                      />
                      <Bar 
                        dataKey="population" 
                        fill="url(#gradient)"
                        radius={[4, 4, 0, 0]}
                      />
                      <defs>
                        <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#8B5CF6" />
                          <stop offset="100%" stopColor="#3B82F6" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </>
              )}

              {selectedView === 'income' && (
                <>
                  <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                    <DollarSign className="w-6 h-6 text-green-400" />
                    Median Income by Area
                  </h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={demographicData} margin={{ top: 20, right: 30, left: 20, bottom: 100 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis 
                        dataKey="metro" 
                        stroke="#e2e8f0"
                        fontSize={10}
                        angle={-45}
                        textAnchor="end"
                        height={100}
                      />
                      <YAxis stroke="#e2e8f0" />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: 'rgba(30, 41, 59, 0.95)',
                          border: '1px solid rgba(255,255,255,0.2)',
                          borderRadius: '12px',
                          color: 'white'
                        }}
                        formatter={(value) => [formatCurrency(value), 'Median Income']}
                      />
                      <Bar 
                        dataKey="medianIncome" 
                        fill="url(#incomeGradient)"
                        radius={[4, 4, 0, 0]}
                      />
                      <defs>
                        <linearGradient id="incomeGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#10B981" />
                          <stop offset="100%" stopColor="#059669" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </>
              )}

              {selectedView === 'regions' && (
                <>
                  <h3 className="text-2xl font-bold text-white mb-6">Regional Distribution</h3>
                  <div className="flex justify-center">
                    <ResponsiveContainer width={400} height={400}>
                      <PieChart>
                        <Pie
                          data={regionData}
                          cx="50%"
                          cy="50%"
                          outerRadius={120}
                          fill="#8884d8"
                          dataKey="value"
                          label={({ name, value }) => `${name} (${value})`}
                        >
                          {regionData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: 'rgba(30, 41, 59, 0.95)',
                            border: '1px solid rgba(255,255,255,0.2)',
                            borderRadius: '12px',
                            color: 'white'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="mt-6 text-center text-purple-200">
                    <p>The South dominates with 7 out of 10 top metropolitan areas</p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Rankings List */}
          <div className="lg:col-span-1">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
              <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <MapPin className="w-6 h-6 text-red-400" />
                Top 10 Rankings
              </h3>
              <div className="space-y-4">
                {demographicData.map((area, index) => (
                  <div
                    key={area.rank}
                    className={`p-4 rounded-xl border transition-all cursor-pointer transform hover:scale-105 ${
                      hoveredArea === area.rank
                        ? 'bg-purple-600/30 border-purple-400'
                        : 'bg-white/5 border-white/10 hover:bg-white/10'
                    }`}
                    onMouseEnter={() => setHoveredArea(area.rank)}
                    onMouseLeave={() => setHoveredArea(null)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="bg-purple-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm">
                          {area.rank}
                        </div>
                        <div>
                          <h4 className="text-white font-semibold text-sm leading-tight">
                            {area.metro.split(',')[0]}
                          </h4>
                          <p className="text-purple-200 text-xs">{area.state}</p>
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-purple-300">MSA Pop:</span>
                        <p className="text-white font-semibold">{formatNumber(area.population)}</p>
                      </div>
                      <div>
                        <span className="text-purple-300">+30mi:</span>
                        <p className="text-orange-300 font-semibold">+{formatNumber(area.extended30Mile)}</p>
                      </div>
                      <div>
                        <span className="text-purple-300">Total:</span>
                        <p className="text-green-300 font-semibold">{formatNumber(area.population + area.extended30Mile)}</p>
                      </div>
                      <div>
                        <span className="text-purple-300">Income:</span>
                        <p className="text-white font-semibold">{formatCurrency(area.medianIncome)}</p>
                      </div>
                    </div>
                    {area.extendedAreas && (
                      <div className="mt-2 pt-2 border-t border-white/10">
                        <span className="text-purple-300 text-xs">Extended areas:</span>
                        <p className="text-white text-xs">{area.extendedAreas}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Key Insights */}
        <div className="mt-8 bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
          <h3 className="text-2xl font-bold text-white mb-4">Population Summary & Extended Area Analysis</h3>
          
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-purple-600/20 rounded-xl p-4 text-center">
              <h4 className="text-purple-300 text-sm">MSA Total</h4>
              <p className="text-2xl font-bold text-white">{formatNumber(demographicData.reduce((sum, area) => sum + area.population, 0))}</p>
            </div>
            <div className="bg-orange-600/20 rounded-xl p-4 text-center">
              <h4 className="text-orange-300 text-sm">30-Mile Extended</h4>
              <p className="text-2xl font-bold text-white">{formatNumber(demographicData.reduce((sum, area) => sum + area.extended30Mile, 0))}</p>
            </div>
            <div className="bg-green-600/20 rounded-xl p-4 text-center">
              <h4 className="text-green-300 text-sm">Combined Total</h4>
              <p className="text-2xl font-bold text-white">{formatNumber(demographicData.reduce((sum, area) => sum + area.population + area.extended30Mile, 0))}</p>
            </div>
            <div className="bg-blue-600/20 rounded-xl p-4 text-center">
              <h4 className="text-blue-300 text-sm">Extended % Increase</h4>
              <p className="text-2xl font-bold text-white">
                {Math.round((demographicData.reduce((sum, area) => sum + area.extended30Mile, 0) / demographicData.reduce((sum, area) => sum + area.population, 0)) * 100)}%
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-purple-200">
            <div className="bg-white/5 rounded-xl p-4">
              <h4 className="text-white font-semibold mb-2">Extended Area Impact</h4>
              <p className="text-sm">
                The 30-mile extended areas add 630,000 additional individuals, representing a 34% increase over MSA-only populations.
              </p>
            </div>
            <div className="bg-white/5 rounded-xl p-4">
              <h4 className="text-white font-semibold mb-2">Largest Extensions</h4>
              <p className="text-sm">
                Atlanta (+95K), Houston (+88K), and DC (+75K) show the highest extended populations due to suburban sprawl patterns.
              </p>
            </div>
            <div className="bg-white/5 rounded-xl p-4">
              <h4 className="text-white font-semibold mb-2">Market Implications</h4>
              <p className="text-sm">
                Including extended areas brings the total addressable population to 2.48 million across these 10 regions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AfricanAmericanDemographics;