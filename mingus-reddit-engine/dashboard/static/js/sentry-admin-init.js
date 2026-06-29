/**
 * Sentry Initialization for Admin Dashboard
 *
 * This script initializes error tracking for the admin dashboardat dashboard.mingusapp.com
 * Include this script in the <head> of all admin pages BEFORE other scripts.
 */
(function() {
  // Get the current script more reliably
  let initScript = document.currentScript;
  
  // Fallback: find the script tag by looking for one with our src
  if (!initScript || !initScript.dataset.sentryDsn) {
    const scripts = document.querySelectorAll('script[data-sentry-dsn]');
    if (scripts.length > 0) {
      initScript = scripts[0];
    }
  }
  
  const sentryDsn = (initScript?.dataset?.sentryDsn || window.SENTRY_DSN_ADMIN || '').trim();
  const sentryEnvironment = (initScript?.dataset?.sentryEnvironment || window.SENTRY_ENVIRONMENT || 'production').trim();
  
  console.log('Sentry: DSN loaded:', !!sentryDsn, 'length:', sentryDsn.length);
  
  if (!sentryDsn) {
    console.warn('Sentry DSN not configured — admin error tracking disabled');
    return;
  }
  
  const script = document.createElement('script');
  script.src = 'https://browser.sentry-cdn.com/7.91.0/bundle.tracing.replay.min.js';
  script.crossOrigin = 'anonymous';
  script.onload = function() {
    initializeSentry(sentryDsn, sentryEnvironment);
  };
  document.head.appendChild(script);
})();

function initializeSentry(dsn, environment) {
  window.Sentry.init({
    dsn: dsn,
    environment: environment,
    tracesSampleRate: 1.0,
    replaysSessionSampleRate: 0.3,
    replaysOnErrorSampleRate: 1.0,
    integrations: [
      new window.Sentry.Replay({
        maskAllText: true,
        blockAllMedia: true,
        maskAllInputs: true,
      }),
    ],
  });
  console.log('✓ Sentry initialized for admin dashboard');
}
