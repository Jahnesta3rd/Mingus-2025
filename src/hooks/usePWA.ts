import { useState, useEffect, useCallback } from 'react';

interface PWAState {
  isInstalled: boolean;
  isOnline: boolean;
  isStandalone: boolean;
  canInstall: boolean;
  deferredPrompt: any;
}

export const usePWA = () => {
  const [pwaState, setPwaState] = useState<PWAState>({
    isInstalled: false,
    isOnline: navigator.onLine,
    isStandalone: window.matchMedia('(display-mode: standalone)').matches,
    canInstall: false,
    deferredPrompt: null
  });

  // Register service worker
  const registerServiceWorker = useCallback(async () => {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered successfully:', registration);
        
        // Listen for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New content is available
                if (confirm('New version available! Reload to update?')) {
                  window.location.reload();
                }
              }
            });
          }
        });
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  }, []);

  // Handle app installation
  const installApp = useCallback(async () => {
    if (pwaState.deferredPrompt) {
      pwaState.deferredPrompt.prompt();
      const { outcome } = await pwaState.deferredPrompt.userChoice;
      
      if (outcome === 'accepted') {
        setPwaState(prev => ({ ...prev, isInstalled: true, canInstall: false }));
      }
      
      pwaState.deferredPrompt = null;
    }
  }, [pwaState.deferredPrompt]);

  // Share functionality
  const shareData = useCallback(async (data: {
    title: string;
    text: string;
    url: string;
  }) => {
    if (navigator.share) {
      try {
        await navigator.share(data);
        return true;
      } catch (error) {
        console.log('Share cancelled or failed:', error);
        return false;
      }
    } else {
      // Fallback to copying to clipboard
      try {
        await navigator.clipboard.writeText(`${data.title}\n\n${data.text}\n\n${data.url}`);
        return true;
      } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        return false;
      }
    }
  }, []);

  // Share salary comparison
  const shareSalaryComparison = useCallback(async (salaryData: any) => {
    const shareData = {
      title: 'My Salary Comparison - Mingus Income Dashboard',
      text: `I'm earning $${salaryData.userSalary.toLocaleString()} in ${salaryData.industry}. See how you compare!`,
      url: window.location.href
    };
    
    return await shareData(shareData);
  }, [shareData]);

  // Share career plan
  const shareCareerPlan = useCallback(async (careerPlan: any) => {
    const shareData = {
      title: 'My Career Advancement Plan - Mingus Income Dashboard',
      text: `I'm planning to increase my salary from $${careerPlan.currentSalary.toLocaleString()} to $${careerPlan.targetSalary.toLocaleString()}. Check out my strategy!`,
      url: window.location.href
    };
    
    return await shareData(shareData);
  }, [shareData]);

  // Request notification permission
  const requestNotificationPermission = useCallback(async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return false;
  }, []);

  // Subscribe to push notifications
  const subscribeToPushNotifications = useCallback(async () => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: 'YOUR_VAPID_PUBLIC_KEY' // Replace with actual VAPID key
        });
        
        console.log('Push notification subscription:', subscription);
        return subscription;
      } catch (error) {
        console.error('Failed to subscribe to push notifications:', error);
        return null;
      }
    }
    return null;
  }, []);

  useEffect(() => {
    // Register service worker on mount
    registerServiceWorker();

    // Listen for online/offline events
    const handleOnline = () => setPwaState(prev => ({ ...prev, isOnline: true }));
    const handleOffline = () => setPwaState(prev => ({ ...prev, isOnline: false }));

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Listen for beforeinstallprompt event
    const handleBeforeInstallPrompt = (e: any) => {
      e.preventDefault();
      setPwaState(prev => ({ 
        ...prev, 
        canInstall: true, 
        deferredPrompt: e 
      }));
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Listen for appinstalled event
    const handleAppInstalled = () => {
      setPwaState(prev => ({ 
        ...prev, 
        isInstalled: true, 
        canInstall: false 
      }));
    };

    window.addEventListener('appinstalled', handleAppInstalled);

    // Check if app is already installed
    const checkIfInstalled = () => {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      setPwaState(prev => ({ ...prev, isInstalled: isStandalone, isStandalone }));
    };

    checkIfInstalled();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, [registerServiceWorker]);

  return {
    ...pwaState,
    installApp,
    shareData,
    shareSalaryComparison,
    shareCareerPlan,
    requestNotificationPermission,
    subscribeToPushNotifications,
    registerServiceWorker
  };
}; 