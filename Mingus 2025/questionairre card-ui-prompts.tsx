import { useState } from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

export default function FinancialWellnessCards() {
  const [currentCard, setCurrentCard] = useState(0);
  const [healthStatus, setHealthStatus] = useState(null);
  const [workoutStatus, setWorkoutStatus] = useState(null);
  const [workChallenges, setWorkChallenges] = useState(3);
  const [relationshipIssues, setRelationshipIssues] = useState(null);
  const [relationshipSeverity, setRelationshipSeverity] = useState(3);
  const [showRelationshipSeverity, setShowRelationshipSeverity] = useState(false);

  const handleNext = () => {
    if (currentCard < 3) {
      setCurrentCard(currentCard + 1);
    }
  };

  const handlePrev = () => {
    if (currentCard > 0) {
      setCurrentCard(currentCard - 1);
    }
  };

  const handleHealthSelect = (status) => {
    setHealthStatus(status);
  };

  const handleWorkoutSelect = (status) => {
    setWorkoutStatus(status);
  };

  const handleWorkChallengesChange = (e) => {
    setWorkChallenges(parseInt(e.target.value));
  };

  const handleRelationshipSelect = (hasIssues) => {
    setRelationshipIssues(hasIssues);
    setShowRelationshipSeverity(hasIssues === false);
  };

  const handleRelationshipSeverityChange = (e) => {
    setRelationshipSeverity(parseInt(e.target.value));
  };

  const cards = [
    // Health Card
    <div key="health" className="bg-white rounded-lg shadow-lg p-6 max-w-md mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">Physical Health</div>
        <div className="text-gray-400 text-sm">1 of 4</div>
      </div>
      
      <h2 className="text-2xl font-bold text-gray-800 mb-6">How has your health been this week?</h2>
      
      <div className="space-y-3 mb-8">
        <button 
          className={`w-full py-3 px-4 rounded-lg border-2 ${healthStatus === 'healthy' ? 'bg-blue-50 border-blue-500' : 'border-gray-200 hover:bg-gray-50'}`}
          onClick={() => handleHealthSelect('healthy')}
        >
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
              <span className="text-green-500 text-lg">✓</span>
            </div>
            <span className="font-medium">Generally Healthy</span>
          </div>
        </button>
        
        <button 
          className={`w-full py-3 px-4 rounded-lg border-2 ${healthStatus === 'chronic' ? 'bg-blue-50 border-blue-500' : 'border-gray-200 hover:bg-gray-50'}`}
          onClick={() => handleHealthSelect('chronic')}
        >
          <div className="flex items-center">
            <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
              <span className="text-yellow-500 text-lg">⟳</span>
            </div>
            <span className="font-medium">Managing Chronic Condition</span>
          </div>
        </button>
        
        <button 
          className={`w-full py-3 px-4 rounded-lg border-2 ${healthStatus === 'recovering' ? 'bg-blue-50 border-blue-500' : 'border-gray-200 hover:bg-gray-50'}`}
          onClick={() => handleHealthSelect('recovering')}
        >
          <div className="flex items-center">
            <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center mr-3">
              <span className="text-red-500 text-lg">+</span>
            </div>
            <span className="font-medium">Recovering from an Injury</span>
          </div>
        </button>
      </div>
      
      <div className="bg-blue-50 p-4 rounded-lg text-sm text-blue-800 mb-6">
        <p><span className="font-medium">Why this matters:</span> Your physical health can impact medical expenses, work productivity, and energy for financial planning. Health changes often come with unexpected costs or income changes.</p>
      </div>
      
      <div className="flex justify-end">
        <button 
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
          onClick={handleNext}
          disabled={healthStatus === null}
        >
          Next
        </button>
      </div>
    </div>,
    
    // Workout Card
    <div key="workout" className="bg-white rounded-lg shadow-lg p-6 max-w-md mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded">Exercise Habits</div>
        <div className="text-gray-400 text-sm">2 of 4</div>
      </div>
      
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Were you on your workout grind this week?</h2>
      
      <div className="space-y-3 mb-8">
        <button 
          className={`w-full py-3 px-4 rounded-lg border-2 ${workoutStatus === 'never' ? 'bg-green-50 border-green-500' : 'border-gray-200 hover:bg-gray-50'}`}
          onClick={() => handleWorkoutSelect('never')}
        >
          <span className="font-medium">Never</span>
        </button>
        
        <button 
          className={`w-full py-3 px-4 rounded-lg border-2 ${workoutStatus === 'one' ? 'bg-green-50 border-green-500' : 'border-gray-200 hover:bg-gray-50'}`}
          onClick={() => handleWorkoutSelect('one')}
        >
          <span className="font-medium">I got one in</span>
        </button>
        
        <button 
          className={`w-full py-3 px-4 rounded-lg border-2 ${workoutStatus === 'three' ? 'bg-green-50 border-green-500' : 'border-gray-200 hover:bg-gray-50'}`}
          onClick={() => handleWorkoutSelect('three')}
        >
          <span className="font-medium">I did my 3 days</span>
        </button>
        
        <button 
          className={`w-full py-3 px-4 rounded-lg border-2 ${workoutStatus === 'hard' ? 'bg-green-50 border-green-500' : 'border-gray-200 hover:bg-gray-50'}`}
          onClick={() => handleWorkoutSelect('hard')}
        >
          <span className="font-medium">I hit it hard</span>
        </button>
      </div>
      
      <div className="bg-green-50 p-4 rounded-lg text-sm text-green-800 mb-6">
        <p><span className="font-medium">Why this matters:</span> Your exercise habits can reveal spending patterns on gym memberships, equipment, or health foods. Regular exercise is also linked to better financial discipline and reduced healthcare costs.</p>
      </div>
      
      <div className="flex justify-between">
        <button 
          className="px-6 py-2 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300"
          onClick={handlePrev}
        >
          Back
        </button>
        <button 
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
          onClick={handleNext}
          disabled={workoutStatus === null}
        >
          Next
        </button>
      </div>
    </div>,
    
    // Work Challenges Card
    <div key="work" className="bg-white rounded-lg shadow-lg p-6 max-w-md mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="bg-purple-100 text-purple-800 text-xs font-medium px-2.5 py-0.5 rounded">Career</div>
        <div className="text-gray-400 text-sm">3 of 4</div>
      </div>
      
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Did you run into problems at work this week?</h2>
      
      <div className="mb-8">
        <div className="mb-2 flex justify-between text-sm text-gray-600">
          <span>No challenges</span>
          <span>Significant challenges</span>
        </div>
        <input 
          type="range" 
          min="1" 
          max="5" 
          value={workChallenges} 
          onChange={handleWorkChallengesChange}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
        />
        <div className="flex justify-between mt-1">
          <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
          <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
          <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
          <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
          <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
        </div>
      </div>
      
      <div className="bg-purple-50 p-4 rounded-lg text-sm text-purple-800 mb-6">
        <p><span className="font-medium">Why this matters:</span> Work challenges often correlate with changes in income, spending patterns, and financial stress. Career stability is a key factor in your long-term financial goals and budget adherence.</p>
      </div>
      
      <div className="flex justify-between">
        <button 
          className="px-6 py-2 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300"
          onClick={handlePrev}
        >
          Back
        </button>
        <button 
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
          onClick={handleNext}
        >
          Next
        </button>
      </div>
    </div>,
    
    // Relationship Card
    <div key="relationship" className="bg-white rounded-lg shadow-lg p-6 max-w-md mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="bg-pink-100 text-pink-800 text-xs font-medium px-2.5 py-0.5 rounded">Relationships</div>
        <div className="text-gray-400 text-sm">4 of 4</div>
      </div>
      
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Are you having relationship issues right now?</h2>
      
      {!showRelationshipSeverity ? (
        <div className="flex justify-center space-x-12 mb-8">
          <button
            className={`flex flex-col items-center ${relationshipIssues === true ? 'text-red-500' : 'text-gray-400 hover:text-gray-600'}`}
            onClick={() => handleRelationshipSelect(true)}
          >
            <ThumbsDown size={48} />
            <span className="mt-2 font-medium">Yes</span>
          </button>
          
          <button
            className={`flex flex-col items-center ${relationshipIssues === false ? 'text-green-500' : 'text-gray-400 hover:text-gray-600'}`}
            onClick={() => handleRelationshipSelect(false)}
          >
            <ThumbsUp size={48} />
            <span className="mt-2 font-medium">No</span>
          </button>
        </div>
      ) : (
        <div className="mb-8">
          <p className="mb-4 text-gray-700">How would you rate the severity?</p>
          <div className="mb-2 flex justify-between text-sm text-gray-600">
            <span>It'll blow over</span>
            <span>It's a wrap</span>
          </div>
          <input 
            type="range" 
            min="1" 
            max="5" 
            value={relationshipSeverity} 
            onChange={handleRelationshipSeverityChange}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-pink-600"
          />
          <div className="flex justify-between mt-1">
            <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
            <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
            <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
            <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
            <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
          </div>
        </div>
      )}
      
      <div className="bg-pink-50 p-4 rounded-lg text-sm text-pink-800 mb-6">
        <p><span className="font-medium">Why this matters:</span> Relationship changes often impact shared expenses, living situations, and emotional spending. Relationship stress can lead to impulse purchases or neglect of financial planning.</p>
      </div>
      
      <div className="flex justify-between">
        <button 
          className="px-6 py-2 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300"
          onClick={handlePrev}
        >
          Back
        </button>
        <button 
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
          onClick={() => alert("Assessment complete!")}
          disabled={relationshipIssues === null || (relationshipIssues === false && !showRelationshipSeverity)}
        >
          Submit
        </button>
      </div>
    </div>
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-6">
          <div className="relative pt-1">
            <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-200">
              <div style={{ width: `${(currentCard + 1) * 25}%` }} className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500"></div>
            </div>
          </div>
        </div>
        
        {cards[currentCard]}
      </div>
    </div>
  );
}