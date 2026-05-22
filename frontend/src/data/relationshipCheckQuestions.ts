import { VIBE_CHECKUPS_QUESTIONS } from '../components/vibe-checkups/vibeCheckupsQuestions';

export type RelationshipCheckQuestionAxis = 'emotional' | 'financial';

export interface RelationshipCheckQuestion {
  id: string;
  axis: RelationshipCheckQuestionAxis;
  prompt: string;
  answers: [string, string, string, string];
}

export const RELATIONSHIP_CHECK_QUESTIONS: RelationshipCheckQuestion[] = [
  {
    id: 'emotional_availability',
    axis: 'emotional',
    prompt: VIBE_CHECKUPS_QUESTIONS[0].hint,
    answers: ['Rarely', 'Sometimes', 'Often', 'Almost always'],
  },
  {
    id: 'conflict_style',
    axis: 'emotional',
    prompt: VIBE_CHECKUPS_QUESTIONS[1].hint,
    answers: ['Avoid or blow up', 'Uneven', 'Mostly workable', 'Consistently kind'],
  },
  {
    id: 'shared_values',
    axis: 'emotional',
    prompt: VIBE_CHECKUPS_QUESTIONS[2].hint,
    answers: ['Mostly unclear', 'Some overlap', 'Mostly aligned', 'Very aligned'],
  },
  {
    id: 'income_transparency',
    axis: 'financial',
    prompt: VIBE_CHECKUPS_QUESTIONS[11].hint,
    answers: ['Hidden', 'Minimal', 'Mostly open', 'Fully transparent'],
  },
  {
    id: 'wiggle_room',
    axis: 'financial',
    prompt: 'How do you feel about the amount of wiggle room in your monthly spending?',
    answers: ['Tight, no room', 'Some pressure', 'Comfortable', 'Lots of room'],
  },
];
