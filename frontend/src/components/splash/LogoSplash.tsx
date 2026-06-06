import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getDailyVibe } from '../../services/vibeService';
import SessionSetupTerminalError from '../auth/SessionSetupTerminalError';

const MIN_SPLASH_MS = 2000;

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

const LogoSplash: React.FC = () => {
  const navigate = useNavigate();
  const { getAccessToken, awaitSessionReady } = useAuth();
  const [phase, setPhase] = useState<'enter' | 'hold' | 'exit'>('enter');
  const [enterDone, setEnterDone] = useState(false);
  const [gateError, setGateError] = useState(false);
  const mountedRef = useRef(true);
  const splashStartRef = useRef(Date.now());
  const minSplashTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const waitForMinSplash = useCallback(async () => {
    const remaining = MIN_SPLASH_MS - (Date.now() - splashStartRef.current);
    if (remaining <= 0) return;
    await new Promise<void>((resolve) => {
      minSplashTimerRef.current = setTimeout(() => {
        minSplashTimerRef.current = null;
        resolve();
      }, remaining);
    });
  }, []);

  const clearMinSplashTimer = useCallback(() => {
    if (minSplashTimerRef.current) {
      clearTimeout(minSplashTimerRef.current);
      minSplashTimerRef.current = null;
    }
  }, []);

  // Trigger enter animation on next frame so CSS transition runs
  useEffect(() => {
    if (phase !== 'enter') return;
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => setEnterDone(true));
    });
    return () => cancelAnimationFrame(id);
  }, [phase]);

  const runGate = useCallback(async () => {
    const showGateError = async () => {
      await waitForMinSplash();
      if (!mountedRef.current) return;
      setGateError(true);
    };

    try {
      await awaitSessionReady();
    } catch (err) {
      console.error('LogoSplash: session-ready failed', err);
      await showGateError();
      return;
    }

    try {
      const token = getAccessToken ? getAccessToken() : null;
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (token) headers.Authorization = `Bearer ${token}`;

      const res = await fetch('/api/profile/setup-status', {
        method: 'GET',
        credentials: 'include',
        headers,
      });

      if (!res.ok) {
        console.error('LogoSplash: setup-status returned', res.status);
        await showGateError();
        return;
      }

      const data = await res.json();
      const isComplete =
        data.setupCompleted === true || data.onboarding_complete === true;

      if (!mountedRef.current) return;
      setPhase('exit');
      await delay(200);
      if (!mountedRef.current) return;
      await waitForMinSplash();
      if (!mountedRef.current) return;

      if (!isComplete) {
        navigate('/onboarding', { replace: true });
        return;
      }
      if (data.show_vibe_moment_today === true) {
        navigate('/vibe-check-meme?t=' + Date.now(), { replace: true });
        return;
      }
      navigate('/dashboard', { replace: true });
    } catch (err) {
      console.error('LogoSplash: setup-status failed', err);
      await showGateError();
    }
  }, [awaitSessionReady, getAccessToken, navigate, waitForMinSplash]);

  useEffect(() => {
    mountedRef.current = true;
    splashStartRef.current = Date.now();

    void getDailyVibe().catch(() => null);
    void runGate();

    const runHoldAnimation = async () => {
      await delay(300);
      if (!mountedRef.current) return;
      setPhase('hold');
    };

    void runHoldAnimation();
    return () => {
      mountedRef.current = false;
      clearMinSplashTimer();
    };
  }, [runGate, clearMinSplashTimer]);

  const handleRetry = () => {
    setGateError(false);
    setPhase('hold');
    setEnterDone(true);
    void runGate();
  };

  const isEnter = phase === 'enter';
  const isExit = phase === 'exit';
  const isHold = phase === 'hold';

  const contentOpacityScale =
    isExit ? 'opacity-0 scale-110' : !isEnter || enterDone ? 'opacity-100 scale-100' : 'opacity-0 scale-90';
  const transitionClass = isExit ? 'duration-200' : 'duration-300';
  const pulseClass = isHold ? 'animate-pulse-subtle' : '';

  return (
    <>
      <style>{`
        @keyframes pulse-subtle {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.02); }
        }
        .animate-pulse-subtle {
          animation: pulse-subtle 2s ease-in-out infinite;
        }
        @keyframes bounce-dot {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
          40% { transform: scale(1); opacity: 1; }
        }
        .animate-bounce-dot {
          animation: bounce-dot 1.4s ease-in-out infinite both;
        }
        .animate-bounce-dot:nth-child(1) { animation-delay: 0s; }
        .animate-bounce-dot:nth-child(2) { animation-delay: 0.2s; }
        .animate-bounce-dot:nth-child(3) { animation-delay: 0.4s; }
      `}</style>
      <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center relative">
        {gateError && (
          <SessionSetupTerminalError variant="dark" onRetry={handleRetry} />
        )}
        <div
          className={`flex flex-col items-center justify-center transition-all ease-out ${transitionClass} ${contentOpacityScale} ${pulseClass}`}
        >
          <img
            src="/mingus-logo.png"
            alt="Mingus"
            className="block max-w-[280px] w-full h-auto mb-3"
          />
          <p className="mt-3 text-2xl text-violet-400">Be. Do. Have...</p>
        </div>

        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-violet-500 animate-bounce-dot" />
          <span className="w-2 h-2 rounded-full bg-violet-500 animate-bounce-dot" />
          <span className="w-2 h-2 rounded-full bg-violet-500 animate-bounce-dot" />
        </div>
      </div>
    </>
  );
};

export default LogoSplash;
