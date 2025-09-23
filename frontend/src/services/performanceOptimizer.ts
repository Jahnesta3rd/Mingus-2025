/**
 * Mingus Application - Frontend Performance Optimizer
 * Comprehensive frontend optimization for Daily Outlook system
 */

import { lazy, Suspense, ComponentType } from 'react';
import { createRoot } from 'react-dom/client';

// Service Worker Registration
class ServiceWorkerManager {
  private static instance: ServiceWorkerManager;
  private registration: ServiceWorkerRegistration | null = null;

  static getInstance(): ServiceWorkerManager {
    if (!ServiceWorkerManager.instance) {
      ServiceWorkerManager.instance = new ServiceWorkerManager();
    }
    return ServiceWorkerManager.instance;
  }

  async register(): Promise<boolean> {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service Worker not supported');
      return false;
    }

    try {
      this.registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });

      console.log('Service Worker registered successfully');
      return true;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      return false;
    }
  }

  async updateCache(): Promise<void> {
    if (this.registration) {
      await this.registration.update();
    }
  }

  async clearCache(): Promise<void> {
    if (this.registration) {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
      );
    }
  }
}

// Progressive Loading Manager
class ProgressiveLoadingManager {
  private static instance: ProgressiveLoadingManager;
  private loadingQueue: Array<() => Promise<void>> = [];
  private isProcessing = false;

  static getInstance(): ProgressiveLoadingManager {
    if (!ProgressiveLoadingManager.instance) {
      ProgressiveLoadingManager.instance = new ProgressiveLoadingManager();
    }
    return ProgressiveLoadingManager.instance;
  }

  addToQueue(loader: () => Promise<void>): void {
    this.loadingQueue.push(loader);
    this.processQueue();
  }

  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.loadingQueue.length === 0) {
      return;
    }

    this.isProcessing = true;

    while (this.loadingQueue.length > 0) {
      const loader = this.loadingQueue.shift();
      if (loader) {
        try {
          await loader();
          // Add small delay to prevent blocking the main thread
          await new Promise(resolve => setTimeout(resolve, 10));
        } catch (error) {
          console.error('Progressive loading error:', error);
        }
      }
    }

    this.isProcessing = false;
  }
}

// Image Optimization Manager
class ImageOptimizationManager {
  private static instance: ImageOptimizationManager;
  private imageCache = new Map<string, string>();
  private lazyImages = new Set<HTMLImageElement>();

  static getInstance(): ImageOptimizationManager {
    if (!ImageOptimizationManager.instance) {
      ImageOptimizationManager.instance = new ImageOptimizationManager();
    }
    return ImageOptimizationManager.instance;
  }

  optimizeImage(src: string, options: {
    width?: number;
    height?: number;
    quality?: number;
    format?: 'webp' | 'jpeg' | 'png';
  } = {}): string {
    const { width, height, quality = 80, format = 'webp' } = options;
    
    // Check cache first
    const cacheKey = `${src}_${width}_${height}_${quality}_${format}`;
    if (this.imageCache.has(cacheKey)) {
      return this.imageCache.get(cacheKey)!;
    }

    // Generate optimized URL (assuming image service like Cloudinary or similar)
    let optimizedUrl = src;
    
    if (width || height || quality !== 80 || format !== 'webp') {
      const params = new URLSearchParams();
      if (width) params.append('w', width.toString());
      if (height) params.append('h', height.toString());
      params.append('q', quality.toString());
      params.append('f', format);
      
      optimizedUrl = `${src}?${params.toString()}`;
    }

    this.imageCache.set(cacheKey, optimizedUrl);
    return optimizedUrl;
  }

  setupLazyLoading(): void {
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            const dataSrc = img.dataset.src;
            
            if (dataSrc) {
              img.src = dataSrc;
              img.classList.remove('lazy');
              imageObserver.unobserve(img);
            }
          }
        });
      }, {
        rootMargin: '50px 0px',
        threshold: 0.01
      });

      // Observe all lazy images
      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }
  }

  preloadCriticalImages(imageUrls: string[]): void {
    imageUrls.forEach(url => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'image';
      link.href = url;
      document.head.appendChild(link);
    });
  }
}

// Component Lazy Loading Manager
class LazyLoadingManager {
  private static instance: LazyLoadingManager;
  private componentCache = new Map<string, ComponentType<any>>();

  static getInstance(): LazyLoadingManager {
    if (!LazyLoadingManager.instance) {
      LazyLoadingManager.instance = new LazyLoadingManager();
    }
    return LazyLoadingManager.instance;
  }

  createLazyComponent<T extends ComponentType<any>>(
    importFunc: () => Promise<{ default: T }>,
    fallback?: ComponentType
  ): ComponentType<T> {
    const LazyComponent = lazy(importFunc);
    
    return (props: any) => (
      <Suspense fallback={fallback ? <fallback /> : <div>Loading...</div>}>
        <LazyComponent {...props} />
      </Suspense>
    );
  }

  preloadComponent(importFunc: () => Promise<any>): void {
    importFunc().catch(error => {
      console.error('Component preload failed:', error);
    });
  }
}

// Performance Monitoring
class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: {
    pageLoadTime: number;
    firstContentfulPaint: number;
    largestContentfulPaint: number;
    cumulativeLayoutShift: number;
    firstInputDelay: number;
    totalBlockingTime: number;
  } = {
    pageLoadTime: 0,
    firstContentfulPaint: 0,
    largestContentfulPaint: 0,
    cumulativeLayoutShift: 0,
    firstInputDelay: 0,
    totalBlockingTime: 0
  };

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  startMonitoring(): void {
    // Monitor Core Web Vitals
    this.observeWebVitals();
    
    // Monitor resource loading
    this.observeResourceTiming();
    
    // Monitor user interactions
    this.observeUserInteractions();
  }

  private observeWebVitals(): void {
    // First Contentful Paint
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const fcp = entries[entries.length - 1];
      this.metrics.firstContentfulPaint = fcp.startTime;
    }).observe({ entryTypes: ['paint'] });

    // Largest Contentful Paint
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lcp = entries[entries.length - 1];
      this.metrics.largestContentfulPaint = lcp.startTime;
    }).observe({ entryTypes: ['largest-contentful-paint'] });

    // Cumulative Layout Shift
    new PerformanceObserver((list) => {
      let clsValue = 0;
      for (const entry of list.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
        }
      }
      this.metrics.cumulativeLayoutShift = clsValue;
    }).observe({ entryTypes: ['layout-shift'] });

    // First Input Delay
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      for (const entry of entries) {
        this.metrics.firstInputDelay = (entry as any).processingStart - entry.startTime;
      }
    }).observe({ entryTypes: ['first-input'] });
  }

  private observeResourceTiming(): void {
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        if (entry.duration > 1000) { // Log slow resources
          console.warn('Slow resource detected:', {
            name: entry.name,
            duration: entry.duration,
            size: (entry as any).transferSize
          });
        }
      });
    }).observe({ entryTypes: ['resource'] });
  }

  private observeUserInteractions(): void {
    let interactionCount = 0;
    const startTime = performance.now();

    const handleInteraction = () => {
      interactionCount++;
      const timeSinceStart = performance.now() - startTime;
      
      if (timeSinceStart > 5000 && interactionCount === 0) {
        console.warn('No user interactions detected in first 5 seconds');
      }
    };

    ['click', 'keydown', 'scroll', 'touchstart'].forEach(event => {
      document.addEventListener(event, handleInteraction, { once: true });
    });
  }

  getMetrics(): typeof this.metrics {
    return { ...this.metrics };
  }

  reportMetrics(): void {
    // Send metrics to analytics service
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'performance_metrics', {
        page_load_time: this.metrics.pageLoadTime,
        first_contentful_paint: this.metrics.firstContentfulPaint,
        largest_contentful_paint: this.metrics.largestContentfulPaint,
        cumulative_layout_shift: this.metrics.cumulativeLayoutShift,
        first_input_delay: this.metrics.firstInputDelay
      });
    }
  }
}

// Bundle Optimization Manager
class BundleOptimizationManager {
  private static instance: BundleOptimizationManager;
  private loadedChunks = new Set<string>();

  static getInstance(): BundleOptimizationManager {
    if (!BundleOptimizationManager.instance) {
      BundleOptimizationManager.instance = new BundleOptimizationManager();
    }
    return BundleOptimizationManager.instance;
  }

  preloadCriticalChunks(chunkNames: string[]): void {
    chunkNames.forEach(chunkName => {
      if (!this.loadedChunks.has(chunkName)) {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'script';
        link.href = `/static/js/${chunkName}.js`;
        document.head.appendChild(link);
        this.loadedChunks.add(chunkName);
      }
    });
  }

  optimizeBundleSplitting(): void {
    // Dynamic imports for route-based code splitting
    const routeChunks = {
      '/dashboard': () => import('../pages/Dashboard'),
      '/daily-outlook': () => import('../pages/DailyOutlook'),
      '/analytics': () => import('../pages/Analytics'),
      '/settings': () => import('../pages/Settings')
    };

    // Preload chunks based on user navigation patterns
    this.preloadCriticalChunks(['dashboard', 'daily-outlook']);
  }
}

// Main Performance Optimizer Class
export class PerformanceOptimizer {
  private serviceWorkerManager: ServiceWorkerManager;
  private progressiveLoadingManager: ProgressiveLoadingManager;
  private imageOptimizationManager: ImageOptimizationManager;
  private lazyLoadingManager: LazyLoadingManager;
  private performanceMonitor: PerformanceMonitor;
  private bundleOptimizationManager: BundleOptimizationManager;

  constructor() {
    this.serviceWorkerManager = ServiceWorkerManager.getInstance();
    this.progressiveLoadingManager = ProgressiveLoadingManager.getInstance();
    this.imageOptimizationManager = ImageOptimizationManager.getInstance();
    this.lazyLoadingManager = LazyLoadingManager.getInstance();
    this.performanceMonitor = PerformanceMonitor.getInstance();
    this.bundleOptimizationManager = BundleOptimizationManager.getInstance();
  }

  async initialize(): Promise<void> {
    // Initialize service worker
    await this.serviceWorkerManager.register();

    // Start performance monitoring
    this.performanceMonitor.startMonitoring();

    // Setup image optimization
    this.imageOptimizationManager.setupLazyLoading();

    // Optimize bundle splitting
    this.bundleOptimizationManager.optimizeBundleSplitting();

    console.log('Performance Optimizer initialized successfully');
  }

  // Daily Outlook specific optimizations
  async optimizeDailyOutlookLoading(): Promise<void> {
    // Preload critical Daily Outlook assets
    const criticalAssets = [
      '/static/images/daily-outlook-bg.webp',
      '/static/images/balance-score-chart.webp',
      '/static/images/quick-actions-icons.webp'
    ];

    this.imageOptimizationManager.preloadCriticalImages(criticalAssets);

    // Preload Daily Outlook components
    this.lazyLoadingManager.preloadComponent(() => 
      import('../components/DailyOutlook')
    );

    // Progressive loading for Daily Outlook data
    this.progressiveLoadingManager.addToQueue(async () => {
      // Load balance score first (most important)
      await this.loadBalanceScore();
    });

    this.progressiveLoadingManager.addToQueue(async () => {
      // Load quick actions second
      await this.loadQuickActions();
    });

    this.progressiveLoadingManager.addToQueue(async () => {
      // Load peer comparison data last
      await this.loadPeerComparisonData();
    });
  }

  private async loadBalanceScore(): Promise<void> {
    // Simulate API call for balance score
    return new Promise(resolve => {
      setTimeout(() => {
        console.log('Balance score loaded');
        resolve();
      }, 100);
    });
  }

  private async loadQuickActions(): Promise<void> {
    // Simulate API call for quick actions
    return new Promise(resolve => {
      setTimeout(() => {
        console.log('Quick actions loaded');
        resolve();
      }, 150);
    });
  }

  private async loadPeerComparisonData(): Promise<void> {
    // Simulate API call for peer comparison
    return new Promise(resolve => {
      setTimeout(() => {
        console.log('Peer comparison data loaded');
        resolve();
      }, 200);
    });
  }

  // Utility methods
  createOptimizedImage(src: string, options?: {
    width?: number;
    height?: number;
    quality?: number;
    format?: 'webp' | 'jpeg' | 'png';
  }): string {
    return this.imageOptimizationManager.optimizeImage(src, options);
  }

  createLazyComponent<T extends ComponentType<any>>(
    importFunc: () => Promise<{ default: T }>,
    fallback?: ComponentType
  ): ComponentType<T> {
    return this.lazyLoadingManager.createLazyComponent(importFunc, fallback);
  }

  getPerformanceMetrics() {
    return this.performanceMonitor.getMetrics();
  }

  reportPerformanceMetrics() {
    this.performanceMonitor.reportMetrics();
  }
}

// Export singleton instance
export const performanceOptimizer = new PerformanceOptimizer();

// Export individual managers for direct use
export {
  ServiceWorkerManager,
  ProgressiveLoadingManager,
  ImageOptimizationManager,
  LazyLoadingManager,
  PerformanceMonitor,
  BundleOptimizationManager
};
