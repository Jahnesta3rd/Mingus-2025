// Chart utility functions for creating and managing charts
// This assumes you're using Chart.js or a similar charting library

// Import Chart.js if available
let Chart;
if (typeof window !== 'undefined' && window.Chart) {
  Chart = window.Chart;
} else {
  console.warn('Chart.js is not loaded. Please include Chart.js in your project.');
}

// Chart color schemes
const chartColors = {
  primary: '#3B82F6',
  secondary: '#10B981',
  accent: '#8B5CF6',
  warning: '#F59E0B',
  danger: '#EF4444',
  success: '#22C55E',
  info: '#06B6D4',
  light: '#F3F4F6',
  dark: '#1F2937',
  gray: '#6B7280'
};

const gradientColors = {
  blue: ['#3B82F6', '#1D4ED8'],
  green: ['#10B981', '#059669'],
  purple: ['#8B5CF6', '#7C3AED'],
  orange: ['#F59E0B', '#D97706']
};

// Helper function to create gradient
const createGradient = (ctx, colors, direction = 'vertical') => {
  const gradient = direction === 'vertical' 
    ? ctx.createLinearGradient(0, 0, 0, 400)
    : ctx.createLinearGradient(0, 0, 400, 0);
  
  gradient.addColorStop(0, colors[0]);
  gradient.addColorStop(1, colors[1]);
  
  return gradient;
};

// Helper function to destroy existing chart
const destroyChart = (chartInstance) => {
  if (chartInstance && typeof chartInstance.destroy === 'function') {
    chartInstance.destroy();
  }
};

// Helper function to create chart container
const createChartContainer = (id, height = '400px') => {
  const existingCanvas = document.getElementById(id);
  if (existingCanvas) {
    return existingCanvas;
  }

  const container = document.createElement('div');
  container.className = 'chart-container';
  container.style.height = height;
  container.style.position = 'relative';

  const canvas = document.createElement('canvas');
  canvas.id = id;
  canvas.style.width = '100%';
  canvas.style.height = '100%';

  container.appendChild(canvas);
  return canvas;
};

// Helper function to update chart data
const updateChartData = (chartInstance, newData) => {
  if (chartInstance && typeof chartInstance.data === 'object') {
    chartInstance.data = newData;
    chartInstance.update('active');
  }
};

// 1. Salary Distribution Chart (Histogram)
export const createSalaryChart = (canvasId, data) => {
  if (!Chart) return null;

  const canvas = createChartContainer(canvasId);
  const ctx = canvas.getContext('2d');

  // Generate salary distribution data
  const generateSalaryDistribution = (meanSalary, stdDev = meanSalary * 0.3) => {
    const distribution = [];
    const min = Math.max(meanSalary * 0.4, 30000);
    const max = meanSalary * 1.8;
    const buckets = 20;
    const bucketSize = (max - min) / buckets;

    for (let i = 0; i < buckets; i++) {
      const bucketStart = min + (i * bucketSize);
      const bucketEnd = bucketStart + bucketSize;
      const bucketCenter = (bucketStart + bucketEnd) / 2;
      
      // Simple normal distribution approximation
      const frequency = Math.exp(-Math.pow((bucketCenter - meanSalary) / stdDev, 2) / 2);
      
      distribution.push({
        x: bucketCenter,
        y: frequency * 100
      });
    }

    return distribution;
  };

  const distribution = generateSalaryDistribution(data.peerAverage || 75000);
  
  // Create gradient
  const gradient = createGradient(ctx, gradientColors.blue);

  const chartData = {
    labels: distribution.map(d => `$${Math.round(d.x / 1000)}k`),
    datasets: [{
      label: 'Salary Distribution',
      data: distribution.map(d => d.y),
      backgroundColor: gradient,
      borderColor: chartColors.primary,
      borderWidth: 1,
      borderRadius: 4,
      fill: true
    }]
  };

  const config = {
    type: 'bar',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Salary Distribution in Your Market',
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => `Frequency: ${context.parsed.y.toFixed(1)}%`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Frequency (%)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Salary Range'
          }
        }
      }
    }
  };

  destroyChart(window[`chart_${canvasId}`]);
  window[`chart_${canvasId}`] = new Chart(ctx, config);
  return window[`chart_${canvasId}`];
};

// 2. Career Progression Chart (Line Chart)
export const createCareerChart = (canvasId, data) => {
  if (!Chart) return null;

  const canvas = createChartContainer(canvasId);
  const ctx = canvas.getContext('2d');

  // Create gradient for the line
  const gradient = createGradient(ctx, gradientColors.green);

  const chartData = {
    labels: data.labels || ['Current', '1 Year', '3 Years', '5 Years'],
    datasets: [{
      label: 'Salary Progression',
      data: data.data || [75000, 85000, 95000, 110000],
      borderColor: chartColors.success,
      backgroundColor: gradient,
      borderWidth: 3,
      fill: true,
      tension: 0.4,
      pointBackgroundColor: chartColors.success,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 6,
      pointHoverRadius: 8
    }]
  };

  const config = {
    type: 'line',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Career Salary Progression',
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => `Salary: $${context.parsed.y.toLocaleString()}`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: 'Salary ($)'
          },
          ticks: {
            callback: (value) => `$${value.toLocaleString()}`
          }
        },
        x: {
          title: {
            display: true,
            text: 'Time Period'
          }
        }
      }
    }
  };

  destroyChart(window[`chart_${canvasId}`]);
  window[`chart_${canvasId}`] = new Chart(ctx, config);
  return window[`chart_${canvasId}`];
};

// 3. Skill Impact Chart (Horizontal Bar Chart)
export const createSkillImpactChart = (canvasId, skills, impacts) => {
  if (!Chart) return null;

  const canvas = createChartContainer(canvasId);
  const ctx = canvas.getContext('2d');

  const chartData = {
    labels: skills,
    datasets: [{
      label: 'Salary Impact',
      data: impacts,
      backgroundColor: impacts.map(impact => {
        if (impact > 15) return chartColors.success;
        if (impact > 10) return chartColors.warning;
        return chartColors.info;
      }),
      borderColor: chartColors.dark,
      borderWidth: 1,
      borderRadius: 4
    }]
  };

  const config = {
    type: 'bar',
    data: chartData,
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Skill Impact on Salary',
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => `+${context.parsed.x}% salary increase`
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Salary Impact (%)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Skills'
          }
        }
      }
    }
  };

  destroyChart(window[`chart_${canvasId}`]);
  window[`chart_${canvasId}`] = new Chart(ctx, config);
  return window[`chart_${canvasId}`];
};

// 4. ROI Chart (Doughnut Chart)
export const createROIChart = (canvasId, data) => {
  if (!Chart) return null;

  const canvas = createChartContainer(canvasId);
  const ctx = canvas.getContext('2d');

  const chartData = {
    labels: data.investments?.map(inv => inv.name) || ['Education', 'Certifications', 'Skills'],
    datasets: [{
      data: data.investments?.map(inv => inv.roi) || [30, 25, 20],
      backgroundColor: [
        chartColors.primary,
        chartColors.secondary,
        chartColors.accent,
        chartColors.warning,
        chartColors.danger
      ],
      borderColor: '#fff',
      borderWidth: 2,
      hoverOffset: 4
    }]
  };

  const config = {
    type: 'doughnut',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Investment ROI by Category',
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          position: 'bottom'
        },
        tooltip: {
          callbacks: {
            label: (context) => `${context.label}: ${context.parsed}% ROI`
          }
        }
      }
    }
  };

  destroyChart(window[`chart_${canvasId}`]);
  window[`chart_${canvasId}`] = new Chart(ctx, config);
  return window[`chart_${canvasId}`];
};

// 5. Progress Chart (Doughnut Chart)
export const createProgressChart = (canvasId, data) => {
  if (!Chart) return null;

  const canvas = createChartContainer(canvasId);
  const ctx = canvas.getContext('2d');

  const progress = Math.min((data.predicted / data.target) * 100, 100);
  const remaining = 100 - progress;

  const chartData = {
    labels: ['Progress', 'Remaining'],
    datasets: [{
      data: [progress, remaining],
      backgroundColor: [
        progress >= 100 ? chartColors.success : chartColors.primary,
        chartColors.light
      ],
      borderColor: '#fff',
      borderWidth: 3,
      cutout: '70%'
    }]
  };

  const config = {
    type: 'doughnut',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Progress to Target Salary',
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              if (context.dataIndex === 0) {
                return `Progress: ${context.parsed.toFixed(1)}%`;
              }
              return `Remaining: ${context.parsed.toFixed(1)}%`;
            }
          }
        }
      }
    }
  };

  destroyChart(window[`chart_${canvasId}`]);
  window[`chart_${canvasId}`] = new Chart(ctx, config);
  return window[`chart_${canvasId}`];
};

// 6. Comparison Chart (Bar Chart)
export const createComparisonChart = (canvasId, userData, peerData) => {
  if (!Chart) return null;

  const canvas = createChartContainer(canvasId);
  const ctx = canvas.getContext('2d');

  const chartData = {
    labels: ['Your Salary', 'Peer Average', 'Market Median', '75th Percentile'],
    datasets: [{
      label: 'Salary Comparison',
      data: [
        userData.currentSalary || 75000,
        peerData.average || 82000,
        peerData.median || 78000,
        peerData.percentile75 || 95000
      ],
      backgroundColor: [
        chartColors.primary,
        chartColors.secondary,
        chartColors.accent,
        chartColors.warning
      ],
      borderColor: chartColors.dark,
      borderWidth: 1,
      borderRadius: 4
    }]
  };

  const config = {
    type: 'bar',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Salary Comparison',
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => `$${context.parsed.y.toLocaleString()}`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: 'Salary ($)'
          },
          ticks: {
            callback: (value) => `$${value.toLocaleString()}`
          }
        },
        x: {
          title: {
            display: true,
            text: 'Comparison Metrics'
          }
        }
      }
    }
  };

  destroyChart(window[`chart_${canvasId}`]);
  window[`chart_${canvasId}`] = new Chart(ctx, config);
  return window[`chart_${canvasId}`];
};

// 7. Demographic Analysis Chart (Multi-line Chart)
export const createDemographicChart = (canvasId, data) => {
  if (!Chart) return null;

  const canvas = createChartContainer(canvasId);
  const ctx = canvas.getContext('2d');

  const chartData = {
    labels: data.locations || ['Atlanta', 'Houston', 'DC', 'Dallas', 'NYC'],
    datasets: [
      {
        label: 'Overall Median',
        data: data.overall || [65000, 60000, 85000, 70000, 80000],
        borderColor: chartColors.primary,
        backgroundColor: 'transparent',
        borderWidth: 3,
        tension: 0.4
      },
      {
        label: 'African American Median',
        data: data.africanAmerican || [58000, 54000, 75000, 63000, 72000],
        borderColor: chartColors.secondary,
        backgroundColor: 'transparent',
        borderWidth: 3,
        tension: 0.4
      }
    ]
  };

  const config = {
    type: 'line',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Salary Comparison by Demographics',
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          position: 'top'
        },
        tooltip: {
          callbacks: {
            label: (context) => `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: 'Median Salary ($)'
          },
          ticks: {
            callback: (value) => `$${value.toLocaleString()}`
          }
        },
        x: {
          title: {
            display: true,
            text: 'Metro Areas'
          }
        }
      }
    }
  };

  destroyChart(window[`chart_${canvasId}`]);
  window[`chart_${canvasId}`] = new Chart(ctx, config);
  return window[`chart_${canvasId}`];
};

// 8. Economic Indicators Chart (Gauge-style)
export const createEconomicChart = (canvasId, data) => {
  if (!Chart) return null;

  const canvas = createChartContainer(canvasId);
  const ctx = canvas.getContext('2d');

  const indicators = [
    { name: 'Inflation', value: data.inflation || 2.5, max: 5 },
    { name: 'Unemployment', value: data.unemployment || 3.8, max: 10 },
    { name: 'GDP Growth', value: data.gdpGrowth || 2.1, max: 5 },
    { name: 'Wage Growth', value: data.wageGrowth || 3.2, max: 5 }
  ];

  const chartData = {
    labels: indicators.map(ind => ind.name),
    datasets: [{
      label: 'Economic Indicators',
      data: indicators.map(ind => (ind.value / ind.max) * 100),
      backgroundColor: indicators.map(ind => {
        const ratio = ind.value / ind.max;
        if (ratio < 0.3) return chartColors.success;
        if (ratio < 0.7) return chartColors.warning;
        return chartColors.danger;
      }),
      borderColor: chartColors.dark,
      borderWidth: 1,
      borderRadius: 4
    }]
  };

  const config = {
    type: 'bar',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Economic Health Indicators',
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const indicator = indicators[context.dataIndex];
              return `${indicator.name}: ${indicator.value}%`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: 'Percentage of Maximum'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Economic Indicators'
          }
        }
      }
    }
  };

  destroyChart(window[`chart_${canvasId}`]);
  window[`chart_${canvasId}`] = new Chart(ctx, config);
  return window[`chart_${canvasId}`];
};

// Export utility functions
export {
  destroyChart,
  updateChartData,
  createChartContainer,
  chartColors,
  gradientColors
};

// Export Chart.js if not already available globally
if (typeof Chart === 'undefined') {
  console.warn('Chart.js is not loaded. Please include Chart.js in your project.');
} 