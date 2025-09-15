import React, { useState, useEffect } from 'react';

const ResponsiveTestComponent: React.FC = () => {
  const [currentBreakpoint, setCurrentBreakpoint] = useState<string>('');
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const updateWindowSize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      setWindowSize({ width, height });

      // Determine current breakpoint
      if (width <= 375) {
        setCurrentBreakpoint('Mobile Small (≤375px)');
      } else if (width <= 414) {
        setCurrentBreakpoint('Mobile Medium (376px-414px)');
      } else if (width <= 768) {
        setCurrentBreakpoint('Mobile Large (415px-768px)');
      } else if (width <= 1024) {
        setCurrentBreakpoint('Tablet (769px-1024px)');
      } else {
        setCurrentBreakpoint('Desktop (≥1025px)');
      }
    };

    updateWindowSize();
    window.addEventListener('resize', updateWindowSize);
    return () => window.removeEventListener('resize', updateWindowSize);
  }, []);

  return (
    <div 
      className="fixed top-4 right-4 bg-black/80 text-white p-4 rounded-lg z-50 text-sm"
      role="complementary"
      aria-label="Responsive test information"
    >
      <div className="font-bold mb-2">Responsive Test</div>
      <div>Breakpoint: {currentBreakpoint}</div>
      <div>Size: {windowSize.width} × {windowSize.height}</div>
    </div>
  );
};

export default ResponsiveTestComponent;
