import React, { useState } from "react";
import { motion } from "framer-motion";
import { Play, ArrowRight } from "lucide-react";
import EducationFlow from "./EducationFlow";

export default function EducationFlowDemo() {
  const [showEducation, setShowEducation] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  const handleStartEducation = () => {
    setShowEducation(true);
  };

  const handleCompleteEducation = () => {
    setIsCompleted(true);
    setShowEducation(false);
    // Here you would typically navigate to the main app or onboarding
    alert("Education flow completed! Ready to start using Mingus.");
  };

  const handleSkipEducation = () => {
    setShowEducation(false);
    // Here you would typically navigate to the main app or onboarding
    alert("Education skipped! You can always access this tour later from the help menu.");
  };

  if (showEducation) {
    return (
      <EducationFlow 
        onComplete={handleCompleteEducation}
        onSkip={handleSkipEducation}
      />
    );
  }

  if (isCompleted) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <div className="bg-gray-900 rounded-xl p-8 shadow-lg text-white max-w-md mx-auto">
            <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <Play className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-4">Welcome to Mingus!</h2>
            <p className="text-gray-300 mb-6">
              You're all set to start your financial wellness journey. 
              Ready to take control of your money and your life?
            </p>
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2 mx-auto"
            >
              <span>Go to Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="text-center"
      >
        <div className="bg-gray-900 rounded-xl p-8 shadow-lg text-white max-w-md mx-auto">
          <h1 className="text-3xl font-bold text-white mb-4">Welcome to Mingus</h1>
          <p className="text-gray-300 mb-6">
            Let's take a quick tour to see how Mingus can help you achieve financial wellness 
            that fits your real life.
          </p>
          <button
            onClick={handleStartEducation}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2 mx-auto"
          >
            <Play className="w-4 h-4" />
            <span>Start Tour</span>
          </button>
          <button
            onClick={handleSkipEducation}
            className="mt-4 text-gray-400 hover:text-gray-300 underline text-sm"
          >
            Skip for now
          </button>
        </div>
      </motion.div>
    </div>
  );
} 