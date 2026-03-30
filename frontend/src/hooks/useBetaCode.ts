import { useState, useCallback } from 'react';

export interface BetaCodeState {
  code: string;
  setCode: (val: string) => void;
  isValidating: boolean;
  isValid: boolean | null;
  errorMessage: string | null;
  validate: () => Promise<void>;
  reset: () => void;
}

export function useBetaCode(): BetaCodeState {
  const [code, setCodeState] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const setCode = useCallback((val: string) => {
    setCodeState(val.toUpperCase());
    setIsValid(null);
    setErrorMessage(null);
  }, []);

  const reset = useCallback(() => {
    setCodeState('');
    setIsValid(null);
    setErrorMessage(null);
    setIsValidating(false);
  }, []);

  const validate = useCallback(async () => {
    const trimmed = code.trim().toUpperCase();
    setIsValidating(true);
    setErrorMessage(null);
    setIsValid(null);

    try {
      const res = await fetch('/api/beta/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: trimmed }),
      });

      if (res.status === 200) {
        const data = await res.json().catch(() => ({}));
        if (data.valid === true) {
          setIsValid(true);
          setErrorMessage(null);
        } else {
          setIsValid(false);
          setErrorMessage('Unable to verify code. Try again.');
        }
        return;
      }

      if (res.status === 404) {
        setIsValid(false);
        setErrorMessage('This code does not exist');
        return;
      }

      if (res.status === 409) {
        setIsValid(false);
        setErrorMessage('This code has already been used');
        return;
      }

      setIsValid(false);
      setErrorMessage('Unable to verify code. Try again.');
    } catch {
      setIsValid(false);
      setErrorMessage('Unable to verify code. Try again.');
    } finally {
      setIsValidating(false);
    }
  }, [code]);

  return {
    code,
    setCode,
    isValidating,
    isValid,
    errorMessage,
    validate,
    reset,
  };
}
