import React from 'react';
import { Link } from 'react-router-dom';
import { WaterfallWidget } from '../components/waterfall';

const WaterfallPage: React.FC = () => {
  return (
    <div className="min-h-screen" style={{ background: 'var(--whisper-purple, #faf5ff)' }}>
      <div className="border-b bg-white px-4 py-4 sm:px-6" style={{ borderColor: '#e8e1f0' }}>
        <div className="mx-auto flex max-w-3xl items-center gap-4">
          <Link
            to="/dashboard/tools"
            className="text-sm font-semibold text-[#5b2d8e] hover:underline"
          >
            ← Dashboard
          </Link>
        </div>
      </div>
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        <WaterfallWidget />
      </div>
    </div>
  );
};

export default WaterfallPage;
