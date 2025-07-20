import React, { useState, useEffect } from "react";
import HealthQuestionnaire from './HealthQuestionnaire';
import RelationshipQuestionnaire from './RelationshipQuestionnaire';
import CareerQuestionnaire from './CareerQuestionnaire';
import QuestionnaireProgress from './QuestionnaireProgress';
import QuestionnaireComplete from './QuestionnaireComplete';
import { submitHealthResponse } from '../api';
import { Controller } from 'react-hook-form';
import type { CareerFormData } from "../types/CareerQuestionnaire";
import WellnessFinanceInsightService from '../services/WellnessFinanceInsightService';
import requests
import schedule
import threading
import time
import smtplib
from email.mime.text import MIMEText
import os
import { useUserLifecycle } from '../hooks/useUserLifecycle';
import { useQuestionnaireSchedule } from '../hooks/useQuestionnaireSchedule';
import { useBehavioralPrompts } from '../hooks/useBehavioralPrompts';
import { useEngagementMetrics } from '../hooks/useEngagementMetrics';
import { QuestionnaireScheduleWidget } from "./QuestionnaireScheduleWidget";
import { UserLifecycleProgress } from "./UserLifecycleProgress";
import { BehavioralPromptModal } from "./BehavioralPromptModal";
import { Spinner } from "./Spinner";
import { BehavioralPrompt } from "../types/lifecycle";
import { UserLifecycleData } from "../types/lifecycle";
from email_service import EmailService
import datetime
from uuid import uuid4
from test_data import create_test_user, generate_responses

export type QuestionnaireType = 'health' | 'relationship' | 'career';

interface QuestionnaireFlowProps {
  user_id: string;
}

export const QuestionnaireFlow: React.FC<QuestionnaireFlowProps> = ({ user_id }) => {
  const { data: lifecycle, loading, error } = useUserLifecycle(user_id);
  const { prompt, loading: promptLoading } = useBehavioralPrompts(user_id);
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    if (prompt && !promptLoading) setShowPrompt(true);
  }, [prompt, promptLoading]);

  if (loading) return <Spinner />;
  if (error || !lifecycle) return <div className="text-red-600">Error loading questionnaire.</div>;

  // Choose questionnaire type
  let QuestionnaireComponent;
  switch (lifecycle.questionnaire_type) {
    case "quick_pulse":
      QuestionnaireComponent = HealthQuestionnaire;
      break;
    case "adaptive":
      QuestionnaireComponent = RelationshipQuestionnaire;
      break;
    case "weekly_with_pulse":
      QuestionnaireComponent = CareerQuestionnaire;
      break;
    default:
      QuestionnaireComponent = HealthQuestionnaire;
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <UserLifecycleProgress lifecycle={lifecycle} />
      <QuestionnaireScheduleWidget user_id={user_id} />
      <div className="my-6">
        <QuestionnaireComponent user_id={user_id} onComplete={() => setShowPrompt(true)} />
      </div>
      {showPrompt && prompt && (
        <BehavioralPromptModal prompt={prompt} onClose={() => setShowPrompt(false)} />
      )}
    </div>
  );
};

export default QuestionnaireFlow;

interface BehavioralPromptModalProps {
  prompt: BehavioralPrompt;
  onClose: () => void;
}

export const BehavioralPromptModal: React.FC<BehavioralPromptModalProps> = ({ prompt, onClose }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg max-w-md w-full p-6 relative">
      <button
        className="absolute top-2 right-2 text-gray-400 hover:text-gray-700"
        onClick={onClose}
        aria-label="Close"
      >
        ×
      </button>
      <h2 className="text-xl font-bold mb-2 text-blue-700 dark:text-blue-300">{prompt.quote}</h2>
      <div className="mb-2 text-gray-700 dark:text-gray-200">{prompt.reframe}</div>
      <div className="mb-4">
        <span className="font-semibold text-blue-600 dark:text-blue-400">{prompt.breathing.title}:</span>
        <ul className="list-disc ml-6 text-gray-600 dark:text-gray-300">
          {prompt.breathing.steps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ul>
      </div>
      <div className="mb-2 italic text-green-700 dark:text-green-400">{prompt.affirmation}</div>
      <div className="mb-4">
        <span className="font-semibold">Action:</span> {prompt.action}
      </div>
      <button
        className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none"
        onClick={onClose}
      >
        Got it!
      </button>
    </div>
  </div>
);

export const UserLifecycleProgress: React.FC<{ lifecycle: UserLifecycleData }> = ({ lifecycle }) => {
  const stageLabels = {
    week_1: "Onboarding (Daily Check-ins)",
    week_2_4: "Habit Building (3x/Week)",
    week_5_plus: "Maintenance (Weekly)"
  };
  return (
    <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900 rounded-lg flex flex-col items-center">
      <div className="text-lg font-bold text-blue-700 dark:text-blue-200">
        {stageLabels[lifecycle.current_stage]}
      </div>
      <div className="text-sm text-gray-700 dark:text-gray-300">
        {lifecycle.milestone || "Keep up the great work!"}
      </div>
      <div className="flex space-x-4 mt-2">
        <div>
          <span className="font-semibold">Next Due:</span>{" "}
          {lifecycle.next_due_dates && lifecycle.next_due_dates[0]}
        </div>
        <div>
          <span className="font-semibold">Streak:</span> {lifecycle.streak ?? 0}
        </div>
        <div>
          <span className="font-semibold">Engagement:</span> {lifecycle.engagement_score ?? 0}%
        </div>
      </div>
    </div>
  );
};

export const QuestionnaireScheduleWidget: React.FC<{ user_id: string }> = ({ user_id }) => {
  const { data, loading, error } = useQuestionnaireSchedule(user_id);

  if (loading) return <div>Loading schedule...</div>;
  if (error || !data) return <div className="text-red-600">Error loading schedule.</div>;

  return (
    <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div className="font-semibold mb-2">Upcoming Questionnaires</div>
      <ul>
        {data.upcoming.map((q, i) => (
          <li key={i} className="flex items-center justify-between py-1">
            <span>{q.date} ({q.type})</span>
            <span className={`text-xs px-2 py-1 rounded ${q.status === "pending" ? "bg-yellow-200" : "bg-green-200"}`}>
              {q.status}
            </span>
          </li>
        ))}
      </ul>
      {data.quick_pulse_available && (
        <button className="mt-2 w-full py-2 bg-blue-500 text-white rounded">
          Quick Pulse Check-In
        </button>
      )}
      {data.missed.length > 0 && (
        <div className="mt-2 text-red-600">
          Missed: {data.missed.map(m => m.date).join(", ")}
        </div>
      )}
    </div>
  );
};

def render_meme_reminder_template(meme_type, missed_days, name):
    meme_gifs = {
        "day_1": "https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif",
        "day_2": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
        "day_3_plus": "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif"
    }
    subject = {
        "day_1": "We See You! 👀 Your Wellness Check-In Awaits",
        "day_2": "We Miss You! 💌 Let's Reconnect",
        "day_3_plus": "This is Fine 😅 (But We'd Love to See You Back!)"
    }[meme_type]
    gif_url = meme_gifs[meme_type]
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f9f9f9; padding: 20px;">
        <div style="max-width: 480px; margin: auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 8px #0001; padding: 24px;">
            <img src="{gif_url}" alt="Meme" style="width:100%; border-radius: 8px; margin-bottom: 16px;">
            <div style="font-size: 1.1em; color: #222;">
                Hi {name},<br>
                Just a gentle nudge from your Mingus fam. We know life gets busy, but your well-being matters.<br>
                <b>Take 2 minutes for yourself today—you deserve it!</b>
            </div>
            <a href="{APP_URL}/questionnaire" style="display: inline-block; background: #007bff; color: #fff; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 18px;">
                Start My Check-In
            </a>
            <div style="margin-top: 24px; font-size: 0.9em; color: #888;">
                Your Mingus Community is cheering you on!
            </div>
        </div>
    </body>
    </html>
    """
    return subject, html

def render_behavioral_prompt_template(prompt_type, trigger_data, name):
    # Use your PROMPT_LIBRARY for content
    prompt = trigger_data
    subject = {
        "high_stress": "You Got This! Here's Support for Stressful Days",
        "financial_stress": "Money Moves: Support for Financial Stress",
        "job_insecurity": "Your Value Goes Beyond Your Job",
        "relationship_strain": "You're Not Alone: Relationship Support Inside",
        "low_energy": "Rest is Power: Take a Moment for You"
    }[prompt_type]
    breathing_steps = "".join(f"<li>{step}</li>" for step in prompt["breathing"]["steps"])
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f9f9f9; padding: 20px;">
        <div style="max-width: 480px; margin: auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 8px #0001; padding: 24px;">
            <h2 style="color: #007bff;">{prompt['quote']}</h2>
            <p>Hi {name},</p>
            <p>{prompt['reframe']}</p>
            <div style="margin: 18px 0; color: #007bff; font-weight: bold;">
                {prompt['affirmation']}
            </div>
            <h3>{prompt['breathing']['title']}</h3>
            <ul>{breathing_steps}</ul>
            <p><b>Action:</b> {prompt['action']}</p>
            <a href="{APP_URL}/resources" style="display: inline-block; background: #007bff; color: #fff; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                Explore More Support
            </a>
            <div style="margin-top: 24px; font-size: 0.9em; color: #888;">
                Your Mingus Community is here for you.
            </div>
        </div>
    </body>
    </html>
    """
    return subject, html 

# Use SendGrid in production, SMTP in dev
email_service = EmailService(use_sendgrid=bool(os.environ.get("USE_SENDGRID", False))) 

def create_test_users_at_all_stages(supabase):
    for stage, days in [("week_1", 0), ("week_2_4", 10), ("week_5_plus", 35)]:
        user = create_test_user(stage, reg_days_ago=days)
        supabase.table("user_profiles").insert(user).execute()

def simulate_questionnaire_completion_patterns(supabase, user_id):
    responses = generate_responses(user_id, 14, pattern="missed_some")
    for resp in responses:
        supabase.table("questionnaire_responses").insert(resp).execute()

def simulate_missed_questionnaire_scenarios(supabase, user_id):
    # Mark some as missed in questionnaire_schedules
    pass

def simulate_concerning_responses(supabase, user_id):
    responses = generate_responses(user_id, 7, pattern="concerning")
    for resp in responses:
        supabase.table("questionnaire_responses").insert(resp).execute()

def simulate_lifecycle_progression(supabase, user_id):
    # Advance user through stages by updating registration_date and responses
    pass 