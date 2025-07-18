import React, { Suspense, lazy, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'
import { useAnalytics } from '../hooks/useAnalytics'

// Lazy load components for code splitting
const AssessmentForm = lazy(() => import('./AssessmentForm').then(module => ({ default: module.AssessmentForm })))
const AssessmentResults = lazy(() => import('./AssessmentResults').then(module => ({ default: module.AssessmentResults })))
const SimpleAssessment = lazy(() => import('./SimpleAssessment').then(module => ({ default: module.SimpleAssessment })))

// Optimized image component with lazy loading
const OptimizedImage: React.FC<{
  src: string
  alt: string
  className?: string
  width?: number
  height?: number
  priority?: boolean
}> = ({ src, alt, className = '', width, height, priority = false }) => {
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [error, setError] = React.useState(false)

  useEffect(() => {
    if (priority) {
      setIsLoaded(true)
    }
  }, [priority])

  return (
    <div className={`image-container ${className}`}>
      {!isLoaded && !error && (
        <div className="image-skeleton animate-pulse bg-gray-300 rounded-lg" style={{ width, height }} />
      )}
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        loading={priority ? 'eager' : 'lazy'}
        onLoad={() => setIsLoaded(true)}
        onError={() => setError(true)}
        className={`transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        } ${error ? 'hidden' : ''}`}
        style={{ width, height }}
      />
      {error && (
        <div className="image-error bg-gray-200 rounded-lg flex items-center justify-center" style={{ width, height }}>
          <span className="text-gray-500 text-sm">Image unavailable</span>
        </div>
      )}
    </div>
  )
}

// SEO optimized hero section
const HeroSection: React.FC = () => {
  const { trackLandingPageView } = useAnalytics()

  useEffect(() => {
    trackLandingPageView()
  }, [trackLandingPageView])

  return (
    <section className="hero-section relative min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 overflow-hidden">
      {/* Background pattern for visual interest */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.1%22%3E%3Ccircle%20cx%3D%2230%22%20cy%3D%2230%22%20r%3D%222%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')]"></div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight">
            Transform Your
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              Financial Future
            </span>
          </h1>
          
          <p className="text-xl sm:text-2xl text-gray-300 mb-8 leading-relaxed max-w-3xl mx-auto">
            Discover your unique money personality and get personalized strategies to build wealth, 
            reduce stress, and achieve financial freedom in just 2 minutes.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <button 
              className="cta-button-primary w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-lg font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-blue-500 focus:ring-opacity-50"
              onClick={() => {
                document.getElementById('questionnaire-section')?.scrollIntoView({ 
                  behavior: 'smooth' 
                })
              }}
            >
              Start Your Free Assessment
            </button>
            
            <button 
              className="cta-button-secondary w-full sm:w-auto px-8 py-4 bg-transparent border-2 border-white text-white text-lg font-semibold rounded-lg hover:bg-white hover:text-gray-900 transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-white focus:ring-opacity-50"
              onClick={() => {
                document.getElementById('how-it-works')?.scrollIntoView({ 
                  behavior: 'smooth' 
                })
              }}
            >
              Learn How It Works
            </button>
          </div>

          {/* Social proof */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 text-gray-400">
            <div className="flex items-center gap-2">
              <div className="flex -space-x-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full border-2 border-gray-900"></div>
                ))}
              </div>
              <span className="text-sm">10,000+ people assessed</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex text-yellow-400">
                {[1, 2, 3, 4, 5].map((i) => (
                  <svg key={i} className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
              <span className="text-sm">4.9/5 rating</span>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>
  )
}

// How it works section
const HowItWorksSection: React.FC = () => {
  const steps = [
    {
      icon: '📝',
      title: 'Take the Assessment',
      description: 'Answer 10 simple questions about your money habits and goals'
    },
    {
      icon: '🧠',
      title: 'Get Your Profile',
      description: 'Discover your unique money personality type and financial DNA'
    },
    {
      icon: '🎯',
      title: 'Receive Strategies',
      description: 'Get personalized recommendations tailored to your profile'
    }
  ]

  return (
    <section id="how-it-works" className="py-20 bg-white">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            How It Works
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Our scientifically-backed assessment reveals your money personality and provides 
            actionable strategies for financial success.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div key={index} className="text-center group">
              <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-3xl transform group-hover:scale-110 transition-transform duration-200">
                {step.icon}
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {step.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// Benefits section
const BenefitsSection: React.FC = () => {
  const benefits = [
    {
      icon: '💰',
      title: 'Build Wealth Faster',
      description: 'Strategies tailored to your personality help you save and invest more effectively'
    },
    {
      icon: '😌',
      title: 'Reduce Financial Stress',
      description: 'Understanding your money patterns helps eliminate anxiety about finances'
    },
    {
      icon: '🎯',
      title: 'Achieve Your Goals',
      description: 'Personalized action plans guide you toward your financial objectives'
    },
    {
      icon: '📈',
      title: 'Track Progress',
      description: 'Monitor your financial growth with our progress tracking tools'
    }
  ]

  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Why Choose Ratchet Money?
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Our approach combines psychology and finance to give you the most effective 
            strategies for your unique situation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {benefits.map((benefit, index) => (
            <div key={index} className="bg-white rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow duration-200">
              <div className="text-4xl mb-4">{benefit.icon}</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                {benefit.title}
              </h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                {benefit.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// Testimonials section
const TestimonialsSection: React.FC = () => {
  const testimonials = [
    {
      name: 'Sarah Johnson',
      role: 'Small Business Owner',
      content: 'This assessment completely changed how I think about money. I\'ve saved more in 3 months than I did all last year!',
      avatar: '/avatars/sarah.jpg'
    },
    {
      name: 'Michael Chen',
      role: 'Software Engineer',
      content: 'The personalized strategies are spot-on. I finally understand why I was struggling with saving and now have a clear path forward.',
      avatar: '/avatars/michael.jpg'
    },
    {
      name: 'Emily Rodriguez',
      role: 'Teacher',
      content: 'Simple, actionable advice that actually works. I\'ve reduced my financial stress and feel more confident about my future.',
      avatar: '/avatars/emily.jpg'
    }
  ]

  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            What Our Users Say
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Join thousands of people who have transformed their financial lives with our assessment.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <OptimizedImage
                  src={testimonial.avatar}
                  alt={`${testimonial.name} avatar`}
                  className="w-12 h-12 rounded-full mr-4"
                  width={48}
                  height={48}
                />
                <div>
                  <h4 className="font-semibold text-gray-900">{testimonial.name}</h4>
                  <p className="text-sm text-gray-600">{testimonial.role}</p>
                </div>
              </div>
              <p className="text-gray-700 italic">"{testimonial.content}"</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// Main landing page component
export const OptimizedLandingPage: React.FC = () => {
  const [showQuestionnaire, setShowQuestionnaire] = React.useState(false)
  const [assessmentComplete, setAssessmentComplete] = React.useState(false)
  const [results, setResults] = React.useState<any>(null)

  return (
    <>
      <Helmet>
        {/* SEO Meta Tags */}
        <title>Ratchet Money - Transform Your Financial Future | Free Money Personality Assessment</title>
        <meta name="description" content="Discover your money personality and get personalized strategies to build wealth, reduce stress, and achieve financial freedom. Take our free 2-minute assessment today." />
        <meta name="keywords" content="money personality, financial assessment, wealth building, financial freedom, money management, personal finance" />
        <meta name="author" content="Ratchet Money" />
        <meta name="robots" content="index, follow" />
        
        {/* Open Graph Tags */}
        <meta property="og:title" content="Ratchet Money - Transform Your Financial Future" />
        <meta property="og:description" content="Discover your money personality and get personalized strategies to build wealth, reduce stress, and achieve financial freedom." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://ratchetmoney.com" />
        <meta property="og:image" content="https://ratchetmoney.com/og-image.jpg" />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:site_name" content="Ratchet Money" />
        
        {/* Twitter Card Tags */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Ratchet Money - Transform Your Financial Future" />
        <meta name="twitter:description" content="Discover your money personality and get personalized strategies to build wealth, reduce stress, and achieve financial freedom." />
        <meta name="twitter:image" content="https://ratchetmoney.com/twitter-image.jpg" />
        
        {/* Additional SEO Tags */}
        <link rel="canonical" href="https://ratchetmoney.com" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
        <meta name="theme-color" content="#1f2937" />
        
        {/* Preload critical resources */}
        <link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="preload" href="/images/hero-bg.jpg" as="image" />
        
        {/* Structured Data */}
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "Ratchet Money",
            "description": "Transform your financial future with personalized money strategies",
            "url": "https://ratchetmoney.com",
            "potentialAction": {
              "@type": "SearchAction",
              "target": "https://ratchetmoney.com/search?q={search_term_string}",
              "query-input": "required name=search_term_string"
            }
          })}
        </script>
      </Helmet>

      <main className="landing-page">
        {!showQuestionnaire && !assessmentComplete && (
          <>
            <HeroSection />
            <HowItWorksSection />
            <BenefitsSection />
            <TestimonialsSection />
            
            {/* CTA Section */}
            <section className="py-20 bg-gradient-to-r from-blue-600 to-purple-600">
              <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
                  Ready to Transform Your Financial Future?
                </h2>
                <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
                  Join thousands of people who have discovered their money personality and 
                  are building wealth with confidence.
                </p>
                <button
                  onClick={() => setShowQuestionnaire(true)}
                  className="bg-white text-blue-600 px-8 py-4 text-lg font-semibold rounded-lg hover:bg-gray-100 transform hover:scale-105 transition-all duration-200 shadow-lg"
                >
                  Start Your Free Assessment Now
                </button>
              </div>
            </section>
          </>
        )}

        {showQuestionnaire && !assessmentComplete && (
          <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div></div>}>
            <section id="questionnaire-section" className="min-h-screen bg-gray-50 py-8">
              <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                <AssessmentForm
                  onCompleted={(results) => {
                    setResults(results)
                    setAssessmentComplete(true)
                    setShowQuestionnaire(false)
                  }}
                />
              </div>
            </section>
          </Suspense>
        )}

        {assessmentComplete && results && (
          <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div></div>}>
            <AssessmentResults
              data={results}
              email=""
            />
          </Suspense>
        )}
      </main>
    </>
  )
} 