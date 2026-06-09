import React from 'react';
import { WaterfallWidget } from '../components/waterfall';

const WaterfallPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        <WaterfallWidget />
      </div>
    </div>
  );
};

export default WaterfallPage;
