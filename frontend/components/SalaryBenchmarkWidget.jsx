import React, { useState, useEffect } from 'react';
import { useSalaryPredictions } from '../hooks/useSalaryPredictions';
import { createSalaryChart } from '../utils/chartUtils';

const SalaryBenchmarkWidget = ({ userData, onDataUpdate }) => {
  const [filters, setFilters] = useState({
    location: userData?.location || '',
    industry: userData?.industry || '',
    experience: userData?.experience || '',
    education: userData?.education || ''
  });

  const [benchmarkData, setBenchmarkData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [chartInstance, setChartInstance] = useState(null);

  const { getSalaryPredictions, loading, error } = useSalaryPredictions();

  useEffect(() => {
    if (userData?.currentSalary) {
      fetchBenchmarkData();
    }
  }, [filters, userData]);

  useEffect(() => {
    if (benchmarkData) {
      renderChart();
    }
  }, [benchmarkData]);

  const fetchBenchmarkData = async () => {
    setIsLoading(true);
    try {
      const predictions = await getSalaryPredictions({
        currentSalary: userData.currentSalary,
        ...filters
      });
      
      setBenchmarkData(predictions);
      onDataUpdate?.(predictions);
    } catch (err) {
      console.error('Failed to fetch benchmark data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const renderChart = () => {
    if (chartInstance) {
      chartInstance.destroy();
    }

    const chart = createSalaryChart('salary-chart', benchmarkData);
    setChartInstance(chart);
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const getPercentile = () => {
    if (!benchmarkData) return null;
    
    const { userSalary, peerData } = benchmarkData;
    const sortedSalaries = peerData.map(p => p.salary).sort((a, b) => a - b);
    const userIndex = sortedSalaries.findIndex(salary => salary >= userSalary);
    
    return Math.round(((userIndex + 1) / sortedSalaries.length) * 100);
  };

  const getSalaryGap = () => {
    if (!benchmarkData) return null;
    
    const { userSalary, peerAverage } = benchmarkData;
    const gap = peerAverage - userSalary;
    const percentage = (gap / userSalary) * 100;
    
    return {
      amount: gap,
      percentage: percentage,
      isAbove: gap > 0
    };
  };

  if (loading || isLoading) {
    return (
      <div className="salary-benchmark-widget loading">
        <div className="loading-spinner"></div>
        <p>Analyzing salary data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="salary-benchmark-widget error">
        <p>Unable to load salary data. Please try again.</p>
        <button onClick={fetchBenchmarkData}>Retry</button>
      </div>
    );
  }

  if (!benchmarkData) {
    return (
      <div className="salary-benchmark-widget empty">
        <p>Enter your salary information to see benchmarks</p>
      </div>
    );
  }

  const percentile = getPercentile();
  const salaryGap = getSalaryGap();

  return (
    <div className="salary-benchmark-widget">
      <div className="widget-header">
        <h3>Salary Benchmark Analysis</h3>
        <div className="filters">
          <select
            value={filters.location}
            onChange={(e) => handleFilterChange('location', e.target.value)}
          >
            <option value="">All Locations</option>
            <option value="atlanta">Atlanta, GA</option>
            <option value="washington-dc">Washington, DC</option>
            <option value="new-york">New York, NY</option>
            <option value="los-angeles">Los Angeles, CA</option>
            <option value="chicago">Chicago, IL</option>
            <option value="houston">Houston, TX</option>
            <option value="phoenix">Phoenix, AZ</option>
            <option value="philadelphia">Philadelphia, PA</option>
            <option value="san-antonio">San Antonio, TX</option>
            <option value="san-diego">San Diego, CA</option>
            <option value="dallas">Dallas, TX</option>
            <option value="san-jose">San Jose, CA</option>
            <option value="austin">Austin, TX</option>
            <option value="jacksonville">Jacksonville, FL</option>
            <option value="fort-worth">Fort Worth, TX</option>
            <option value="columbus">Columbus, OH</option>
            <option value="charlotte">Charlotte, NC</option>
            <option value="san-francisco">San Francisco, CA</option>
            <option value="indianapolis">Indianapolis, IN</option>
            <option value="seattle">Seattle, WA</option>
            <option value="denver">Denver, CO</option>
            <option value="boston">Boston, MA</option>
            <option value="el-paso">El Paso, TX</option>
            <option value="detroit">Detroit, MI</option>
            <option value="nashville">Nashville, TN</option>
            <option value="portland">Portland, OR</option>
            <option value="memphis">Memphis, TN</option>
            <option value="oklahoma-city">Oklahoma City, OK</option>
            <option value="las-vegas">Las Vegas, NV</option>
            <option value="louisville">Louisville, KY</option>
            <option value="baltimore">Baltimore, MD</option>
            <option value="milwaukee">Milwaukee, WI</option>
            <option value="albuquerque">Albuquerque, NM</option>
            <option value="tucson">Tucson, AZ</option>
            <option value="fresno">Fresno, CA</option>
            <option value="sacramento">Sacramento, CA</option>
            <option value="mesa">Mesa, AZ</option>
            <option value="kansas-city">Kansas City, MO</option>
            <option value="long-beach">Long Beach, CA</option>
            <option value="colorado-springs">Colorado Springs, CO</option>
            <option value="raleigh">Raleigh, NC</option>
            <option value="miami">Miami, FL</option>
            <option value="virginia-beach">Virginia Beach, VA</option>
            <option value="omaha">Omaha, NE</option>
            <option value="oakland">Oakland, CA</option>
            <option value="minneapolis">Minneapolis, MN</option>
            <option value="tulsa">Tulsa, OK</option>
            <option value="arlington">Arlington, TX</option>
            <option value="tampa">Tampa, FL</option>
            <option value="new-orleans">New Orleans, LA</option>
            <option value="wichita">Wichita, KS</option>
            <option value="cleveland">Cleveland, OH</option>
            <option value="bakersfield">Bakersfield, CA</option>
            <option value="aurora">Aurora, CO</option>
            <option value="anaheim">Anaheim, CA</option>
            <option value="honolulu">Honolulu, HI</option>
            <option value="santa-ana">Santa Ana, CA</option>
            <option value="corpus-christi">Corpus Christi, TX</option>
            <option value="riverside">Riverside, CA</option>
            <option value="lexington">Lexington, KY</option>
            <option value="stockton">Stockton, CA</option>
            <option value="henderson">Henderson, NV</option>
            <option value="saint-paul">Saint Paul, MN</option>
            <option value="st-louis">St. Louis, MO</option>
            <option value="cincinnati">Cincinnati, OH</option>
            <option value="pittsburgh">Pittsburgh, PA</option>
            <option value="greensboro">Greensboro, NC</option>
            <option value="anchorage">Anchorage, AK</option>
            <option value="plano">Plano, TX</option>
            <option value="lincoln">Lincoln, NE</option>
            <option value="orlando">Orlando, FL</option>
            <option value="irvine">Irvine, CA</option>
            <option value="newark">Newark, NJ</option>
            <option value="durham">Durham, NC</option>
            <option value="chula-vista">Chula Vista, CA</option>
            <option value="toledo">Toledo, OH</option>
            <option value="fort-wayne">Fort Wayne, IN</option>
            <option value="st-petersburg">St. Petersburg, FL</option>
            <option value="laredo">Laredo, TX</option>
            <option value="jersey-city">Jersey City, NJ</option>
            <option value="chandler">Chandler, AZ</option>
            <option value="madison">Madison, WI</option>
            <option value="lubbock">Lubbock, TX</option>
            <option value="scottsdale">Scottsdale, AZ</option>
            <option value="reno">Reno, NV</option>
            <option value="buffalo">Buffalo, NY</option>
            <option value="gilbert">Gilbert, AZ</option>
            <option value="glendale">Glendale, AZ</option>
            <option value="north-las-vegas">North Las Vegas, NV</option>
            <option value="winston-salem">Winston-Salem, NC</option>
            <option value="chesapeake">Chesapeake, VA</option>
            <option value="norfolk">Norfolk, VA</option>
            <option value="fremont">Fremont, CA</option>
            <option value="garland">Garland, TX</option>
            <option value="irving">Irving, TX</option>
            <option value="hialeah">Hialeah, FL</option>
            <option value="richmond">Richmond, VA</option>
            <option value="boise">Boise, ID</option>
            <option value="spokane">Spokane, WA</option>
            <option value="baton-rouge">Baton Rouge, LA</option>
            <option value="tacoma">Tacoma, WA</option>
            <option value="san-bernardino">San Bernardino, CA</option>
            <option value="grand-rapids">Grand Rapids, MI</option>
            <option value="huntsville">Huntsville, AL</option>
            <option value="salt-lake-city">Salt Lake City, UT</option>
            <option value="frisco">Frisco, TX</option>
            <option value="cary">Cary, NC</option>
            <option value="yonkers">Yonkers, NY</option>
            <option value="amarillo">Amarillo, TX</option>
            <option value="santa-clarita">Santa Clarita, CA</option>
            <option value="glendale-ca">Glendale, CA</option>
            <option value="mobile">Mobile, AL</option>
            <option value="grand-prairie">Grand Prairie, TX</option>
            <option value="overland-park">Overland Park, KS</option>
            <option value="cape-coral">Cape Coral, FL</option>
            <option value="des-moines">Des Moines, IA</option>
            <option value="mckinney">McKinney, TX</option>
            <option value="modesto">Modesto, CA</option>
            <option value="fayetteville">Fayetteville, NC</option>
            <option value="tacoma-wa">Tacoma, WA</option>
            <option value="oxnard">Oxnard, CA</option>
            <option value="fontana">Fontana, CA</option>
            <option value="columbus-ga">Columbus, GA</option>
            <option value="montgomery">Montgomery, AL</option>
            <option value="moreno-valley">Moreno Valley, CA</option>
            <option value="shreveport">Shreveport, LA</option>
            <option value="aurora-il">Aurora, IL</option>
            <option value="yonkers-ny">Yonkers, NY</option>
            <option value="akron">Akron, OH</option>
            <option value="huntington-beach">Huntington Beach, CA</option>
            <option value="little-rock">Little Rock, AR</option>
            <option value="augusta">Augusta, GA</option>
            <option value="amarillo-tx">Amarillo, TX</option>
            <option value="glendale-az">Glendale, AZ</option>
            <option value="grand-rapids-mi">Grand Rapids, MI</option>
            <option value="tallahassee">Tallahassee, FL</option>
            <option value="huntsville-al">Huntsville, AL</option>
            <option value="grand-prairie-tx">Grand Prairie, TX</option>
            <option value="overland-park-ks">Overland Park, KS</option>
            <option value="cape-coral-fl">Cape Coral, FL</option>
            <option value="tempe">Tempe, AZ</option>
            <option value="mckinney-tx">McKinney, TX</option>
            <option value="mobile-al">Mobile, AL</option>
            <option value="cary-nc">Cary, NC</option>
            <option value="shreveport-la">Shreveport, LA</option>
            <option value="frisco-tx">Frisco, TX</option>
            <option value="rochester">Rochester, NY</option>
            <option value="winston-salem-nc">Winston-Salem, NC</option>
            <option value="santa-clarita-ca">Santa Clarita, CA</option>
            <option value="fayetteville-nc">Fayetteville, NC</option>
            <option value="anchorage-ak">Anchorage, AK</option>
            <option value="knoxville">Knoxville, TN</option>
            <option value="aurora-il-2">Aurora, IL</option>
            <option value="bakersfield-ca">Bakersfield, CA</option>
            <option value="new-orleans-la">New Orleans, LA</option>
            <option value="cleveland-oh">Cleveland, OH</option>
            <option value="tampa-fl">Tampa, FL</option>
            <option value="tulsa-ok">Tulsa, OK</option>
            <option value="arlington-tx">Arlington, TX</option>
            <option value="wichita-ks">Wichita, KS</option>
            <option value="minneapolis-mn">Minneapolis, MN</option>
            <option value="oakland-ca">Oakland, CA</option>
            <option value="omaha-ne">Omaha, NE</option>
            <option value="virginia-beach-va">Virginia Beach, VA</option>
            <option value="miami-fl">Miami, FL</option>
            <option value="raleigh-nc">Raleigh, NC</option>
            <option value="colorado-springs-co">Colorado Springs, CO</option>
            <option value="long-beach-ca">Long Beach, CA</option>
            <option value="kansas-city-mo">Kansas City, MO</option>
            <option value="mesa-az">Mesa, AZ</option>
            <option value="sacramento-ca">Sacramento, CA</option>
            <option value="fresno-ca">Fresno, CA</option>
            <option value="tucson-az">Tucson, AZ</option>
            <option value="albuquerque-nm">Albuquerque, NM</option>
            <option value="milwaukee-wi">Milwaukee, WI</option>
            <option value="baltimore-md">Baltimore, MD</option>
            <option value="louisville-ky">Louisville, KY</option>
            <option value="las-vegas-nv">Las Vegas, NV</option>
            <option value="oklahoma-city-ok">Oklahoma City, OK</option>
            <option value="memphis-tn">Memphis, TN</option>
            <option value="portland-or">Portland, OR</option>
            <option value="nashville-tn">Nashville, TN</option>
            <option value="detroit-mi">Detroit, MI</option>
            <option value="el-paso-tx">El Paso, TX</option>
            <option value="boston-ma">Boston, MA</option>
            <option value="seattle-wa">Seattle, WA</option>
            <option value="indianapolis-in">Indianapolis, IN</option>
            <option value="san-francisco-ca">San Francisco, CA</option>
            <option value="charlotte-nc">Charlotte, NC</option>
            <option value="columbus-oh">Columbus, OH</option>
            <option value="fort-worth-tx">Fort Worth, TX</option>
            <option value="jacksonville-fl">Jacksonville, FL</option>
            <option value="austin-tx">Austin, TX</option>
            <option value="san-jose-ca">San Jose, CA</option>
            <option value="dallas-tx">Dallas, TX</option>
            <option value="san-diego-ca">San Diego, CA</option>
            <option value="san-antonio-tx">San Antonio, TX</option>
            <option value="philadelphia-pa">Philadelphia, PA</option>
            <option value="phoenix-az">Phoenix, AZ</option>
            <option value="houston-tx">Houston, TX</option>
            <option value="chicago-il">Chicago, IL</option>
            <option value="los-angeles-ca">Los Angeles, CA</option>
            <option value="new-york-ny">New York, NY</option>
            <option value="washington-dc">Washington, DC</option>
            <option value="remote">Remote</option>
            <option value="other">Other</option>
          </select>

          <select
            value={filters.industry}
            onChange={(e) => handleFilterChange('industry', e.target.value)}
          >
            <option value="">All Industries</option>
            <option value="technology">Technology</option>
            <option value="healthcare">Healthcare</option>
            <option value="finance">Finance</option>
            <option value="education">Education</option>
            <option value="government">Government</option>
            <option value="non-profit">Non-Profit</option>
            <option value="manufacturing">Manufacturing</option>
            <option value="retail">Retail</option>
            <option value="consulting">Consulting</option>
            <option value="marketing">Marketing</option>
            <option value="legal">Legal</option>
            <option value="real-estate">Real Estate</option>
            <option value="media">Media</option>
            <option value="other">Other</option>
          </select>

          <select
            value={filters.experience}
            onChange={(e) => handleFilterChange('experience', e.target.value)}
          >
            <option value="">All Experience Levels</option>
            <option value="entry">Entry Level (0-2 years)</option>
            <option value="mid">Mid Level (3-7 years)</option>
            <option value="senior">Senior Level (8-15 years)</option>
            <option value="executive">Executive (15+ years)</option>
          </select>

          <select
            value={filters.education}
            onChange={(e) => handleFilterChange('education', e.target.value)}
          >
            <option value="">All Education Levels</option>
            <option value="high-school">High School</option>
            <option value="associate">Associate's Degree</option>
            <option value="bachelor">Bachelor's Degree</option>
            <option value="master">Master's Degree</option>
            <option value="doctorate">Doctorate</option>
            <option value="certification">Professional Certification</option>
          </select>
        </div>
      </div>

      <div className="widget-content">
        <div className="summary-stats">
          <div className="stat-card">
            <h4>Your Salary</h4>
            <div className="stat-value">${userData.currentSalary.toLocaleString()}</div>
            <div className="stat-label">{percentile}th percentile</div>
          </div>

          <div className="stat-card">
            <h4>Peer Average</h4>
            <div className="stat-value">${benchmarkData.peerAverage.toLocaleString()}</div>
            <div className="stat-label">Based on {benchmarkData.sampleSize} professionals</div>
          </div>

          {salaryGap && (
            <div className={`stat-card ${salaryGap.isAbove ? 'positive' : 'negative'}`}>
              <h4>Salary Gap</h4>
              <div className="stat-value">
                {salaryGap.isAbove ? '+' : ''}${Math.abs(salaryGap.amount).toLocaleString()}
              </div>
              <div className="stat-label">
                {salaryGap.isAbove ? 'Above' : 'Below'} average by {Math.abs(salaryGap.percentage).toFixed(1)}%
              </div>
            </div>
          )}
        </div>

        <div className="chart-container">
          <canvas id="salary-chart"></canvas>
        </div>

        <div className="confidence-interval">
          <h4>Confidence Interval</h4>
          <p>
            Based on our analysis, your salary falls within the range of{' '}
            <strong>${benchmarkData.confidenceInterval.lower.toLocaleString()}</strong> to{' '}
            <strong>${benchmarkData.confidenceInterval.upper.toLocaleString()}</strong>{' '}
            for professionals with similar backgrounds in your area.
          </p>
        </div>

        <div className="insights">
          <h4>Key Insights</h4>
          <ul>
            <li>
              <strong>Market Position:</strong> You are in the {percentile}th percentile of earners in your field.
            </li>
            <li>
              <strong>Growth Potential:</strong> Based on your experience and education, you could potentially earn{' '}
              ${(benchmarkData.peer75thPercentile - userData.currentSalary).toLocaleString()} more annually.
            </li>
            <li>
              <strong>Regional Factors:</strong> Your location {salaryGap?.isAbove ? 'provides' : 'may limit'} salary opportunities.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default SalaryBenchmarkWidget; 