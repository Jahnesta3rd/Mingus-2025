import React, { useState, useEffect } from "react";
import { ArrowUpRight, CheckCircle, ShieldCheck, TrendingUp, Building, Users, MapPin } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// Testimonial data with diverse representation and real challenges
const testimonials = [
  { 
    quote: "Finally, a money app that gets my life - juggling student loans, childcare, and helping my parents", 
    author: "Keisha, 28, Atlanta, Healthcare Professional" 
  },
  { 
    quote: "Helped me see the connection between my stress and spending after losing my job", 
    author: "Marcus, 31, Houston, Tech Professional" 
  },
  {
    quote: "As a single mom, this helps me plan for everything - from daycare to my parents' medical bills",
    author: "Aisha, 35, Chicago, Educator"
  }
];

export default function EducationalCardJobSecurity({ onSeeScore, testimonialIndex = 0 }) {
  const [expanded, setExpanded] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showSuccess, setShowSuccess] = useState(false);
  const [score] = useState(78); // Demo score

  // Animate progress bar
  useEffect(() => {
    if (expanded && score) {
      setTimeout(() => setProgress(score), 300);
    } else {
      setProgress(0);
    }
  }, [expanded, score]);

  // Animate success checkmark
  useEffect(() => {
    if (showSuccess) {
      const t = setTimeout(() => setShowSuccess(false), 1200);
      return () => clearTimeout(t);
    }
  }, [showSuccess]);

  const handleTryIt = () => {
    setShowSuccess(true);
    // Mock functionality - would show real score
    setTimeout(() => {
      alert("This would show your real career confidence score based on your industry, location, and role!");
    }, 500);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      setExpanded((e) => !e);
    }
  };

  return (
    <motion.div
      initial={{ x: 80, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 60, damping: 18 }}
      className="bg-gray-900 rounded-xl p-6 shadow-lg text-white max-w-lg mx-auto mb-6"
      role="region"
      aria-labelledby="career-confidence-title"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 id="career-confidence-title" className="text-2xl font-bold text-blue-400">
          Your Career Confidence Score
        </h2>
        <motion.div
          animate={{ scale: [1, 1.15, 1] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
          aria-hidden="true"
        >
          <ShieldCheck className="w-8 h-8 text-blue-400" />
        </motion.div>
      </div>
      
      <p className="mb-3 text-gray-200">
        We analyze your industry trends, skill demand, and local job market to give you a clear picture of your career stability. 
        Think of it as your professional weather forecast - helping you prepare for opportunities and challenges ahead, 
        whether you're dealing with job transitions, student loan payments, or supporting family members.
      </p>
      
      <ul className="mb-3 space-y-1" role="list">
        {[
          "Industry growth tracking",
          "Skill gap identification", 
          "Local market insights",
          "Promotion pathway mapping"
        ].map((item, i) => (
          <li key={i} className="flex items-center" role="listitem">
            <motion.span
              initial={{ scale: 0.7 }}
              animate={{ scale: expanded ? 1.2 : 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 10 }}
              className="mr-2"
              aria-hidden="true"
            >
              <CheckCircle className="text-green-400 w-4 h-4" />
            </motion.span>
            <span className="text-gray-200">{item}</span>
          </li>
        ))}
      </ul>

      <button
        className="text-blue-400 underline mb-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-900 rounded"
        onClick={() => setExpanded((e) => !e)}
        onKeyDown={handleKeyDown}
        aria-expanded={expanded}
        aria-controls="career-details"
        tabIndex={0}
      >
        {expanded ? "Hide details" : "Tap to expand details"}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            id="career-details"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="overflow-hidden"
            role="region"
            aria-labelledby="career-details-title"
          >
            {/* Animated Progress Bar */}
            <div className="mb-4">
              <div className="flex items-center mb-1">
                <span className="text-sm text-gray-400 mr-2">Demo Score</span>
                <TrendingUp className="w-4 h-4 text-blue-400" aria-hidden="true" />
              </div>
              <div 
                className="w-full bg-gray-700 rounded-full h-3"
                role="progressbar"
                aria-valuenow={progress}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Career confidence score: ${progress} percent`}
              >
                <motion.div
                  className="bg-blue-400 h-3 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 1.2, ease: "easeOut" }}
                />
              </div>
              <span className="text-blue-400 font-bold">{progress}%</span>
            </div>

            {/* Data Visualization Preview */}
            <div className="mb-4 p-3 bg-gray-800 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Industry Analysis Preview</span>
                <div className="flex space-x-1" aria-hidden="true">
                  <Building className="w-4 h-4 text-blue-400" />
                  <Users className="w-4 h-4 text-green-400" />
                  <MapPin className="w-4 h-4 text-purple-400" />
                </div>
              </div>
              <svg 
                width="100%" 
                height="60" 
                className="mb-2"
                role="img"
                aria-labelledby="industry-trend-chart"
              >
                <title id="industry-trend-chart">Industry growth trend showing upward trajectory</title>
                {/* Sample upward trending line graph */}
                <polyline
                  points="0,50 20,45 40,35 60,25 80,15 100,10"
                  fill="none"
                  stroke="#60a5fa"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {/* Add some data points */}
                <circle cx="20" cy="45" r="3" fill="#60a5fa" />
                <circle cx="40" cy="35" r="3" fill="#60a5fa" />
                <circle cx="60" cy="25" r="3" fill="#60a5fa" />
                <circle cx="80" cy="15" r="3" fill="#60a5fa" />
                <circle cx="100" cy="10" r="3" fill="#60a5fa" />
              </svg>
              <div className="text-xs text-gray-400">
                Growth trend: +12% YoY • Local demand: High • Skills gap: Low
              </div>
            </div>

            {/* Why it matters */}
            <div className="mb-4">
              <span className="block text-gray-400 font-semibold mb-1">Why it matters:</span>
              <span className="text-gray-200">
                Knowledge is power. When you understand your career landscape, you can make informed decisions 
                that build wealth, not just pay bills. This helps you navigate challenges like job transitions, 
                student loan repayment, or supporting family members with confidence.
              </span>
            </div>

            {/* Try It Button */}
            <button
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-900"
              onClick={handleTryIt}
              aria-describedby="try-it-description"
            >
              Try It
            </button>
            <div id="try-it-description" className="sr-only">
              Opens your personalized career confidence score dashboard
            </div>

            {/* Success checkmark */}
            <AnimatePresence>
              {showSuccess && (
                <motion.div
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1.2, opacity: 1 }}
                  exit={{ scale: 0.5, opacity: 0 }}
                  transition={{ type: "spring", bounce: 0.7, duration: 0.6 }}
                  className="flex items-center mt-2"
                  role="status"
                  aria-live="polite"
                >
                  <CheckCircle className="text-green-400 mr-2" aria-hidden="true" />
                  <span className="text-green-400 font-semibold">Success!</span>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Testimonial */}
      <div className="mt-4 text-sm text-gray-400 italic border-t border-gray-800 pt-2">
        <blockquote>
          <span>"{testimonials[testimonialIndex % testimonials.length].quote}"</span>
          <footer className="block text-right text-gray-500 mt-1">
            — {testimonials[testimonialIndex % testimonials.length].author}
          </footer>
        </blockquote>
      </div>
    </motion.div>
  );
} 