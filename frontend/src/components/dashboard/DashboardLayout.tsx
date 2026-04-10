import React, { useEffect, useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import PageWrapper from '../PageWrapper';
import NPSSurvey from '../NPSSurvey';
import { useAuth } from '../../hooks/useAuth';
import { useNPSSurvey } from '../../hooks/useNPSSurvey';

const VC_IMPORT_SHOWN_KEY = 'vc_import_shown';
const VC_IMPORT_PENDING_KEY = 'mingus_vc_import_pending';
const VC_IMPORT_HAD_LEAD_KEY = 'mingus_vc_import_had_lead';

const DashboardLayout: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { shouldShow, markShown, reloadStatus } = useNPSSurvey();
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
    navigate('/dashboard?tab=life-ledger');
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
    <PageWrapper>
      <div className="pt-16 min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2 flex items-center justify-end text-sm text-gray-800">
            <span className="flex items-center font-medium">
              {user?.name ?? 'User'}
              {user?.is_beta === true && (
                <span
                  title="Beta tester — Professional tier access"
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800 ml-2"
                >
                  BETA
                </span>
              )}
            </span>
          </div>
        </div>
        {user?.isAuthenticated && showVcWelcome ? (
          <div className="bg-gray-50 border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-5 flex flex-col sm:flex-row sm:items-start gap-4">
                <div className="flex-1 min-w-0">
                  <h2 className="text-base font-semibold text-gray-900">
                    Your Vibe Checkups data is here 💛
                  </h2>
                  <p className="mt-2 text-sm text-gray-600 leading-relaxed">
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
                      className="inline-flex items-center justify-center rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 transition-colors"
                    >
                      See My Life Ledger
                    </button>
                    <button
                      type="button"
                      onClick={dismissVcWelcome}
                      className="text-sm font-medium text-gray-600 hover:text-gray-900"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : null}
        <Outlet />
      </div>
      {user?.isAuthenticated && shouldShow ? (
        <NPSSurvey onDismiss={dismissNpsSurvey} />
      ) : null}
    </PageWrapper>
  );
};

export default DashboardLayout;
