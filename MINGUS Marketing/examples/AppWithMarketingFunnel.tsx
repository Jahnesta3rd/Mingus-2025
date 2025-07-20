import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { MarketingFunnelRoute } from '../src/components/MarketingFunnelRoute'

// Example main app components (replace with your actual components)
const HomePage = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">Your Main App</h1>
      <p className="text-gray-600 mb-8">Welcome to your existing application</p>
      <div className="space-x-4">
        <Link 
          to="/dashboard" 
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
        >
          Dashboard
        </Link>
        <Link 
          to="/marketing-funnel" 
          className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700"
        >
          Financial Assessment
        </Link>
      </div>
    </div>
  </div>
)

const Dashboard = () => (
  <div className="min-h-screen bg-gray-50 p-8">
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Your Dashboard Content</h2>
        <p className="text-gray-600 mb-4">
          This is your existing dashboard. You can add links to the marketing funnel here.
        </p>
        <Link 
          to="/marketing-funnel" 
          className="inline-block bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
        >
          Take Financial Assessment
        </Link>
      </div>
    </div>
  </div>
)

const Navigation = () => (
  <nav className="bg-white shadow-sm border-b">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between h-16">
        <div className="flex items-center">
          <Link to="/" className="text-xl font-bold text-gray-900">
            Your App
          </Link>
        </div>
        <div className="flex items-center space-x-4">
          <Link 
            to="/" 
            className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
          >
            Home
          </Link>
          <Link 
            to="/dashboard" 
            className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
          >
            Dashboard
          </Link>
          <Link 
            to="/marketing-funnel" 
            className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700"
          >
            Financial Assessment
          </Link>
        </div>
      </div>
    </div>
  </nav>
)

/**
 * Example App with Marketing Funnel Integration
 * 
 * This shows how to integrate the Ratchet Money marketing funnel
 * into an existing React application using React Router.
 * 
 * Key integration points:
 * 1. Marketing funnel is a separate route (/marketing-funnel)
 * 2. Navigation includes link to marketing funnel
 * 3. Marketing funnel is isolated from main app logic
 * 4. Shared database and environment variables
 */
function AppWithMarketingFunnel() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <Routes>
          {/* Your existing routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          
          {/* Marketing Funnel Routes */}
          <Route path="/marketing-funnel" element={<MarketingFunnelRoute />} />
          <Route path="/assessment" element={<MarketingFunnelRoute />} />
          <Route path="/ratchet-money" element={<MarketingFunnelRoute />} />
          
          {/* Optional: Direct access to specific funnel steps */}
          {/* 
          <Route path="/assessment/email" element={<EmailCollection />} />
          <Route path="/assessment/questions" element={<AssessmentForm />} />
          <Route path="/assessment/results" element={<AssessmentResults />} />
          */}
        </Routes>
      </div>
    </Router>
  )
}

export default AppWithMarketingFunnel 