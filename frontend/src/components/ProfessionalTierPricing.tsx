import React, { useState, useEffect } from 'react';
import { 
  Check, 
  X, 
  Star, 
  Building2, 
  Car, 
  Calculator, 
  BarChart3, 
  FileText, 
  CreditCard, 
  Users, 
  Shield,
  TrendingUp,
  DollarSign,
  MapPin,
  Calendar,
  Settings,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap,
  Crown,
  Award
} from 'lucide-react';

interface SubscriptionPlan {
  name: string;
  price: number;
  currency: string;
  interval: string;
  features: {
    [key: string]: boolean | number;
  };
}

interface Feature {
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  category: 'fleet' | 'tax' | 'analytics' | 'integrations' | 'support';
}

const ProfessionalTierPricing: React.FC = () => {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<string>('professional');
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  const features: Feature[] = [
    // Fleet Management Features
    {
      name: 'Unlimited Vehicles',
      description: 'Add unlimited business and personal vehicles to your fleet',
      icon: Car,
      category: 'fleet'
    },
    {
      name: 'Business/Personal Designation',
      description: 'Categorize vehicles by business use with percentage tracking',
      icon: Building2,
      category: 'fleet'
    },
    {
      name: 'Department Assignment',
      description: 'Assign vehicles to departments and employees for cost allocation',
      icon: Users,
      category: 'fleet'
    },
    {
      name: 'GPS Mileage Tracking',
      description: 'Automatic mileage logging with GPS verification for IRS compliance',
      icon: MapPin,
      category: 'fleet'
    },
    {
      name: 'Multi-Vehicle Maintenance Scheduling',
      description: 'Optimize maintenance schedules across your entire fleet',
      icon: Calendar,
      category: 'fleet'
    },

    // Tax-Adjacent Features
    {
      name: 'Business vs Personal Mileage Logging',
      description: 'Track business and personal miles with IRS-compliant documentation',
      icon: MapPin,
      category: 'tax'
    },
    {
      name: 'Receipt Storage & Categorization',
      description: 'Store and categorize receipts with automatic business expense classification',
      icon: Upload,
      category: 'tax'
    },
    {
      name: 'Expense Report Generation',
      description: 'Generate detailed expense reports for tax preparation and business use',
      icon: FileText,
      category: 'tax'
    },
    {
      name: 'Annual Expense Summaries',
      description: 'Comprehensive annual summaries of all vehicle-related expenses',
      icon: BarChart3,
      category: 'tax'
    },
    {
      name: 'IRS-Compliant Mileage Logs',
      description: 'Maintain IRS-compliant mileage logs with proper documentation',
      icon: Calendar,
      category: 'tax'
    },
    {
      name: 'Maintenance Record Keeping',
      description: 'Track and document all vehicle maintenance with business use allocation',
      icon: Car,
      category: 'tax'
    },
    {
      name: 'Business Trip Documentation',
      description: 'Document business trips with purpose, destination, and mileage tracking',
      icon: Building2,
      category: 'tax'
    },
    {
      name: 'Vehicle Use Percentage Tracking',
      description: 'Calculate and track business vs personal use percentage for tax purposes',
      icon: TrendingUp,
      category: 'tax'
    },
    {
      name: 'Tax Deduction Education Library',
      description: 'Comprehensive library of tax deduction guides and educational content',
      icon: BookOpen,
      category: 'tax'
    },
    {
      name: 'IRS Publication Summaries',
      description: 'Clear summaries of relevant IRS publications (marked as educational)',
      icon: FileText,
      category: 'tax'
    },
    {
      name: 'Common Deduction Checklists',
      description: 'Step-by-step checklists to ensure proper documentation and compliance',
      icon: CheckCircle,
      category: 'tax'
    },
    {
      name: 'Tax Season Preparation Guides',
      description: 'Comprehensive guides to prepare your vehicle deductions for tax season',
      icon: Calendar,
      category: 'tax'
    },

    // Executive Decision Support
    {
      name: 'Vehicle Replacement ROI Analysis',
      description: 'Calculate ROI for replacing vehicles with detailed cost analysis',
      icon: BarChart3,
      category: 'analytics'
    },
    {
      name: 'Lease vs Buy Optimization',
      description: 'Compare leasing vs buying options for business vehicles',
      icon: TrendingUp,
      category: 'analytics'
    },
    {
      name: 'Insurance Optimization',
      description: 'Analyze and optimize insurance coverage across your fleet',
      icon: Shield,
      category: 'analytics'
    },
    {
      name: 'Corporate Policy Compliance',
      description: 'Track compliance with corporate vehicle policies',
      icon: CheckCircle,
      category: 'analytics'
    },

    // Advanced Analytics
    {
      name: 'Cost Per Mile Analysis',
      description: 'Detailed cost analysis per mile across your entire fleet',
      icon: DollarSign,
      category: 'analytics'
    },
    {
      name: 'Department Cost Allocation',
      description: 'Allocate vehicle costs to specific departments or employees',
      icon: Users,
      category: 'analytics'
    },
    {
      name: 'Predictive Maintenance',
      description: 'AI-powered maintenance predictions to reduce downtime',
      icon: Clock,
      category: 'analytics'
    },
    {
      name: 'Custom Executive Reports',
      description: 'Customizable reports for executive decision-making',
      icon: BarChart3,
      category: 'analytics'
    },

    // Business Integrations
    {
      name: 'QuickBooks Integration',
      description: 'Sync expenses and mileage with QuickBooks automatically',
      icon: FileText,
      category: 'integrations'
    },
    {
      name: 'Corporate Credit Card Integration',
      description: 'Automatically categorize credit card transactions',
      icon: CreditCard,
      category: 'integrations'
    },
    {
      name: 'HR System Integration',
      description: 'Connect with HR systems for employee vehicle benefits',
      icon: Users,
      category: 'integrations'
    },
    {
      name: 'Insurance Policy Management',
      description: 'Manage insurance policies across your fleet',
      icon: Shield,
      category: 'integrations'
    },

    // Concierge Services
    {
      name: 'Priority Support',
      description: 'Dedicated success manager with priority support',
      icon: Award,
      category: 'support'
    },
    {
      name: 'Custom Integrations',
      description: 'Custom integrations with your existing business systems',
      icon: Settings,
      category: 'support'
    },
    {
      name: 'White-Label Reporting',
      description: 'Custom branded reports for internal use',
      icon: FileText,
      category: 'support'
    },
    {
      name: 'Quarterly Business Reviews',
      description: 'Quarterly reviews with optimization recommendations',
      icon: Calendar,
      category: 'support'
    }
  ];

  useEffect(() => {
    fetchSubscriptionPlans();
  }, []);

  const fetchSubscriptionPlans = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/subscription/plans');
      const data = await response.json();
      setPlans(Object.values(data.plans));
    } catch (error) {
      console.error('Error fetching subscription plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getFeatureIcon = (category: string) => {
    switch (category) {
      case 'fleet': return <Car className="w-4 h-4" />;
      case 'tax': return <Calculator className="w-4 h-4" />;
      case 'analytics': return <BarChart3 className="w-4 h-4" />;
      case 'integrations': return <Settings className="w-4 h-4" />;
      case 'support': return <Award className="w-4 h-4" />;
      default: return <Check className="w-4 h-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'fleet': return 'text-blue-600 bg-blue-100';
      case 'tax': return 'text-green-600 bg-green-100';
      case 'analytics': return 'text-purple-600 bg-purple-100';
      case 'integrations': return 'text-orange-600 bg-orange-100';
      case 'support': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const handleUpgrade = async (planName: string) => {
    try {
      const response = await fetch('/api/subscription/upgrade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tier: planName.toLowerCase()
        })
      });
      
      const data = await response.json();
      if (data.success) {
        // Handle successful upgrade
        console.log('Upgrade successful:', data);
      }
    } catch (error) {
      console.error('Error upgrading subscription:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading pricing plans...</p>
        </div>
      </div>
    );
  }

  const freePlan = plans.find(p => p.name.toLowerCase() === 'free');
  const professionalPlan = plans.find(p => p.name.toLowerCase() === 'professional');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-12">
            <div className="text-center mx-auto">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                Professional Tier Pricing
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                Executive-level features for business vehicle management
              </p>
              
              {/* Billing Toggle */}
              <div className="flex items-center justify-center space-x-4 mb-8">
                <span className={`text-sm font-medium ${billingCycle === 'monthly' ? 'text-gray-900' : 'text-gray-500'}`}>
                  Monthly
                </span>
                <button
                  onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
                  className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      billingCycle === 'yearly' ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className={`text-sm font-medium ${billingCycle === 'yearly' ? 'text-gray-900' : 'text-gray-500'}`}>
                  Yearly
                  <span className="ml-1 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                    Save 20%
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Free Plan */}
          {freePlan && (
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{freePlan.name}</h3>
                <div className="text-4xl font-bold text-gray-900 mb-2">
                  {formatCurrency(freePlan.price)}
                  <span className="text-lg font-normal text-gray-500">/{freePlan.interval}</span>
                </div>
                <p className="text-gray-600">Perfect for personal use</p>
              </div>

              <div className="space-y-4 mb-8">
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">Up to {freePlan.features.max_vehicles} vehicles</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">Basic maintenance tracking</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">Commute cost calculator</span>
                </div>
                <div className="flex items-center">
                  <X className="w-5 h-5 text-gray-400 mr-3" />
                  <span className="text-gray-500">Fleet management</span>
                </div>
                <div className="flex items-center">
                  <X className="w-5 h-5 text-gray-400 mr-3" />
                  <span className="text-gray-500">Tax optimization</span>
                </div>
                <div className="flex items-center">
                  <X className="w-5 h-5 text-gray-400 mr-3" />
                  <span className="text-gray-500">Business integrations</span>
                </div>
              </div>

              <button className="w-full bg-gray-600 text-white py-3 px-6 rounded-lg hover:bg-gray-700 transition-colors">
                Current Plan
              </button>
            </div>
          )}

          {/* Professional Plan */}
          {professionalPlan && (
            <div className="bg-white rounded-2xl shadow-xl border-2 border-blue-500 p-8 relative">
              {/* Popular Badge */}
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <div className="bg-blue-600 text-white px-4 py-2 rounded-full text-sm font-medium flex items-center">
                  <Crown className="w-4 h-4 mr-1" />
                  Most Popular
                </div>
              </div>

              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{professionalPlan.name}</h3>
                <div className="text-4xl font-bold text-gray-900 mb-2">
                  {formatCurrency(professionalPlan.price)}
                  <span className="text-lg font-normal text-gray-500">/{professionalPlan.interval}</span>
                </div>
                <p className="text-gray-600">For business owners and executives</p>
              </div>

              <div className="space-y-4 mb-8">
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">Unlimited vehicles</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">Fleet management dashboard</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">Tax optimization suite</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">IRS-compliant reporting</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">GPS mileage tracking</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">Business integrations</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  <span className="text-gray-700">Concierge support</span>
                </div>
              </div>

              <button
                onClick={() => handleUpgrade('professional')}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Upgrade to Professional
              </button>
            </div>
          )}
        </div>

        {/* Feature Comparison */}
        <div className="mt-16">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Professional Tier Features
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div key={index} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-start space-x-3">
                  <div className={`p-2 rounded-lg ${getCategoryColor(feature.category)}`}>
                    {getFeatureIcon(feature.category)}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {feature.name}
                    </h3>
                    <p className="text-gray-600 text-sm">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Value Proposition */}
        <div className="mt-16 bg-blue-50 rounded-2xl p-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose Professional Tier?
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Designed for business owners, executives, and high-net-worth individuals
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <DollarSign className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Maximize Tax Savings</h3>
                <p className="text-gray-600">
                  Optimize your business vehicle tax deductions with IRS-compliant reporting
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <TrendingUp className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Executive Decision Support</h3>
                <p className="text-gray-600">
                  Make informed decisions with ROI analysis and cost optimization tools
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <Settings className="w-8 h-8 text-purple-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Seamless Integrations</h3>
                <p className="text-gray-600">
                  Connect with your existing business systems for streamlined operations
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfessionalTierPricing;
