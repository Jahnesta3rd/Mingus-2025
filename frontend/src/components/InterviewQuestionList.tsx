import React, { useState } from 'react';
import { Copy, X } from 'lucide-react';
import type { CompanyScreenQuestion } from '../types/companyScreen';

interface InterviewQuestionListProps {
  questions: CompanyScreenQuestion[];
  screenId: string;
  authToken: string;
}

type CopyFeedback = 'idle' | 'copied' | 'failed';

export default function InterviewQuestionList({
  questions,
  screenId,
  authToken,
}: InterviewQuestionListProps) {
  const [localQuestions, setLocalQuestions] = useState<CompanyScreenQuestion[]>(questions);
  const [copyFeedback, setCopyFeedback] = useState<Record<string, CopyFeedback>>({});
  const [dismissFailed, setDismissFailed] = useState<Record<string, boolean>>({});

  const visibleQuestions = localQuestions.filter((q) => q.dismissed_at == null);

  const handleCopy = async (question: CompanyScreenQuestion) => {
    try {
      const resp = await fetch(
        `/api/company-screen/questions/${question.id}/copy`,
        {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        },
      );
      if (!resp.ok) {
        setCopyFeedback((prev) => ({ ...prev, [question.id]: 'failed' }));
        window.setTimeout(
          () => setCopyFeedback((prev) => ({ ...prev, [question.id]: 'idle' })),
          2000,
        );
        return;
      }
      const copiedAt = new Date().toISOString();
      setLocalQuestions((prev) =>
        prev.map((q) =>
          q.id === question.id ? { ...q, copied_at: copiedAt } : q,
        ),
      );
      setCopyFeedback((prev) => ({ ...prev, [question.id]: 'copied' }));
      window.setTimeout(
        () => setCopyFeedback((prev) => ({ ...prev, [question.id]: 'idle' })),
        2000,
      );
    } catch {
      setCopyFeedback((prev) => ({ ...prev, [question.id]: 'failed' }));
      window.setTimeout(
        () => setCopyFeedback((prev) => ({ ...prev, [question.id]: 'idle' })),
        2000,
      );
    }
  };

  const handleDismiss = async (question: CompanyScreenQuestion) => {
    try {
      const resp = await fetch(
        `/api/company-screen/questions/${question.id}/dismiss`,
        {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        },
      );
      if (!resp.ok) {
        setDismissFailed((prev) => ({ ...prev, [question.id]: true }));
        window.setTimeout(
          () => setDismissFailed((prev) => ({ ...prev, [question.id]: false })),
          2000,
        );
        return;
      }
      setLocalQuestions((prev) => prev.filter((q) => q.id !== question.id));
    } catch {
      setDismissFailed((prev) => ({ ...prev, [question.id]: true }));
      window.setTimeout(
        () => setDismissFailed((prev) => ({ ...prev, [question.id]: false })),
        2000,
      );
    }
  };

  return (
    <div className="mt-6">
      <h3 className="text-base font-bold text-[#1E293B]">
        Questions to Ask in Your Interview
      </h3>
      <p className="mt-1 text-sm text-gray-500">
        Generated based on signals found in this screen.
      </p>

      {visibleQuestions.length === 0 ? (
        <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 px-4 py-6 text-center">
          <p className="text-sm text-[#1E293B]">All questions dismissed.</p>
          <p className="mt-1 text-sm text-gray-500">
            Re-run this screen to generate a fresh set.
          </p>
        </div>
      ) : (
        <ul className="mt-4 space-y-3">
          {visibleQuestions.map((question) => {
            const feedback = copyFeedback[question.id] ?? 'idle';
            const isCopied = question.copied_at != null;
            return (
              <li
                key={question.id}
                className="flex items-start justify-between gap-3 rounded-lg border border-gray-200 bg-white p-3"
              >
                <p className="flex-1 text-sm text-[#1E293B]">
                  <span className="mr-2 font-semibold text-gray-500">
                    {question.display_order + 1}.
                  </span>
                  {question.question_text}
                </p>
                <div className="flex shrink-0 items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleCopy(question)}
                    className={`rounded p-1.5 hover:bg-gray-100 ${
                      isCopied ? 'text-green-600' : 'text-gray-500'
                    }`}
                    aria-label="Copy question"
                    title={
                      feedback === 'copied'
                        ? 'Copied!'
                        : feedback === 'failed'
                          ? 'Failed'
                          : 'Copy'
                    }
                  >
                    {feedback === 'copied' ? (
                      <span className="text-xs font-medium">Copied!</span>
                    ) : feedback === 'failed' ? (
                      <span className="text-xs font-medium text-red-600">Failed</span>
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDismiss(question)}
                    className="rounded p-1.5 text-gray-500 hover:bg-gray-100"
                    aria-label="Dismiss question"
                    title={dismissFailed[question.id] ? 'Failed' : 'Dismiss'}
                  >
                    {dismissFailed[question.id] ? (
                      <span className="text-xs font-medium text-red-600">Failed</span>
                    ) : (
                      <X className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
