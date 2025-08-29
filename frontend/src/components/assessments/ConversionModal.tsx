import React, { useState, useEffect, useRef, useCallback } from 'react';
import LoadingSpinner from '../shared/LoadingSpinner';

// Types
interface AssessmentResult {
  id: string;
  assessment_type: string;
  score: number;
  risk_level: string;
  conversion_offer: {
    lead_id: string;
    lead_score: number;
    offer_type: string;
    discount_percentage: number;
    trial_days: number;
    message: string;
  };
}

interface SubscriptionTier {
  id: string;
  name: string;
  price: number;
  original_price: number;
  features: string[];
  popular?: boolean;
  discount_percentage?: number;
}

interface UserTestimonial {
  id: string;
  name: string;
  role: string;
  company: string;
  content: string;
  rating: number;
  assessment_type: string;
  avatar_url?: string;
}

interface ConversionModalProps {
  assessmentResult: AssessmentResult;
  onClose: () => void;
}

const ConversionModal: React.FC<ConversionModalProps> = ({
  assessmentResult,
  onClose,
}) => {
  const [selectedTier, setSelectedTier] = useState<string>('');
  const [timeRemaining, setTimeRemaining] = useState(3600); // 60 minutes in seconds
  const [showEmergencyOffer, setShowEmergencyOffer] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [testimonials, setTestimonials] = useState<UserTestimonial[]>([]);
  const [loadingTestimonials, setLoadingTestimonials] = useState(true);
  const modalRef = useRef<HTMLDivElement>(null);

  // Subscription tiers
  const subscriptionTiers: SubscriptionTier[] = [
    {
      id: 'basic',
      name: 'Basic Plan',
      price: 10,
      original_price: 15,
      features: [
        'Full assessment results',
        'Personalized recommendations',
        'Email support',
        'Monthly check-ins',
      ],
      discount_percentage: 33,
    },
    {
      id: 'premium',
      name: 'Premium Plan',
      price: 20,
      original_price: 30,
      features: [
        'Everything in Basic',
        'Priority support',
        'Weekly check-ins',
        'Advanced analytics',
        'Custom action plans',
      ],
      popular: true,
      discount_percentage: 33,
    },
    {
      id: 'enterprise',
      name: 'Enterprise Plan',
      price: 50,
      original_price: 75,
      features: [
        'Everything in Premium',
        '1-on-1 coaching sessions',
        'Custom integrations',
        'Dedicated account manager',
        'Advanced reporting',
      ],
      discount_percentage: 33,
    },
  ];

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          setShowEmergencyOffer(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Exit intent detection
  useEffect(() => {
    const handleMouseLeave = (e: MouseEvent) => {
      if (e.clientY <= 0 && !showEmergencyOffer) {
        setShowEmergencyOffer(true);
      }
    };

    document.addEventListener('mouseleave', handleMouseLeave);
    return () => document.removeEventListener('mouseleave', handleMouseLeave);
  }, [showEmergencyOffer]);

  // Load testimonials
  const loadTestimonials = useCallback(async () => {
    try {
      setLoadingTestimonials(true);
      const response = await fetch('/api/testimonials/assessment', {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setTestimonials(data.testimonials || []);
      }
    } catch (err) {
      console.error('Failed to load testimonials:', err);
    } finally {
      setLoadingTestimonials(false);
    }
  }, []);

  useEffect(() => {
    loadTestimonials();
  }, [loadTestimonials]);

  // Format time remaining
  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle payment
  const handlePayment = async (tierId: string) => {
    if (!selectedTier) {
      setSelectedTier(tierId);
      return;
    }

    try {
      setProcessing(true);
      
      const response = await fetch('/api/assessments/convert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          assessment_id: assessmentResult.id,
          subscription_tier: tierId,
          lead_id: assessmentResult.conversion_offer.lead_id,
        }),
      });

      if (!response.ok) {
        throw new Error('Payment failed');
      }

      const data = await response.json();
      
      // Redirect to Stripe checkout
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        // Handle success
        onClose();
        window.location.href = '/dashboard';
      }
    } catch (err) {
      console.error('Payment error:', err);
      alert('Payment failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  // Handle emergency offer
  const handleEmergencyOffer = () => {
    setShowEmergencyOffer(false);
    setSelectedTier('basic');
    // Auto-select emergency offer
    handlePayment('basic');
  };

  // Close modal on backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const selectedTierData = subscriptionTiers.find(tier => tier.id === selectedTier);

  return (
    <>
      {/* Main Modal */}
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div
          ref={modalRef}
          className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
          onClick={handleBackdropClick}
        >
          <div className="p-8">
            {/* Header */}
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Unlock Your Full Potential
              </h2>
              <p className="text-xl text-gray-600 mb-6">
                {assessmentResult.conversion_offer.message}
              </p>
              
              {/* Countdown Timer */}
              <div className="bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg p-4 mb-6">
                <div className="text-sm font-medium mb-2">Limited Time Offer</div>
                <div className="text-2xl font-bold font-mono">
                  {formatTime(timeRemaining)}
                </div>
                <div className="text-sm opacity-90">remaining to claim your discount</div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Subscription Tiers */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-6">Choose Your Plan</h3>
                <div className="space-y-4">
                  {subscriptionTiers.map((tier) => (
                    <div
                      key={tier.id}
                      className={`border-2 rounded-lg p-6 cursor-pointer transition-all duration-200 ${
                        selectedTier === tier.id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-purple-300'
                      } ${tier.popular ? 'ring-2 ring-purple-200' : ''}`}
                      onClick={() => setSelectedTier(tier.id)}
                    >
                      {tier.popular && (
                        <div className="bg-purple-500 text-white text-xs font-semibold px-2 py-1 rounded-full inline-block mb-2">
                          MOST POPULAR
                        </div>
                      )}
                      
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-lg font-semibold text-gray-900">{tier.name}</h4>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-purple-600">
                            ${tier.price}
                          </div>
                          <div className="text-sm text-gray-500 line-through">
                            ${tier.original_price}
                          </div>
                        </div>
                      </div>

                      <ul className="space-y-2 mb-4">
                        {tier.features.map((feature, index) => (
                          <li key={index} className="flex items-center text-sm text-gray-700">
                            <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            {feature}
                          </li>
                        ))}
                      </ul>

                      <button
                        onClick={() => handlePayment(tier.id)}
                        disabled={processing}
                        className={`w-full py-3 px-4 rounded-lg font-semibold transition-colors ${
                          selectedTier === tier.id
                            ? 'bg-purple-600 text-white hover:bg-purple-700'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        } disabled:opacity-50`}
                      >
                        {processing ? (
                          <div className="flex items-center justify-center">
                            <LoadingSpinner size="sm" className="mr-2" />
                            Processing...
                          </div>
                        ) : (
                          `Get ${tier.name} - ${tier.discount_percentage}% OFF`
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Testimonials */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-6">What Our Users Say</h3>
                
                {loadingTestimonials ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <div className="space-y-4">
                    {testimonials.slice(0, 3).map((testimonial) => (
                      <div key={testimonial.id} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center mb-3">
                          {testimonial.avatar_url ? (
                            <img
                              src={testimonial.avatar_url}
                              alt={testimonial.name}
                              className="w-10 h-10 rounded-full mr-3"
                            />
                          ) : (
                            <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center text-white font-semibold mr-3">
                              {testimonial.name.charAt(0)}
                            </div>
                          )}
                          <div>
                            <div className="font-semibold text-gray-900">{testimonial.name}</div>
                            <div className="text-sm text-gray-600">{testimonial.role} at {testimonial.company}</div>
                          </div>
                        </div>
                        <p className="text-gray-700 text-sm mb-2">"{testimonial.content}"</p>
                        <div className="flex items-center">
                          {[...Array(5)].map((_, i) => (
                            <svg
                              key={i}
                              className={`w-4 h-4 ${i < testimonial.rating ? 'text-yellow-400' : 'text-gray-300'}`}
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Money-back guarantee */}
                <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <svg className="w-6 h-6 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <div className="font-semibold text-green-800">30-Day Money-Back Guarantee</div>
                      <div className="text-sm text-green-700">Not satisfied? Get a full refund, no questions asked.</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Close button */}
            <div className="text-center mt-8">
              <button
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                Maybe later
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Emergency Offer Modal */}
      {showEmergencyOffer && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-60 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-8 text-center">
            <div className="text-6xl mb-4">🚨</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Wait! Special Emergency Offer
            </h3>
            <p className="text-gray-600 mb-6">
              We don't want you to miss out! Get our Basic Plan for just $19 instead of $30.
            </p>
            <div className="space-y-4">
              <button
                onClick={handleEmergencyOffer}
                disabled={processing}
                className="w-full bg-red-500 text-white py-3 px-4 rounded-lg font-semibold hover:bg-red-600 transition-colors disabled:opacity-50"
              >
                {processing ? 'Processing...' : 'Get Emergency Offer - $19'}
              </button>
              <button
                onClick={() => setShowEmergencyOffer(false)}
                className="w-full text-gray-500 hover:text-gray-700 transition-colors"
              >
                No thanks, I'll pass
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ConversionModal;
