import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import PageWrapper from '../PageWrapper';
import NPSSurvey from '../NPSSurvey';
import { useAuth } from '../../hooks/useAuth';
import { useNPSSurvey } from '../../hooks/useNPSSurvey';

const VC_IMPORT_SHOWN_KEY = 'vc_import_shown';
const VC_IMPORT_PENDING_KEY = 'mingus_vc_import_pending';
const VC_IMPORT_HAD_LEAD_KEY = 'mingus_vc_import_had_lead';

function IconHome({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
      />
    </svg>
  );
}

function IconPeople({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  );
}

function IconChart({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  );
}

function IconGrid({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
      />
    </svg>
  );
}

function IconPerson({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  );
}

const DASH_NAV = [
  { to: '/dashboard', end: true, label: 'Home', Icon: IconHome },
  { to: '/dashboard/roster', end: false, label: 'My Roster', Icon: IconPeople },
  { to: '/dashboard/forecast', end: false, label: 'Forecast', Icon: IconChart },
  { to: '/dashboard/tools', end: false, label: 'Tools', Icon: IconGrid },
  { to: '/dashboard/profile', end: false, label: 'Profile', Icon: IconPerson },
] as const;

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
    isActive ? 'bg-[#5B2D8E] text-white' : 'bg-transparent text-[#64748B] hover:text-[#1E293B]',
  ].join(' ');

const bottomNavLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'flex flex-1 flex-col items-center justify-center gap-0.5 rounded-lg mx-0.5 my-1 py-2 px-0.5 text-[11px] font-medium transition-colors min-w-0 max-w-[20%]',
    isActive ? 'bg-[#5B2D8E] text-white' : 'bg-transparent text-[#64748B]',
  ].join(' ');

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
    <PageWrapper>
      <div className="min-h-screen bg-[#F8FAFC] pt-16 lg:flex lg:pb-0 pb-[calc(4.5rem+env(safe-area-inset-bottom,0px))]">
        <aside
          className="hidden lg:flex lg:w-56 lg:flex-shrink-0 lg:flex-col lg:border-r lg:border-[#E2E8F0] lg:bg-white lg:sticky lg:top-16 lg:self-start lg:max-h-[calc(100vh-4rem)] lg:overflow-y-auto"
          aria-label="Main navigation"
        >
          <nav className="flex flex-col gap-1 p-4">
            {DASH_NAV.map(({ to, end, label, Icon }) => (
              <NavLink key={to} to={to} end={end} className={navLinkClass}>
                <Icon className="h-5 w-5 flex-shrink-0" />
                {label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <div className="min-w-0 flex-1 flex flex-col">
          <div className="border-b border-[#E2E8F0] bg-white">
            <div className="mx-auto flex max-w-7xl items-center justify-end px-4 py-2 text-sm text-[#1E293B] sm:px-6 lg:px-8">
              <span className="flex items-center font-medium">
                {user?.name ?? 'User'}
                {user?.is_beta === true && (
                  <span
                    title="Beta tester — Professional tier access"
                    className="ml-2 inline-flex items-center rounded-full bg-[#EDE9FE] px-2 py-0.5 text-xs font-bold text-[#6D28D9]"
                  >
                    BETA
                  </span>
                )}
              </span>
            </div>
          </div>
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
          <Outlet />
        </div>

        <nav
          className="fixed bottom-0 left-0 right-0 z-40 flex border-t border-[#E2E8F0] bg-white lg:hidden pb-[env(safe-area-inset-bottom,0px)]"
          aria-label="Main navigation"
        >
          {DASH_NAV.map(({ to, end, label, Icon }) => (
            <NavLink key={to} to={to} end={end} className={bottomNavLinkClass}>
              <Icon className="h-5 w-5" />
              <span className="truncate text-center leading-tight">{label}</span>
            </NavLink>
          ))}
        </nav>
      </div>
      {user?.isAuthenticated && shouldShow ? (
        <NPSSurvey onDismiss={dismissNpsSurvey} />
      ) : null}
    </PageWrapper>
  );
};

export default DashboardLayout;
