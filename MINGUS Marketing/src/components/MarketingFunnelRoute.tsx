import React from 'react'
import { AssessmentWorkflow } from './AssessmentWorkflow'

/**
 * Marketing Funnel Route Component
 * 
 * This component can be easily integrated into an existing React app as a route.
 * It provides the complete Ratchet Money marketing funnel functionality.
 * 
 * Usage in your main app:
 * <Route path="/marketing-funnel" element={<MarketingFunnelRoute />} />
 * or
 * <Route path="/assessment" element={<MarketingFunnelRoute />} />
 */
export const MarketingFunnelRoute: React.FC = () => {
  return (
    <div className="marketing-funnel-route">
      <AssessmentWorkflow />
    </div>
  )
}

export default MarketingFunnelRoute 