import React, { useState } from 'react';
import CompanyScreenEntryModal from './CompanyScreenEntryModal';
import CompanyScreenPanel from './CompanyScreenPanel';
import ScreenHistoryDrawer from './ScreenHistoryDrawer';
import type { CompanyScreen } from '../types/companyScreen';

interface CompanyScreenWidgetProps {
  authToken: string;
}

export default function CompanyScreenWidget({ authToken }: CompanyScreenWidgetProps) {
  const [activeScreen, setActiveScreen] = useState<CompanyScreen | null>(null);
  const [entryModalOpen, setEntryModalOpen] = useState(false);
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false);

  return (
    <div className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <h3 className="text-base font-semibold text-[#1E293B]">Company Screen</h3>
        <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
          NEW
        </span>
      </div>

      {activeScreen == null ? (
        <>
          <p className="text-sm text-[#1E293B]">
            Screen a company before your next interview.
          </p>
          <p className="mt-1 text-sm text-gray-500">
            Get a financial health, culture, and community brief in under 20
            seconds.
          </p>
          <button
            type="button"
            onClick={() => setEntryModalOpen(true)}
            className="mt-4 w-full rounded-lg bg-purple-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-purple-800"
          >
            Screen a Company
          </button>
        </>
      ) : (
        <CompanyScreenPanel
          screen={activeScreen}
          authToken={authToken}
          onRescreen={() => {
            setActiveScreen(null);
            setEntryModalOpen(true);
          }}
        />
      )}

      <button
        type="button"
        onClick={() => setHistoryDrawerOpen(true)}
        className="mt-4 text-sm font-medium text-purple-700 hover:text-purple-900"
      >
        View past screens →
      </button>

      <CompanyScreenEntryModal
        isOpen={entryModalOpen}
        onClose={() => setEntryModalOpen(false)}
        onScreenComplete={(screen) => {
          setActiveScreen(screen);
          setEntryModalOpen(false);
        }}
        authToken={authToken}
      />

      <ScreenHistoryDrawer
        isOpen={historyDrawerOpen}
        onClose={() => setHistoryDrawerOpen(false)}
        onSelectScreen={(screen) => {
          setActiveScreen(screen);
          setHistoryDrawerOpen(false);
        }}
        authToken={authToken}
      />
    </div>
  );
}

interface CompanyScreenButtonProps {
  employerName: string;
  employerCik?: string;
  authToken: string;
  onScreenComplete?: (screen: CompanyScreen) => void;
}

export function CompanyScreenButton({
  employerName,
  employerCik,
  authToken,
  onScreenComplete,
}: CompanyScreenButtonProps) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setModalOpen(true)}
        className="text-sm text-purple-700 underline hover:text-purple-900"
      >
        Screen this company
      </button>
      <CompanyScreenEntryModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onScreenComplete={(screen) => {
          setModalOpen(false);
          onScreenComplete?.(screen);
        }}
        authToken={authToken}
        prefilledEmployerName={employerName}
        prefilledEmployerCik={employerCik}
      />
    </>
  );
}
