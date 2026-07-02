/**
 * Axiom client-side logging for the Mingus admin dashboard.
 *
 * Include in <head> after Sentry with data-axiom-token (and optional data-axiom-dataset).
 */
(function () {
  let initScript = document.currentScript;

  if (!initScript || !initScript.dataset.axiomToken) {
    const scripts = document.querySelectorAll('script[data-axiom-token]');
    if (scripts.length > 0) {
      initScript = scripts[0];
    }
  }

  const token = (initScript?.dataset?.axiomToken || '').trim();
  const dataset = (initScript?.dataset?.axiomDataset || 'mingus-admin-frontend').trim();

  if (!token) {
    return;
  }

  const ingestUrl = 'https://api.axiom.co/v1/datasets/' + encodeURIComponent(dataset) + '/ingest';

  function buildEntry(level, message, extra) {
    const entry = {
      timestamp: new Date().toISOString(),
      level: level,
      message: message,
      path: window.location.pathname,
      url: window.location.href,
      user_agent: navigator.userAgent,
    };
    if (extra && typeof extra === 'object') {
      Object.assign(entry, extra);
    }
    return entry;
  }

  function send(entries) {
    try {
      fetch(ingestUrl, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + token,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(entries),
        keepalive: true,
      }).catch(function () {});
    } catch (e) {
      // fail silently
    }
  }

  function log(level, message, extra) {
    send([buildEntry(level, message, extra)]);
  }

  window.AxiomLogger = {
    log: function (message, extra) { log('log', message, extra); },
    info: function (message, extra) { log('info', message, extra); },
    warn: function (message, extra) { log('warn', message, extra); },
    error: function (message, extra) { log('error', message, extra); },
  };

  window.addEventListener('error', function (event) {
    log('error', event.message || 'Uncaught error', {
      filename: event.filename || '',
      lineno: event.lineno || 0,
      colno: event.colno || 0,
      type: 'uncaught',
    });
  });

  console.log('✓ Axiom logger initialized');
})();
