/**
 * Sentry Initialization for Admin Dashboard
 *
 * This script initializes error tracking for the admin dashboard at dashboard.mingusapp.com
 * Include this script in the <head> of all admin pages BEFORE other scripts.
 */

(function() {
  const initScript = document.currentScript;
  const sentryDsn = initScript?.dataset?.sentryDsn || window.SENTRY_DSN_ADMIN || '';
  const sentryEnvironment = initScript?.dataset?.sentryEnvironment || window.SENTRY_ENVIRONMENT || 'production';

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

    beforeSend(event, hint) {
      if (event.exception) {
        const error = hint.originalException;

        if (error instanceof TypeError && error.message?.includes('favicon')) {
          return null;
        }

        if (error?.message?.includes('ResizeObserver')) {
          return null;
        }

        if (error?.message?.includes('Non-Error promise rejection')) {
          return null;
        }
      }

      return event;
    },
  });

  window.Sentry.setTag('app', 'admin-dashboard');
  window.Sentry.setTag('domain', 'dashboard.mingusapp.com');

  console.log('✓ Sentry initialized for admin dashboard');
}

window.setSentryAdminContext = function(adminId, adminEmail) {
  if (!window.Sentry) return;

  window.Sentry.setUser({
    id: adminId,
    email: adminEmail,
    username: adminEmail.split('@')[0],
  });

  window.Sentry.setContext('admin', {
    authenticated: true,
    timestamp: new Date().toISOString(),
  });

  window.Sentry.captureMessage('Admin authenticated', 'info');
};

window.clearSentryAdminContext = function() {
  if (!window.Sentry) return;

  window.Sentry.setUser(null);
  window.Sentry.setContext('admin', { authenticated: false });
  window.Sentry.captureMessage('Admin logged out', 'info');
};

window.trackAdminPageView = function(pageName) {
  if (!window.Sentry) return;

  window.Sentry.setTag('page', pageName);

  window.Sentry.addBreadcrumb({
    category: 'navigation',
    message: 'Navigated to ' + pageName,
    level: 'info',
    data: { page: pageName, timestamp: new Date().toISOString() },
  });
};

window.trackAdminAction = function(actionName, metadata) {
  if (!window.Sentry) return;

  window.Sentry.addBreadcrumb({
    category: 'admin-action',
    message: actionName,
    level: 'info',
    data: Object.assign({}, metadata || {}, { timestamp: new Date().toISOString() }),
  });
};

window.trackAdminApiCall = function(endpoint, status, duration, error) {
  if (!window.Sentry) return;

  if (error) {
    window.Sentry.captureException(error, {
      tags: {
        action: 'api_call',
        endpoint: endpoint,
        status: String(status),
      },
      extra: {
        endpoint: endpoint,
        status: status,
        durationMs: duration,
      },
    });
  } else {
    window.Sentry.addBreadcrumb({
      category: 'http.request',
      message: 'API call: ' + endpoint,
      level: 'info',
      data: {
        endpoint: endpoint,
        status: status,
        durationMs: duration,
      },
    });
  }
};

window.addEventListener('error', function(event) {
  if (window.Sentry && event.error) {
    window.Sentry.captureException(event.error, {
      tags: { type: 'uncaught_error' },
    });
  }
});

window.addEventListener('unhandledrejection', function(event) {
  if (window.Sentry && event.reason) {
    window.Sentry.captureException(event.reason, {
      tags: { type: 'unhandled_promise_rejection' },
    });
  }
});
