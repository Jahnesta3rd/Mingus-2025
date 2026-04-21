import React, { useEffect, useRef, useState } from 'react';
import { MINGUS_TERMS_TEXT } from '../../constants/termsText';
import styles from './TermsAcknowledgmentModal.module.css';

const HEADER_TITLE_ID = 'terms-acknowledgment-modal-title';
const HEADER_SUBTITLE_ID = 'terms-acknowledgment-modal-subtitle';
const HEADER_DESC_ID = 'terms-acknowledgment-modal-description';
const SCROLL_REGION_DESC_ID = 'terms-acknowledgment-scroll-region-desc';
const CHECKBOX_ID = 'terms-acknowledgment-checkbox';

function csrfHeaders() {
  const token =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
    'test-token';
  return { 'X-CSRF-Token': token };
}

const recordAgreementAcceptance = async () => {
  const token =
    typeof window !== 'undefined'
      ? localStorage.getItem('auth_token') ?? localStorage.getItem('mingus_token')
      : null;

  const response = await fetch('/api/user/agreement-acceptance', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...csrfHeaders(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    credentials: 'include',
    body: JSON.stringify({
      agreementVersion: 'September2025',
    }),
  });

  if (!response.ok) {
    let message = `Failed to save agreement: ${response.statusText}`;
    try {
      const errorData = await response.json();
      message = errorData.error || errorData.message || message;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }

  return response.json();
};

export function TermsAcknowledgmentModal({ onAccept, onDecline }) {
  const scrollRegionRef = useRef(null);
  const dialogRef = useRef(null);

  const [hasScrolledEnough, setHasScrolledEnough] = useState(false);
  const [isCheckboxChecked, setIsCheckboxChecked] = useState(false);
  const [canAccept, setCanAccept] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [acceptError, setAcceptError] = useState(null);

  useEffect(() => {
    setCanAccept(hasScrolledEnough && isCheckboxChecked);
  }, [hasScrolledEnough, isCheckboxChecked]);

  useEffect(() => {
    const root = dialogRef.current;
    if (!root) return;

    const selector =
      'button:not([disabled]), [href]:not([tabindex="-1"]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

    const getFocusable = () =>
      Array.from(root.querySelectorAll(selector)).filter(
        (el) => el instanceof HTMLElement && !el.hasAttribute('disabled'),
      );

    const onKeyDown = (e) => {
      if (e.key !== 'Tab') return;
      const list = getFocusable();
      if (list.length === 0) return;
      const first = list[0];
      const last = list[list.length - 1];
      const active = document.activeElement;
      if (e.shiftKey) {
        if (active === first) {
          e.preventDefault();
          last.focus();
        }
      } else if (active === last) {
        e.preventDefault();
        first.focus();
      }
    };

    root.addEventListener('keydown', onKeyDown);
    return () => root.removeEventListener('keydown', onKeyDown);
  }, []);

  const handleScroll = () => {
    const el = scrollRegionRef.current;
    if (!el) return;

    const { scrollTop, scrollHeight, clientHeight } = el;
    const maxScroll = scrollHeight - clientHeight;
    const scrollProgressValue =
      maxScroll <= 0 ? 100 : (scrollTop / maxScroll) * 100;

    setHasScrolledEnough(scrollProgressValue >= 95);
  };

  const handleAccept = async () => {
    setAcceptError(null);
    setIsLoading(true);
    try {
      await recordAgreementAcceptance();
      onAccept();
    } catch (err) {
      console.error(err);
      setAcceptError(
        err instanceof Error ? err.message : 'Could not save your acceptance.',
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleDecline = () => {
    onDecline();
  };

  const acceptDisabled = !canAccept || isLoading;

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby={HEADER_TITLE_ID}
      aria-describedby={`${HEADER_SUBTITLE_ID} ${HEADER_DESC_ID} ${SCROLL_REGION_DESC_ID}`}
      className={styles.overlay}
    >
      <div className={styles.modal}>
        <header className={styles.header}>
          <h1 id={HEADER_TITLE_ID} className={styles.title}>
            MINGUS USER AGREEMENT
          </h1>
          <p id={HEADER_SUBTITLE_ID} className={styles.subtitle}>
            Last Updated: September 2025
          </p>
          <p id={HEADER_DESC_ID} className={styles.description}>
            Please read the full agreement below. You must scroll through the
            document and confirm your acceptance before continuing.
          </p>
        </header>

        <div
          ref={scrollRegionRef}
          role="region"
          aria-label="Agreement text, scrollable"
          aria-describedby={SCROLL_REGION_DESC_ID}
          tabIndex={0}
          onScroll={handleScroll}
          className={styles.scrollRegion}
        >
          <span id={SCROLL_REGION_DESC_ID} className={styles.srOnly}>
            Full Mingus user agreement legal text. Scroll to read all sections
            before accepting.
          </span>
          <div className={styles.termsBody}>{MINGUS_TERMS_TEXT}</div>
        </div>

        <footer className={styles.footer}>
          <div className={styles.checkboxRow}>
            <input
              id={CHECKBOX_ID}
              type="checkbox"
              checked={isCheckboxChecked}
              onChange={(e) => setIsCheckboxChecked(e.target.checked)}
              className={styles.checkboxInput}
            />
            <label htmlFor={CHECKBOX_ID} className={styles.checkboxLabel}>
              I have read and agree to the Mingus User Agreement, including the
              disclaimer that the application does not provide financial or
              professional advice.
            </label>
          </div>

          <div role="status" aria-live="polite" className={styles.statusRegion}>
            {acceptError ? (
              <p className={styles.scrollStatusMessage} role="alert">
                {acceptError}
              </p>
            ) : null}
            {!hasScrolledEnough ? (
              <p className={styles.scrollStatusMessage}>
                Please scroll through the entire agreement.
              </p>
            ) : null}
            {hasScrolledEnough && !isCheckboxChecked ? (
              <p className={styles.checkboxPromptMessage}>
                Please confirm that you agree by checking the box below.
              </p>
            ) : null}
            {canAccept ? (
              <p className={styles.acceptReadyMessage}>
                You can accept and continue.
              </p>
            ) : null}
          </div>

          <div className={styles.buttonRow}>
            <button
              type="button"
              aria-label="Decline the user agreement"
              onClick={handleDecline}
              className={styles.declineButton}
            >
              Decline
            </button>
            <button
              type="button"
              disabled={acceptDisabled}
              aria-label="Accept the user agreement and continue"
              onClick={handleAccept}
              className={
                acceptDisabled ? styles.acceptButtonDisabled : styles.acceptButton
              }
            >
              {isLoading ? 'ACCEPTING...' : 'ACCEPT & CONTINUE'}
            </button>
          </div>

          <p className={styles.footerDisclaimer}>
            This agreement is legally binding. If you decline, you may be unable
            to use certain features of the application.
          </p>
        </footer>
      </div>
    </div>
  );
}
