import React, { useState, useRef, useEffect } from 'react';

interface ChartData {
  label: string;
  value: number;
  color: string;
  percentage?: number;
}

interface TouchOptimizedChartProps {
  data: ChartData[];
  type: 'bar' | 'pie' | 'progress' | 'salary-range';
  title?: string;
  subtitle?: string;
  className?: string;
  onDataPointClick?: (data: ChartData, index: number) => void;
  interactive?: boolean;
}

const TouchOptimizedChart: React.FC<TouchOptimizedChartProps> = ({
  data,
  type,
  title,
  subtitle,
  className = '',
  onDataPointClick,
  interactive = true
}) => {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);

  const maxValue = Math.max(...data.map(d => d.value));
  const totalValue = data.reduce((sum, d) => sum + d.value, 0);

  const handleTouchStart = (e: React.TouchEvent, index: number) => {
    setTouchStart(e.touches[0].clientX);
    setActiveIndex(index);
  };

  const handleTouchEnd = () => {
    setTouchStart(null);
    if (activeIndex !== null && onDataPointClick) {
      onDataPointClick(data[activeIndex], activeIndex);
    }
    setTimeout(() => setActiveIndex(null), 200);
  };

  const handleMouseEnter = (index: number) => {
    if (!interactive) return;
    setActiveIndex(index);
  };

  const handleMouseLeave = () => {
    if (!interactive) return;
    setActiveIndex(null);
  };

  const handleClick = (index: number) => {
    if (!interactive) return;
    if (onDataPointClick) {
      onDataPointClick(data[index], index);
    }
  };

  const BarChart = () => (
    <div className="space-y-3">
      {data.map((item, index) => (
        <div
          key={index}
          className="relative"
          onTouchStart={(e) => handleTouchStart(e, index)}
          onTouchEnd={handleTouchEnd}
          onMouseEnter={() => handleMouseEnter(index)}
          onMouseLeave={handleMouseLeave}
          onClick={() => handleClick(index)}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">{item.label}</span>
            <span className="text-sm text-gray-500">
              ${item.value.toLocaleString()}
            </span>
          </div>
          <div className="relative h-8 bg-gray-200 rounded-lg overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ease-out ${
                activeIndex === index ? 'opacity-90' : 'opacity-70'
              }`}
              style={{
                width: `${(item.value / maxValue) * 100}%`,
                backgroundColor: item.color,
                transform: activeIndex === index ? 'scaleY(1.05)' : 'scaleY(1)'
              }}
            />
            {activeIndex === index && (
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-semibold text-white drop-shadow">
                  {((item.value / maxValue) * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );

  const PieChart = () => {
    const radius = 80;
    const centerX = 100;
    const centerY = 100;
    let currentAngle = 0;

    return (
      <div className="relative">
        <svg width="200" height="200" className="mx-auto">
          <g transform={`translate(${centerX}, ${centerY})`}>
            {data.map((item, index) => {
              const percentage = item.value / totalValue;
              const angle = percentage * 2 * Math.PI;
              const x1 = radius * Math.cos(currentAngle);
              const y1 = radius * Math.sin(currentAngle);
              const x2 = radius * Math.cos(currentAngle + angle);
              const y2 = radius * Math.sin(currentAngle + angle);
              
              const largeArcFlag = angle > Math.PI ? 1 : 0;
              
              const pathData = [
                `M 0 0`,
                `L ${x1} ${y1}`,
                `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
                'Z'
              ].join(' ');

              currentAngle += angle;

              return (
                <path
                  key={index}
                  d={pathData}
                  fill={item.color}
                  opacity={activeIndex === index ? 0.9 : 0.7}
                  className="transition-all duration-200 cursor-pointer"
                  onTouchStart={(e) => handleTouchStart(e, index)}
                  onTouchEnd={handleTouchEnd}
                  onMouseEnter={() => handleMouseEnter(index)}
                  onMouseLeave={handleMouseLeave}
                  onClick={() => handleClick(index)}
                  style={{
                    transform: activeIndex === index ? 'scale(1.05)' : 'scale(1)',
                    transformOrigin: 'center'
                  }}
                />
              );
            })}
          </g>
        </svg>
        
        {/* Legend */}
        <div className="mt-4 space-y-2">
          {data.map((item, index) => (
            <div
              key={index}
              className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
                activeIndex === index ? 'bg-gray-100' : ''
              }`}
              onTouchStart={(e) => handleTouchStart(e, index)}
              onTouchEnd={handleTouchEnd}
              onMouseEnter={() => handleMouseEnter(index)}
              onMouseLeave={handleMouseLeave}
              onClick={() => handleClick(index)}
            >
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm font-medium">{item.label}</span>
              <span className="text-sm text-gray-500 ml-auto">
                ${item.value.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const ProgressChart = () => (
    <div className="space-y-4">
      {data.map((item, index) => (
        <div
          key={index}
          className="relative"
          onTouchStart={(e) => handleTouchStart(e, index)}
          onTouchEnd={handleTouchEnd}
          onMouseEnter={() => handleMouseEnter(index)}
          onMouseLeave={handleMouseLeave}
          onClick={() => handleClick(index)}
        >
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">{item.label}</span>
            <span className="text-sm text-gray-500">
              {item.percentage || ((item.value / maxValue) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="relative h-4 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ease-out ${
                activeIndex === index ? 'opacity-90' : 'opacity-70'
              }`}
              style={{
                width: `${item.percentage || (item.value / maxValue) * 100}%`,
                backgroundColor: item.color,
                transform: activeIndex === index ? 'scaleY(1.1)' : 'scaleY(1)'
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );

  const SalaryRangeChart = () => (
    <div className="space-y-6">
      <div className="relative h-12 bg-gray-100 rounded-lg overflow-hidden">
        <div className="absolute inset-0 flex items-center px-4">
          <div className="flex-1 relative">
            {/* Range segments */}
            {data.map((item, index) => {
              const startPercent = index === 0 ? 0 : 
                data.slice(0, index).reduce((sum, d) => sum + (d.value / totalValue) * 100, 0);
              const width = (item.value / totalValue) * 100;
              
              return (
                <div
                  key={index}
                  className="absolute h-6 rounded transition-all duration-200"
                  style={{
                    left: `${startPercent}%`,
                    width: `${width}%`,
                    backgroundColor: item.color,
                    opacity: activeIndex === index ? 0.9 : 0.7,
                    transform: activeIndex === index ? 'scaleY(1.1)' : 'scaleY(1)'
                  }}
                  onTouchStart={(e) => handleTouchStart(e, index)}
                  onTouchEnd={handleTouchEnd}
                  onMouseEnter={() => handleMouseEnter(index)}
                  onMouseLeave={handleMouseLeave}
                  onClick={() => handleClick(index)}
                />
              );
            })}
          </div>
        </div>
      </div>
      
      {/* Labels */}
      <div className="flex justify-between text-xs text-gray-500">
        {data.map((item, index) => (
          <div
            key={index}
            className={`text-center transition-all ${
              activeIndex === index ? 'font-semibold text-gray-700' : ''
            }`}
            onTouchStart={(e) => handleTouchStart(e, index)}
            onTouchEnd={handleTouchEnd}
            onMouseEnter={() => handleMouseEnter(index)}
            onMouseLeave={handleMouseLeave}
            onClick={() => handleClick(index)}
          >
            <div className="font-medium">{item.label}</div>
            <div>${item.value.toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderChart = () => {
    switch (type) {
      case 'bar':
        return <BarChart />;
      case 'pie':
        return <PieChart />;
      case 'progress':
        return <ProgressChart />;
      case 'salary-range':
        return <SalaryRangeChart />;
      default:
        return <BarChart />;
    }
  };

  return (
    <div className={`bg-white rounded-lg p-6 shadow-sm ${className}`}>
      {title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {subtitle && (
            <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
          )}
        </div>
      )}
      
      <div ref={chartRef} className="touch-manipulation">
        {renderChart()}
      </div>
    </div>
  );
};

export default TouchOptimizedChart; 