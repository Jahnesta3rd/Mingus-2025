import React, { useEffect, useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import NPSSurvey from '../NPSSurvey';
import SeanEllisSurvey from '../SeanEllisSurvey';
import { useAuth } from '../../hooks/useAuth';
import { useNPSSurvey } from '../../hooks/useNPSSurvey';
import { useSeanEllisSurvey } from '../../hooks/useSeanEllisSurvey';
import { ImportantDateModalProvider } from '../../context/ImportantDateModalContext';

const VC_IMPORT_SHOWN_KEY = 'vc_import_shown';
const VC_IMPORT_PENDING_KEY = 'mingus_vc_import_pending';
const VC_IMPORT_HAD_LEAD_KEY = 'mingus_vc_import_had_lead';

const DashboardLayout: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { shouldShow, markShown, reloadStatus } = useNPSSurvey();
  const { shouldShow: shouldShowSeanEllis, dismiss, markSubmitted } = useSeanEllisSurvey();
  const [showVcWelcome, setShowVcWelcome] = useState(false);
  const [vcWelcomeHadLead, setVcWelcomeHadLead] = useState(true);

  useEffect(() => {
    if (!user?.isAuthenticated) return;
    try {
      const pending = sessionStorage.getItem(VC_IMPORT_PENDING_KEY) === '1';
      const already = localStorage.getItem(VC_IMPORT_SHOWN_KEY) === 'true';
      const hadLead = sessionStorage.getItem(VC_IMPORT_HAD_LEAD_KEY) !== '0';
      if (pending && !already) {
        setVcWelcomeHadLead(hadLead);
        setShowVcWelcome(true);
      }
    } catch {
      /* ignore */
    }
  }, [user?.isAuthenticated]);

  const dismissVcWelcome = () => {
    try {
      localStorage.setItem(VC_IMPORT_SHOWN_KEY, 'true');
      sessionStorage.removeItem(VC_IMPORT_PENDING_KEY);
      sessionStorage.removeItem(VC_IMPORT_HAD_LEAD_KEY);
    } catch {
      /* ignore */
    }
    setShowVcWelcome(false);
  };

  const goToLifeLedger = () => {
    navigate('/dashboard/tools?tab=life-ledger');
    window.setTimeout(() => {
      document
        .getElementById('life-ledger-dashboard-section')
        ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 400);
  };

  const dismissNpsSurvey = () => {
    void reloadStatus();
    markShown();
  };

  return (
    <div className="min-h-screen bg-[#FAF5FF]">
      <div className="min-h-screen">
        <div className="flex flex-col">
          {user?.isAuthenticated && showVcWelcome ? (
            <div className="border-b border-[#E2E8F0] bg-[#F8FAFC]">
              <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
                <div className="flex flex-col gap-4 rounded-xl border border-[#E2E8F0] bg-white p-4 shadow-sm sm:flex-row sm:items-start sm:p-5">
                  <div className="min-w-0 flex-1">
                    <h2 className="text-base font-semibold text-[#1E293B]">
                      Your Vibe Checkups data is here 💛
                    </h2>
                    <p className="mt-2 text-sm leading-relaxed text-[#64748B]">
                      {vcWelcomeHadLead ? (
                        <>
                          We imported your relationship financial profile. Your Life Ledger score and a
                          relationship budget line item have been added to your dashboard.
                        </>
                      ) : (
                        <>
                          Welcome from Vibe Checkups. Open Life Ledger to build your relationship
                          financial profile on Mingus.
                        </>
                      )}
                    </p>
                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        onClick={goToLifeLedger}
                        className="inline-flex items-center justify-center rounded-lg bg-[#5B2D8E] px-4 py-2 text-sm font-medium text-white transition-colors hover:opacity-95"
                      >
                        See My Life Ledger
                      </button>
                      <button
                        type="button"
                        onClick={dismissVcWelcome}
                        className="text-sm font-medium text-[#64748B] hover:text-[#1E293B]"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
          <ImportantDateModalProvider>
            <Outlet />
          </ImportantDateModalProvider>
        </div>
      </div>
      {user?.isAuthenticated && shouldShow ? (
        <NPSSurvey onDismiss={dismissNpsSurvey} />
      ) : null}
      {user?.isAuthenticated && shouldShowSeanEllis ? (
        <SeanEllisSurvey onDismiss={dismiss} onSubmitted={markSubmitted} />
      ) : null}
    </div>
  );
};

export default DashboardLayout;
