import React, { useState, useEffect } from "react";
import { ArrowUpRight, CheckCircle, HeartPulse, Smile, Users, Brain, DollarSign } from "lucide-react";
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

export default function EducationalCardWellness({ onSeeWellness, testimonialIndex = 0 }) {
  const [expanded, setExpanded] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showSuccess, setShowSuccess] = useState(false);
  const [score] = useState(72); // Demo score

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
    // Mock functionality - would show real wellness tracking
    setTimeout(() => {
      alert("This would show your personalized wellness tracking dashboard with health metrics and spending correlations!");
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
      aria-labelledby="wellness-title"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 id="wellness-title" className="text-2xl font-bold text-blue-400">
          Whole-Life Wellness = Wealth
        </h2>
        <motion.div
          animate={{ scale: [1, 1.15, 1] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
          aria-hidden="true"
        >
          <HeartPulse className="w-8 h-8 text-blue-400" />
        </motion.div>
      </div>
      
      <p className="mb-3 text-gray-200">
        Your physical and mental health directly impact your money decisions. We track how stress, 
        relationships, and self-care connect to your spending patterns. Whether you're managing 
        family responsibilities, work stress, or financial pressures, understanding these connections 
        helps you build sustainable money habits.
      </p>
      
      <ul className="mb-3 space-y-1" role="list">
        {[
          "Physical activity tracking",
          "Stress & mental health check-ins",
          "Relationship health monitoring",
          "Mindfulness practice logging"
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
        aria-controls="wellness-details"
        tabIndex={0}
      >
        {expanded ? "Hide details" : "Tap to expand details"}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            id="wellness-details"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="overflow-hidden"
            role="region"
            aria-labelledby="wellness-details-title"
          >
            {/* Animated Progress Bar */}
            <div className="mb-4">
              <div className="flex items-center mb-1">
                <span className="text-sm text-gray-400 mr-2">Wellness Score</span>
                <HeartPulse className="w-4 h-4 text-blue-400" aria-hidden="true" />
              </div>
              <div 
                className="w-full bg-gray-700 rounded-full h-3"
                role="progressbar"
                aria-valuenow={progress}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Wellness score: ${progress} percent`}
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

            {/* Interconnected Circles Visualization */}
            <div className="mb-4 p-3 bg-gray-800 rounded-lg">
              <div className="text-sm text-gray-400 mb-3 text-center">Health Metrics Connection</div>
              <div className="relative h-32 flex items-center justify-center">
                {/* Central Dollar Sign */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                  className="absolute z-10 bg-blue-600 rounded-full w-12 h-12 flex items-center justify-center"
                  aria-hidden="true"
                >
                  <DollarSign className="w-6 h-6 text-white" />
                </motion.div>
                
                {/* Health Metrics Circles */}
                {[
                  { icon: HeartPulse, color: "bg-red-500", position: "top-0 left-1/2 transform -translate-x-1/2", label: "Physical" },
                  { icon: Brain, color: "bg-purple-500", position: "top-1/2 right-0 transform translate-y-1/2", label: "Mental" },
                  { icon: Users, color: "bg-green-500", position: "bottom-0 left-1/2 transform -translate-x-1/2", label: "Social" },
                  { icon: Smile, color: "bg-yellow-500", position: "top-1/2 left-0 transform translate-y-1/2", label: "Emotional" }
                ].map((metric, i) => (
                  <motion.div
                    key={i}
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.4 + i * 0.1, type: "spring" }}
                    className={`absolute ${metric.position} ${metric.color} rounded-full w-8 h-8 flex items-center justify-center`}
                    aria-hidden="true"
                  >
                    <metric.icon className="w-4 h-4 text-white" />
                  </motion.div>
                ))}
                
                {/* Connection Lines */}
                <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 5 }} aria-hidden="true">
                  {[0, 1, 2, 3].map((i) => (
                    <motion.line
                      key={i}
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                      transition={{ delay: 0.8 + i * 0.1, duration: 0.8 }}
                      x1="50%"
                      y1="50%"
                      x2={i === 0 ? "50%" : i === 1 ? "75%" : i === 2 ? "50%" : "25%"}
                      y2={i === 0 ? "25%" : i === 1 ? "50%" : i === 2 ? "75%" : "50%"}
                      stroke="#60a5fa"
                      strokeWidth="2"
                      strokeDasharray="5,5"
                    />
                  ))}
                </svg>
              </div>
              
              {/* Metrics Labels */}
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 mt-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-red-500 rounded-full mr-1" aria-hidden="true"></div>
                  Physical Health
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-purple-500 rounded-full mr-1" aria-hidden="true"></div>
                  Mental Health
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-1" aria-hidden="true"></div>
                  Social Health
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full mr-1" aria-hidden="true"></div>
                  Emotional Health
                </div>
              </div>
            </div>

            {/* Health-Spending Correlation Chart */}
            <div className="mb-4 p-3 bg-gray-800 rounded-lg">
              <div className="text-sm text-gray-400 mb-2">Health-Spending Correlation</div>
              <div className="space-y-2">
                {[
                  { health: "High Stress", spending: "Impulse purchases up 40%", color: "text-red-400" },
                  { health: "Good Sleep", spending: "Better financial decisions", color: "text-green-400" },
                  { health: "Regular Exercise", spending: "Reduced stress spending", color: "text-blue-400" }
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 1.2 + i * 0.1 }}
                    className="flex justify-between items-center text-xs"
                  >
                    <span className="text-gray-300">{item.health}</span>
                    <span className={item.color}>{item.spending}</span>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Why it matters */}
            <div className="mb-4">
              <span className="block text-gray-400 font-semibold mb-1">Why it matters:</span>
              <span className="text-gray-200">
                When you're stressed or exhausted, you spend differently. Understanding these patterns 
                helps you build better money habits that stick. Whether you're managing family responsibilities, 
                work stress, or financial pressures, taking care of your wellness is an investment in your 
                financial future.
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
              Opens your personalized wellness tracking dashboard
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