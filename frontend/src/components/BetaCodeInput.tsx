import React, { useEffect, useRef } from 'react';
import { Check } from 'lucide-react';
import { useBetaCode } from '../hooks/useBetaCode';
import LoadingSpinner from './common/LoadingSpinner';

export interface BetaCodeInputProps {
  onValidCode: (code: string) => void;
  onClear: () => void;
}

const INPUT_CLASSES =
  'appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500 sm:text-sm uppercase';

export const BetaCodeInput: React.FC<BetaCodeInputProps> = ({ onValidCode, onClear }) => {
  const { code, setCode, isValidating, isValid, errorMessage, validate } = useBetaCode();
  const lastNotifiedRef = useRef<string | null>(null);

  useEffect(() => {
    if (isValid === true && code.trim()) {
      const normalized = code.trim().toUpperCase();
      if (lastNotifiedRef.current !== normalized) {
        lastNotifiedRef.current = normalized;
        onValidCode(normalized);
      }
    }
  }, [isValid, code, onValidCode]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value.toUpperCase();
    if (isValid === true) {
      lastNotifiedRef.current = null;
      onClear();
    }
    setCode(v);
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
        <input
          type="text"
          autoComplete="off"
          spellCheck={false}
          placeholder="MINGUS-BETA-XXXXXX"
          value={code}
          onChange={handleChange}
          className={INPUT_CLASSES}
          aria-invalid={isValid === false}
          aria-describedby={errorMessage ? 'beta-code-error' : undefined}
        />
        <button
          type="button"
          onClick={() => void validate()}
          disabled={isValidating || !code.trim()}
          className="inline-flex justify-center items-center gap-2 px-4 py-2 rounded-md text-sm font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 shrink-0"
          style={{ backgroundColor: '#5B2D8E' }}
        >
          {isValidating ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin shrink-0" />
              Verifying…
            </>
          ) : (
            'Verify Code'
          )}
        </button>
      </div>

      {isValid === true && (
        <div className="flex items-start gap-2 rounded-md bg-green-50 border border-green-200 px-3 py-2 text-sm text-green-800">
          <Check className="w-5 h-5 text-green-600 shrink-0 mt-0.5" aria-hidden />
          <p>
            Beta access confirmed! You will have full Professional access — no payment required.
          </p>
        </div>
      )}

      {isValid === false && errorMessage && (
        <p id="beta-code-error" className="text-sm text-red-600" role="alert">
          {errorMessage}
        </p>
      )}
    </div>
  );
};

export default BetaCodeInput;
