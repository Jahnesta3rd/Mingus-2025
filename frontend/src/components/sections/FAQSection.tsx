import React from 'react';
import { ChevronDown } from 'lucide-react';

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQSectionProps {
  faqData: FAQItem[];
  openFAQ: number | null;
  onToggleFAQ: (index: number) => void;
  onKeyDown: (event: React.KeyboardEvent, index: number) => void;
}

const FAQSection: React.FC<FAQSectionProps> = ({
  faqData,
  openFAQ,
  onToggleFAQ,
  onKeyDown
}) => {
  return (
    <section id="faq" className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-slate-900 to-slate-800" role="region" aria-label="Frequently asked questions">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
            Frequently Asked Questions
          </h2>
          <p className="text-xl text-gray-300">
            Everything you need to know about Mingus
          </p>
        </div>
        
        <div className="space-y-4 sm:space-y-6">
          {faqData.map((faq, index) => (
            <div 
              key={index} 
              className={`bg-slate-800/80 backdrop-blur-sm rounded-xl border border-slate-700/50 shadow-xl transition-all duration-300 hover:border-violet-500/30 hover:bg-slate-800/90 hover:shadow-2xl hover:shadow-violet-500/10 ${
                openFAQ === index ? 'ring-2 ring-violet-500/50 shadow-2xl shadow-violet-500/20' : ''
              }`}
            >
              <button
                className="w-full px-4 sm:px-6 py-4 sm:py-5 text-left flex justify-between items-center hover:bg-slate-700/30 transition-all duration-300 rounded-xl group focus-ring focus-visible:ring-4 focus-visible:ring-violet-500 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-800"
                onClick={() => onToggleFAQ(index)}
                onKeyDown={(e) => onKeyDown(e, index)}
                aria-expanded={openFAQ === index}
                aria-controls={`faq-answer-${index}`}
                id={`faq-question-${index}`}
                tabIndex={0}
              >
                <span className="font-semibold text-gray-100 group-hover:text-violet-300 transition-colors duration-300 pr-4 text-sm sm:text-base">
                  {faq.question}
                </span>
                <div className="flex-shrink-0">
                  <div className={`transform transition-all duration-300 ease-in-out ${
                    openFAQ === index ? 'rotate-180 scale-110' : 'rotate-0 scale-100'
                  }`}>
                    <ChevronDown className="w-4 h-4 sm:w-5 sm:h-5 text-violet-400 group-hover:text-violet-300 transition-colors duration-300" />
                  </div>
                </div>
              </button>
              <div 
                id={`faq-answer-${index}`}
                role="region"
                aria-labelledby={`faq-question-${index}`}
                className={`overflow-hidden transition-all duration-500 ease-in-out ${
                  openFAQ === index 
                    ? 'max-h-96 opacity-100' 
                    : 'max-h-0 opacity-0'
                }`}
              >
                <div className="px-4 sm:px-6 pb-4 sm:pb-5 pt-2">
                  <div className="border-t border-slate-700/50 pt-4">
                    <p className="text-gray-300 leading-relaxed text-sm sm:text-base">
                      {faq.answer}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FAQSection;

