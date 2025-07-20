import React, { useState } from 'react'
import { EmailCollection } from './EmailCollection'
import { AssessmentForm } from './AssessmentForm'
import { AssessmentResults } from './AssessmentResults'

type WorkflowStep = 'email' | 'assessment' | 'results'

interface AssessmentWorkflowProps {
  // Props for customization
}

export const AssessmentWorkflow: React.FC<AssessmentWorkflowProps> = () => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('email')
  const [userEmail, setUserEmail] = useState('')
  const [assessmentData, setAssessmentData] = useState<any>(null)

  const handleEmailSubmitted = (email: string) => {
    setUserEmail(email)
    setCurrentStep('assessment')
  }

  const handleAssessmentCompleted = (data: any) => {
    setAssessmentData(data)
    setCurrentStep('results')
  }

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'email':
        return <EmailCollection onEmailSubmitted={handleEmailSubmitted} />
      case 'assessment':
        return <AssessmentForm onCompleted={handleAssessmentCompleted} />
      case 'results':
        return <AssessmentResults data={assessmentData} email={userEmail} />
      default:
        return <EmailCollection onEmailSubmitted={handleEmailSubmitted} />
    }
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {renderCurrentStep()}
    </div>
  )
} 