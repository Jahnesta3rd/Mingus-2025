import React, { useState, useEffect } from "react";
import { ArrowUpRight, CheckCircle, Calendar, DollarSign, AlertTriangle, TrendingUp, Clock } from "lucide-react";
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

export default function EducationalCardCashFlow({ onSeePlanner, testimonialIndex = 1 }) {
  const [expanded, setExpanded] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showSuccess, setShowSuccess] = useState(false);
  const [score] = useState(85); // Demo score

  // Sample important dates for the calendar visual - reflecting real life challenges
  const importantDates = [
    { day: 5, label: "Childcare Payment", amount: 800, type: "expense" },
    { day: 12, label: "Student Loan", amount: 350, type: "expense" },
    { day: 18, label: "Parents' Medical", amount: 200, type: "expense" },
    { day: 25, label: "Family Dinner", amount: 120, type: "expense" },
    { day: 15, label: "Payday", amount: 3200, type: "income" }
  ];

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
    // Mock functionality - would show real planner
    setTimeout(() => {
      alert("This would show your personalized cash flow planner with your actual income, expenses, and important dates!");
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
      aria-labelledby="smart-money-title"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 id="smart-money-title" className="text-2xl font-bold text-blue-400" className="text-2xl font-semibold text-gray-800 mb-4">
          Smart Money Moves, Real Life Focus
        </h2>
        <motion.div
          animate={{ scale: [1, 1.15, 1] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
          aria-hidden="true"
        >
          <Calendar className="w-8 h-8 text-blue-400" />
        </motion.div>
      </div>
      
      <p className="mb-3 text-gray-200">
        We map your income and expenses against your actual life - childcare payments, student loans, 
        family medical expenses, and community events. No more surprise broke weeks. 
        Take control of your money to support what matters most to you and your family.
      </p>
      
      <ul className="mb-3 space-y-1" role="list">
        {[
          "Income & expense tracking",
          "Important date planning that leaves you with the cash required on those dates",
          "Emergency buffer alerts",
          "'What-if' spending scenarios"
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
        className="text-blue-400 underline mb-2 text-base leading-relaxed focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-900 rounded"
        onClick={() => setExpanded((e) => !e)}
        onKeyDown={handleKeyDown}
        aria-expanded={expanded}
        aria-controls="cashflow-details"
        tabIndex={0}
      >
        {expanded ? "Hide details" : "Tap to expand details"}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            id="cashflow-details"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="overflow-hidden"
            role="region"
            aria-labelledby="cashflow-details-title"
          >
            {/* Animated Progress Bar */}
            <div className="mb-4">
              <div className="flex items-center mb-1">
                <span className="text-base leading-relaxed text-gray-400 mr-2">Planning Score</span>
                <TrendingUp className="w-4 h-4 text-blue-400" aria-hidden="true" />
              </div>
              <div 
                className="w-full bg-gray-700 rounded-full h-3"
                role="progressbar"
                aria-valuenow={progress}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Cash flow planning score: ${progress} percent`}
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

            {/* Calendar with Money Icons */}
            <div className="mb-4 p-3 bg-gray-800 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <span className="text-base leading-relaxed text-gray-400">Monthly Calendar Preview</span>
                <div className="flex space-x-1" aria-hidden="true">
                  <DollarSign className="w-4 h-4 text-green-400" />
                  <AlertTriangle className="w-4 h-4 text-yellow-400" />
                  <Clock className="w-4 h-4 text-blue-400" />
                </div>
              </div>
              
              {/* Calendar Grid */}
              <div 
                className="grid grid-cols-7 gap-1 mb-2"
                role="grid"
                aria-label="Monthly calendar showing important financial dates"
              >
                {Array.from({ length: 31 }, (_, i) => {
                  const day = i + 1;
                  const event = importantDates.find(d => d.day === day);
                  return (
                    <div
                      key={day}
                      className={`
                        w-6 h-6 rounded text-base leading-relaxed flex items-center justify-center relative
                        ${event ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'}
                      `}
                      role="gridcell"
                      aria-label={event ? `${day}: ${event.label} - $${event.amount}` : `${day}`}
                    >
                      {day}
                      {event && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ delay: day * 0.05 }}
                          className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-400 rounded-full"
                          aria-hidden="true"
                        />
                      )}
                    </div>
                  );
                })}
              </div>
              
              {/* Event Legend */}
              <div className="text-base leading-relaxed text-gray-400 space-y-1">
                {importantDates.slice(0, 3).map((event, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="flex items-center">
                      <DollarSign className={`w-3 h-3 mr-1 ${event.type === 'income' ? 'text-green-400' : 'text-red-400'}`} aria-hidden="true" />
                      {event.label}
                    </span>
                    <span className={event.type === 'income' ? 'text-green-400' : 'text-red-400'}>
                      ${event.amount}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Cash Flow Line Graph */}
            <div className="mb-4 p-3 bg-gray-800 rounded-lg">
              <div className="text-base leading-relaxed text-gray-400 mb-2">Cash Flow Trend</div>
              <svg 
                width="100%" 
                height="40"
                role="img"
                aria-labelledby="cashflow-trend-chart"
              >
                <title id="cashflow-trend-chart">Cash flow trend showing monthly income and expenses</title>
                {/* Sample cash flow line */}
                <polyline
                  points="0,30 20,25 40,35 60,20 80,15 100,10"
                  fill="none"
                  stroke="#60a5fa"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {/* Add some data points */}
                <circle cx="20" cy="25" r="2" fill="#60a5fa" />
                <circle cx="40" cy="35" r="2" fill="#60a5fa" />
                <circle cx="60" cy="20" r="2" fill="#60a5fa" />
                <circle cx="80" cy="15" r="2" fill="#60a5fa" />
                <circle cx="100" cy="10" r="2" fill="#60a5fa" />
              </svg>
              <div className="text-base leading-relaxed text-gray-400 mt-1">
                Net cash flow: +$1,200 this month • Emergency buffer: 2.5 months
              </div>
            </div>

            {/* Why it matters */}
            <div className="mb-4">
              <span className="block text-gray-400 font-semibold mb-1">Why it matters:</span>
              <span className="text-gray-200">
                Your money should work around your life, not the other way around. 
                Plan for what matters most to you and your family - whether that's childcare, 
                student loans, supporting parents, or building community. Take control of your 
                financial future with confidence.
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
              Opens your personalized cash flow planner dashboard
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
      <div className="mt-4 text-base leading-relaxed text-gray-400 italic border-t border-gray-800 pt-2">
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