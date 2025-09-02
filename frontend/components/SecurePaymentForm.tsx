import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { toast } from 'react-hot-toast';

// Load Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

interface PaymentFormProps {
  amount: number;
  currency?: string;
  description?: string;
  onSuccess: (paymentIntent: any) => void;
  onError: (error: string) => void;
  disabled?: boolean;
  className?: string;
}

interface PaymentFormData {
  amount: number;
  currency: string;
  description: string;
  billing_details: {
    name: string;
    email: string;
    address: {
      line1: string;
      line2?: string;
      city: string;
      state: string;
      postal_code: string;
      country: string;
    };
  };
}

const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '16px',
      color: '#424770',
      '::placeholder': {
        color: '#aab7c4',
      },
      backgroundColor: 'transparent',
    },
    invalid: {
      color: '#9e2146',
    },
  },
};

const PaymentFormContent: React.FC<PaymentFormProps> = ({
  amount,
  currency = 'usd',
  description = 'Payment',
  onSuccess,
  onError,
  disabled = false,
  className = '',
}) => {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [formData, setFormData] = useState<PaymentFormData>({
    amount,
    currency,
    description,
    billing_details: {
      name: '',
      email: '',
      address: {
        line1: '',
        line2: '',
        city: '',
        state: '',
        postal_code: '',
        country: 'US',
      },
    },
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      billing_details: {
        ...prev.billing_details,
        [field]: value,
      },
    }));
  };

  const handleAddressChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      billing_details: {
        ...prev.billing_details,
        address: {
          ...prev.billing_details.address,
          [field]: value,
        },
      },
    }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements) {
      onError('Stripe has not loaded yet. Please try again.');
      return;
    }

    setIsProcessing(true);

    try {
      // Create payment intent
      const response = await fetch('/api/payment/payment-intents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: Math.round(formData.amount * 100), // Convert to cents
          currency: formData.currency,
          description: formData.description,
          metadata: {
            billing_name: formData.billing_details.name,
            billing_email: formData.billing_details.email,
          },
        }),
      });

      const { payment_intent, error } = await response.json();

      if (error) {
        throw new Error(error);
      }

      // Confirm payment
      const { error: confirmError, paymentIntent } = await stripe.confirmCardPayment(
        payment_intent.client_secret,
        {
          payment_method: {
            card: elements.getElement(CardElement)!,
            billing_details: formData.billing_details,
          },
        }
      );

      if (confirmError) {
        throw new Error(confirmError.message);
      }

      if (paymentIntent.status === 'succeeded') {
        toast.success('Payment successful!');
        onSuccess(paymentIntent);
      } else {
        throw new Error('Payment failed. Please try again.');
      }
    } catch (error: any) {
      console.error('Payment error:', error);
      toast.error(error.message || 'Payment failed. Please try again.');
      onError(error.message || 'Payment failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const isFormValid = () => {
    return (
      formData.billing_details.name.trim() !== '' &&
      formData.billing_details.email.trim() !== '' &&
      formData.billing_details.address.line1.trim() !== '' &&
      formData.billing_details.address.city.trim() !== '' &&
      formData.billing_details.address.state.trim() !== '' &&
      formData.billing_details.address.postal_code.trim() !== ''
    );
  };

  return (
    <form onSubmit={handleSubmit} className={`space-y-6 ${className}`}>
      {/* Payment Amount Display */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex justify-between items-center">
          <span className="text-lg font-medium text-gray-900">Total Amount:</span>
          <span className="text-2xl font-bold text-green-600">
            ${formData.amount.toFixed(2)} {formData.currency.toUpperCase()}
          </span>
        </div>
        {description && (
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        )}
      </div>

      {/* Card Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Card Information</h3>
        <div className="border border-gray-300 rounded-md p-4 bg-white">
          <CardElement options={CARD_ELEMENT_OPTIONS} />
        </div>
      </div>

      {/* Billing Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Billing Information</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Full Name *
            </label>
            <input
              type="text"
              id="name"
              value={formData.billing_details.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="John Doe"
              required
              disabled={disabled || isProcessing}
              aria-label="Full name"
              aria-describedby="name-help"
              aria-required="true"
              aria-invalid={formData.billing_details.name.trim() === '' ? 'true' : 'false'}
            />
            <div id="name-help" className="sr-only">Enter your full legal name as it appears on your identification</div>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address *
            </label>
            <input
              type="email"
              id="email"
              value={formData.billing_details.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="john@example.com"
              required
              disabled={disabled || isProcessing}
              aria-label="Email address"
              aria-describedby="email-help"
              aria-required="true"
              aria-invalid={formData.billing_details.email.trim() === '' ? 'true' : 'false'}
            />
            <div id="email-help" className="sr-only">Enter your email address for payment confirmation</div>
          </div>
        </div>

        <div>
          <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
            Address Line 1 *
          </label>
          <input
            type="text"
            id="address"
            value={formData.billing_details.address.line1}
            onChange={(e) => handleAddressChange('line1', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="123 Main Street"
            required
            disabled={disabled || isProcessing}
            aria-label="Address line 1"
            aria-describedby="address-help"
            aria-required="true"
            aria-invalid={formData.billing_details.address.line1.trim() === '' ? 'true' : 'false'}
          />
          <div id="address-help" className="sr-only">Enter your street address</div>
        </div>

        <div>
          <label htmlFor="address2" className="block text-sm font-medium text-gray-700 mb-1">
            Address Line 2 (Optional)
          </label>
          <input
            type="text"
            id="address2"
            value={formData.billing_details.address.line2}
            onChange={(e) => handleAddressChange('line2', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Apt 4B"
            disabled={disabled || isProcessing}
            aria-label="Address line 2 (optional)"
            aria-describedby="address2-help"
            aria-required="false"
          />
          <div id="address2-help" className="sr-only">Enter apartment number or suite if applicable</div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
              City *
            </label>
            <input
              type="text"
              id="city"
              value={formData.billing_details.address.city}
              onChange={(e) => handleAddressChange('city', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="New York"
              required
              disabled={disabled || isProcessing}
              aria-label="City"
              aria-describedby="city-help"
              aria-required="true"
              aria-invalid={formData.billing_details.address.city.trim() === '' ? 'true' : 'false'}
            />
            <div id="city-help" className="sr-only">Enter your city</div>
          </div>

          <div>
            <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
              State *
            </label>
            <input
              type="text"
              id="state"
              value={formData.billing_details.address.state}
              onChange={(e) => handleAddressChange('state', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="NY"
              required
              disabled={disabled || isProcessing}
              aria-label="State or province"
              aria-describedby="state-help"
              aria-required="true"
              aria-invalid={formData.billing_details.address.state.trim() === '' ? 'true' : 'false'}
            />
            <div id="state-help" className="sr-only">Enter your state or province</div>
          </div>

          <div>
            <label htmlFor="postal_code" className="block text-sm font-medium text-gray-700 mb-1">
              Postal Code *
            </label>
            <input
              type="text"
              id="postal_code"
              value={formData.billing_details.address.postal_code}
              onChange={(e) => handleAddressChange('postal_code', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="10001"
              required
              disabled={disabled || isProcessing}
              aria-label="Postal code"
              aria-describedby="postal-help"
              aria-required="true"
              aria-invalid={formData.billing_details.address.postal_code.trim() === '' ? 'true' : 'false'}
            />
            <div id="postal-help" className="sr-only">Enter your postal or zip code</div>
          </div>
        </div>

        <div>
          <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-1">
            Country *
          </label>
          <select
            id="country"
            value={formData.billing_details.address.country}
            onChange={(e) => handleAddressChange('country', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
            disabled={disabled || isProcessing}
            aria-label="Country"
            aria-describedby="country-help"
            aria-required="true"
          >
            <option value="US">United States</option>
            <option value="CA">Canada</option>
            <option value="GB">United Kingdom</option>
            <option value="AU">Australia</option>
            <option value="DE">Germany</option>
            <option value="FR">France</option>
            <option value="JP">Japan</option>
            <option value="IN">India</option>
            <option value="BR">Brazil</option>
            <option value="MX">Mexico</option>
          </select>
        </div>
      </div>

      {/* Security Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Secure Payment</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                Your payment information is encrypted and secure. We use Stripe for payment processing 
                and never store your credit card details on our servers.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={disabled || isProcessing || !isFormValid()}
        className={`w-full py-3 px-4 rounded-md font-medium text-white transition-colors ${
          disabled || isProcessing || !isFormValid()
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
        }`}
      >
        {isProcessing ? (
          <div className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing Payment...
          </div>
        ) : (
          `Pay $${formData.amount.toFixed(2)} ${formData.currency.toUpperCase()}`
        )}
      </button>

      {/* PCI DSS Compliance Notice */}
      <div className="text-xs text-gray-500 text-center">
        <p>
          🔒 PCI DSS Compliant • SSL Encrypted • Secure Payment Processing
        </p>
        <p className="mt-1">
          Powered by Stripe • Your card details are never stored on our servers
        </p>
      </div>
    </form>
  );
};

const SecurePaymentForm: React.FC<PaymentFormProps> = (props) => {
  return (
    <Elements stripe={stripePromise}>
      <PaymentFormContent {...props} />
    </Elements>
  );
};

export default SecurePaymentForm;
