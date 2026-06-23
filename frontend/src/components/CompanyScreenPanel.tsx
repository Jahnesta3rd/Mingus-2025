import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import InterviewQuestionList from './InterviewQuestionList';
import type {
  CompanyScreen,
  CompositeBand,
  Layer3Band,
} from '../types/companyScreen';

interface CompanyScreenPanelProps {
  screen: CompanyScreen;
  authToken: string;
  onRescreen?: () => void;
}

function formatScreenDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
}

function compositeBandClasses(band: CompositeBand): string {
  switch (band) {
    case 'strong':
      return 'bg-green-100 text-green-800';
    case 'mixed':
      return 'bg-yellow-100 text-yellow-800';
    case 'caution':
      return 'bg-orange-100 text-orange-800';
    case 'high_risk':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-500';
  }
}

function compositeScoreColor(band: CompositeBand): string {
  switch (band) {
    case 'strong':
      return 'text-green-800';
    case 'mixed':
      return 'text-yellow-800';
    case 'caution':
      return 'text-orange-800';
    case 'high_risk':
      return 'text-red-800';
    default:
      return 'text-gray-400';
  }
}

function layerScoreColor(score: number | null): string {
  if (score == null) return 'text-gray-400';
  if (score >= 65) return 'text-green-700';
  if (score >= 40) return 'text-yellow-700';
  return 'text-red-700';
}

function layer3BandClasses(band: Layer3Band): string {
  switch (band) {
    case 'positive':
      return 'bg-green-100 text-green-700';
    case 'mixed':
      return 'bg-yellow-100 text-yellow-700';
    case 'negative':
      return 'bg-red-100 text-red-700';
    default:
      return 'bg-gray-100 text-gray-500';
  }
}

function confidenceLabel(confidence: CompanyScreen['layer3_detail']['confidence']): string {
  switch (confidence) {
    case 'high':
      return '(High confidence)';
    case 'medium':
      return '(Medium)';
    case 'low':
      return '(Low)';
    default:
      return '';
  }
}

function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1)}…`;
}

export default function CompanyScreenPanel({
  screen,
  authToken,
  onRescreen,
}: CompanyScreenPanelProps) {
  const [threadsOpen, setThreadsOpen] = useState(false);
  const jargonPhrases = screen.layer2_detail?.top_jargon_phrases ?? [];
  const sampleThreads = screen.layer3_detail?.sample_threads ?? [];

  const bandLabel =
    screen.composite_band != null
      ? screen.composite_band.replace('_', ' ')
      : 'Analyzing...';

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-[#1E293B]">{screen.employer_name}</h2>
          <p className="mt-1 text-sm text-gray-500">
            Screened {formatScreenDate(screen.created_at)}
          </p>
        </div>
        <div className="text-right">
          <span
            className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize ${compositeBandClasses(
              screen.composite_band,
            )}`}
          >
            {bandLabel}
          </span>
          <p
            className={`mt-2 text-3xl font-bold tabular-nums ${compositeScoreColor(
              screen.composite_band,
            )}`}
          >
            {screen.composite_score != null ? screen.composite_score : '—'}
          </p>
        </div>
      </div>

      {screen.layoff_event_detected ? (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3">
          <p className="text-sm font-semibold text-red-800">
            ⚠️ Active layoff filing detected
          </p>
          <p className="mt-1 text-sm text-red-700">
            An 8-K workforce reduction was filed
            {screen.layoff_event_date
              ? ` on ${screen.layoff_event_date}`
              : ' recently'}
            . Verify headcount plans before accepting an offer.
          </p>
        </div>
      ) : null}

      <div className="mt-6 flex flex-col gap-4 md:flex-row">
        <div className="flex-1 rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-[#1E293B]">Financial Health</h3>
          {screen.layer1_status === 'unavailable' ? (
            <>
              <p className="mt-3 text-2xl font-bold text-gray-400">Not available</p>
              <p className="mt-1 text-sm text-gray-400">
                Private company — no SEC filing data
              </p>
            </>
          ) : (
            <>
              <p
                className={`mt-3 text-2xl font-bold tabular-nums ${layerScoreColor(
                  screen.layer1_score,
                )}`}
              >
                {screen.layer1_score != null ? `${screen.layer1_score}/100` : '—'}
              </p>
              {screen.layoff_event_detected ? (
                <span className="mt-2 inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">
                  ⚠ Active layoff filing
                </span>
              ) : null}
            </>
          )}
          <p className="mt-3 text-xs text-gray-400">Based on SEC EDGAR filings</p>
        </div>

        <div className="flex-1 rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-[#1E293B]">Culture Clarity</h3>
          {screen.layer2_status === 'unavailable' ||
          screen.layer2_status === 'insufficient_text' ? (
            <>
              <p className="mt-3 text-2xl font-bold text-gray-400">Not available</p>
              <p className="mt-1 text-sm text-gray-400">
                {screen.layer2_status === 'insufficient_text'
                  ? "Couldn't retrieve enough public text"
                  : 'Data unavailable'}
              </p>
            </>
          ) : (
            <p
              className={`mt-3 text-2xl font-bold tabular-nums ${layerScoreColor(
                screen.layer2_score,
              )}`}
            >
              {screen.layer2_score != null ? `${screen.layer2_score}/100` : '—'}
            </p>
          )}
          <p className="mt-3 text-xs text-gray-400">
            Based on job postings &amp; careers page
          </p>
          {jargonPhrases.length > 0 ? (
            <div className="mt-3">
              <p className="text-xs italic text-gray-500">Phrases flagged:</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {jargonPhrases.slice(0, 3).map((phrase) => (
                  <span
                    key={phrase}
                    className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                  >
                    {phrase}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <div className="flex-1 rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-[#1E293B]">Community Sentiment</h3>
          {screen.layer3_status === 'unavailable' ||
          screen.layer3_status === 'insufficient_data' ? (
            <>
              <p className="mt-3 text-2xl font-bold text-gray-400">Not available</p>
              <p className="mt-1 text-sm text-gray-400">Not enough Reddit posts found</p>
            </>
          ) : (
            <>
              <span
                className={`mt-3 inline-flex rounded-full px-3 py-1 text-sm font-medium capitalize ${layer3BandClasses(
                  screen.layer3_band,
                )}`}
              >
                {screen.layer3_band ?? 'unknown'}
              </span>
              {screen.layer3_detail?.confidence ? (
                <p className="mt-2 text-xs text-gray-500">
                  {confidenceLabel(screen.layer3_detail.confidence)}
                </p>
              ) : null}
              {screen.layer3_detail?.sentiment_summary ? (
                <p className="mt-2 text-sm italic text-gray-600">
                  {screen.layer3_detail.sentiment_summary}
                </p>
              ) : null}
            </>
          )}
          <p className="mt-3 text-xs text-gray-400">Based on Reddit discussions</p>
        </div>
      </div>

      <InterviewQuestionList
        questions={screen.questions ?? []}
        screenId={screen.id}
        authToken={authToken}
      />

      {sampleThreads.length > 0 ? (
        <div className="mt-6">
          <button
            type="button"
            onClick={() => setThreadsOpen((open) => !open)}
            className="flex w-full items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-left text-sm font-medium text-[#1E293B] hover:bg-gray-100"
          >
            <span>Community Discussions ({sampleThreads.length})</span>
            {threadsOpen ? (
              <ChevronUp className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            )}
          </button>
          {threadsOpen ? (
            <ul className="mt-2 space-y-2">
              {sampleThreads.slice(0, 3).map((thread) => (
                <li key={thread.url}>
                  <a
                    href={thread.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm text-[#1E293B] hover:bg-gray-50"
                  >
                    <span className="shrink-0 text-xs text-gray-500">
                      r/{thread.subreddit}
                    </span>
                    <span className="min-w-0 flex-1 truncate">
                      {truncate(thread.title, 80)}
                    </span>
                    <ExternalLink className="h-4 w-4 shrink-0 text-gray-400" />
                  </a>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {onRescreen ? (
        <button
          type="button"
          onClick={onRescreen}
          className="mt-4 rounded-lg border border-purple-700 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-50"
        >
          Screen Another Company
        </button>
      ) : null}
    </div>
  );
}
