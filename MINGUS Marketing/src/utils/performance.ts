import { analytics } from '../services/analytics'

// Type definitions for performance entries
interface LayoutShift extends PerformanceEntry {
  value: number
  hadRecentInput: boolean
}

interface PerformanceEventTiming extends PerformanceEntry {
  processingStart: number
  processingEnd: number
}

// Core Web Vitals thresholds
const CORE_WEB_VITALS_THRESHOLDS = {
  LCP: 2500, // Largest Contentful Paint (2.5s)
  FID: 100,  // First Input Delay (100ms)
  CLS: 0.1,  // Cumulative Layout Shift (0.1)
  FCP: 1800, // First Contentful Paint (1.8s)
  TTFB: 800  // Time to First Byte (800ms)
}

// Performance metrics interface
interface PerformanceMetrics {
  LCP?: number
  FID?: number
  CLS?: number
  FCP?: number
  TTFB?: number
  navigationStart?: number
  loadEventEnd?: number
  domContentLoaded?: number
  firstPaint?: number
  firstContentfulPaint?: number
}

// Performance observer for Core Web Vitals
class PerformanceMonitor {
  private metrics: PerformanceMetrics = {}
  private observers: PerformanceObserver[] = []

  constructor() {
    this.initObservers()
    this.trackNavigationTiming()
  }

  // Initialize performance observers
  private initObservers(): void {
    // LCP Observer
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const lastEntry = entries[entries.length - 1] as PerformanceEntry
          this.metrics.LCP = lastEntry.startTime
          this.trackMetric('LCP', lastEntry.startTime)
        })
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })
        this.observers.push(lcpObserver)
      } catch (error) {
        console.warn('LCP observer not supported:', error)
      }

      // FID Observer
      try {
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          entries.forEach((entry) => {
            const firstInputEntry = entry as PerformanceEventTiming
            this.metrics.FID = firstInputEntry.processingStart - firstInputEntry.startTime
            this.trackMetric('FID', this.metrics.FID)
          })
        })
        fidObserver.observe({ entryTypes: ['first-input'] })
        this.observers.push(fidObserver)
      } catch (error) {
        console.warn('FID observer not supported:', error)
      }

      // CLS Observer
      try {
        let clsValue = 0
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const layoutShiftEntry = entry as LayoutShift
            if (!layoutShiftEntry.hadRecentInput) {
              clsValue += layoutShiftEntry.value
            }
          }
          this.metrics.CLS = clsValue
          this.trackMetric('CLS', clsValue)
        })
        clsObserver.observe({ entryTypes: ['layout-shift'] })
        this.observers.push(clsObserver)
      } catch (error) {
        console.warn('CLS observer not supported:', error)
      }

      // FCP Observer
      try {
        const fcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const firstEntry = entries[0] as PerformanceEntry
          this.metrics.FCP = firstEntry.startTime
          this.trackMetric('FCP', firstEntry.startTime)
        })
        fcpObserver.observe({ entryTypes: ['paint'] })
        this.observers.push(fcpObserver)
      } catch (error) {
        console.warn('FCP observer not supported:', error)
      }
    }
  }

  // Track navigation timing metrics
  private trackNavigationTiming(): void {
    if ('performance' in window) {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      if (navigation) {
        this.metrics.navigationStart = navigation.startTime
        this.metrics.loadEventEnd = navigation.loadEventEnd
        this.metrics.domContentLoaded = navigation.domContentLoadedEventEnd
        this.metrics.TTFB = navigation.responseStart - navigation.requestStart

        // Track TTFB
        this.trackMetric('TTFB', this.metrics.TTFB)

        // Track page load time
        const pageLoadTime = navigation.loadEventEnd - navigation.startTime
        this.trackMetric('PageLoadTime', pageLoadTime)

        // Track DOM content loaded time
        const domContentLoadedTime = navigation.domContentLoadedEventEnd - navigation.startTime
        this.trackMetric('DOMContentLoaded', domContentLoadedTime)
      }
    }
  }

  // Track individual metric
  private trackMetric(name: string, value: number): void {
    const threshold = CORE_WEB_VITALS_THRESHOLDS[name as keyof typeof CORE_WEB_VITALS_THRESHOLDS]
    const rating = threshold ? this.getRating(value, threshold) : 'unknown'

    analytics.trackUserBehavior('performance_metric', {
      metric_name: name,
      metric_value: value,
      metric_rating: rating,
      threshold: threshold,
      timestamp: Date.now()
    })

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`Performance Metric - ${name}:`, {
        value: `${value.toFixed(2)}ms`,
        rating,
        threshold: threshold ? `${threshold}ms` : 'N/A'
      })
    }
  }

  // Get performance rating
  private getRating(value: number, threshold: number): 'good' | 'needs-improvement' | 'poor' {
    if (value <= threshold * 0.75) return 'good'
    if (value <= threshold) return 'needs-improvement'
    return 'poor'
  }

  // Get all metrics
  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics }
  }

  // Track custom performance metric
  public trackCustomMetric(name: string, value: number, category?: string): void {
    analytics.trackUserBehavior('custom_performance_metric', {
      metric_name: name,
      metric_value: value,
      metric_category: category,
      timestamp: Date.now()
    })
  }

  // Track resource loading performance
  public trackResourcePerformance(): void {
    if ('performance' in window) {
      const resources = performance.getEntriesByType('resource')
      resources.forEach((resource) => {
        const resourceEntry = resource as PerformanceResourceTiming
        this.trackCustomMetric('ResourceLoadTime', resourceEntry.duration, 'resource')
        this.trackCustomMetric('ResourceSize', resourceEntry.transferSize, 'resource')
      })
    }
  }

  // Track memory usage (if available)
  public trackMemoryUsage(): void {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      this.trackCustomMetric('MemoryUsed', memory.usedJSHeapSize, 'memory')
      this.trackCustomMetric('MemoryTotal', memory.totalJSHeapSize, 'memory')
      this.trackCustomMetric('MemoryLimit', memory.jsHeapSizeLimit, 'memory')
    }
  }

  // Track long tasks
  public trackLongTasks(): void {
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry) => {
            this.trackCustomMetric('LongTask', entry.duration, 'long-task')
          })
        })
        longTaskObserver.observe({ entryTypes: ['longtask'] })
        this.observers.push(longTaskObserver)
      } catch (error) {
        console.warn('Long task observer not supported:', error)
      }
    }
  }

  // Cleanup observers
  public destroy(): void {
    this.observers.forEach(observer => observer.disconnect())
    this.observers = []
  }
}

// Image loading performance tracker
export class ImagePerformanceTracker {
  private static instance: ImagePerformanceTracker
  private trackedImages: Set<string> = new Set()

  public static getInstance(): ImagePerformanceTracker {
    if (!ImagePerformanceTracker.instance) {
      ImagePerformanceTracker.instance = new ImagePerformanceTracker()
    }
    return ImagePerformanceTracker.instance
  }

  // Track image loading performance
  public trackImage(src: string): void {
    if (this.trackedImages.has(src)) return
    this.trackedImages.add(src)

    const img = new Image()
    const startTime = performance.now()

    img.onload = () => {
      const loadTime = performance.now() - startTime
      analytics.trackUserBehavior('image_load_performance', {
        image_src: src,
        load_time: loadTime,
        image_size: img.naturalWidth * img.naturalHeight,
        timestamp: Date.now()
      })
    }

    img.onerror = () => {
      analytics.trackUserBehavior('image_load_error', {
        image_src: src,
        timestamp: Date.now()
      })
    }

    img.src = src
  }

  // Track lazy loaded images
  public trackLazyImage(element: HTMLImageElement): void {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement
          this.trackImage(img.src)
          observer.unobserve(img)
        }
      })
    })

    observer.observe(element)
  }
}

// Bundle size tracker
export class BundleSizeTracker {
  // Track JavaScript bundle size
  public static trackBundleSize(): void {
    if ('performance' in window) {
      const resources = performance.getEntriesByType('resource')
      const jsResources = resources.filter(resource => 
        resource.name.includes('.js') && resource.name.includes('static')
      )

      jsResources.forEach(resource => {
        const resourceEntry = resource as PerformanceResourceTiming
        analytics.trackUserBehavior('bundle_size', {
          bundle_name: resource.name.split('/').pop(),
          bundle_size: resourceEntry.transferSize,
          bundle_duration: resource.duration,
          timestamp: Date.now()
        })
      })
    }
  }
}

// Network performance tracker
export class NetworkPerformanceTracker {
  // Track network conditions
  public static trackNetworkConditions(): void {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      analytics.trackUserBehavior('network_conditions', {
        effective_type: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        save_data: connection.saveData,
        timestamp: Date.now()
      })
    }
  }

  // Track API response times
  public static trackAPIResponse(url: string, startTime: number, endTime: number, status: number): void {
    const responseTime = endTime - startTime
    analytics.trackUserBehavior('api_performance', {
      api_url: url,
      response_time: responseTime,
      status_code: status,
      timestamp: Date.now()
    })
  }
}

// Performance optimization utilities
export class PerformanceOptimizer {
  // Debounce function calls
  public static debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout
    return (...args: Parameters<T>) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => func(...args), wait)
    }
  }

  // Throttle function calls
  public static throttle<T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): (...args: Parameters<T>) => void {
    let inThrottle: boolean
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args)
        inThrottle = true
        setTimeout(() => inThrottle = false, limit)
      }
    }
  }

  // Preload critical resources
  public static preloadResource(href: string, as: string): void {
    const link = document.createElement('link')
    link.rel = 'preload'
    link.href = href
    link.as = as
    document.head.appendChild(link)
  }

  // Prefetch non-critical resources
  public static prefetchResource(href: string): void {
    const link = document.createElement('link')
    link.rel = 'prefetch'
    link.href = href
    document.head.appendChild(link)
  }

  // Optimize images
  public static optimizeImage(img: HTMLImageElement): void {
    // Add loading="lazy" for images below the fold
    if (!img.loading) {
      img.loading = 'lazy'
    }

    // Add decoding="async" for better performance
    if (!img.decoding) {
      img.decoding = 'async'
    }

    // Track image performance
    ImagePerformanceTracker.getInstance().trackImage(img.src)
  }
}

// Initialize performance monitoring
export const performanceMonitor = new PerformanceMonitor()

// Export performance tracking functions
export const trackPerformance = {
  // Track Core Web Vitals
  trackCoreWebVitals: () => {
    // Already handled by PerformanceMonitor
  },

  // Track custom metrics
  trackCustomMetric: (name: string, value: number, category?: string) => {
    performanceMonitor.trackCustomMetric(name, value, category)
  },

  // Track image performance
  trackImage: (src: string) => {
    ImagePerformanceTracker.getInstance().trackImage(src)
  },

  // Track bundle size
  trackBundleSize: () => {
    BundleSizeTracker.trackBundleSize()
  },

  // Track network conditions
  trackNetworkConditions: () => {
    NetworkPerformanceTracker.trackNetworkConditions()
  },

  // Track API performance
  trackAPI: (url: string, startTime: number, endTime: number, status: number) => {
    NetworkPerformanceTracker.trackAPIResponse(url, startTime, endTime, status)
  },

  // Track resource performance
  trackResourcePerformance: () => {
    performanceMonitor.trackResourcePerformance()
  },

  // Track memory usage
  trackMemoryUsage: () => {
    performanceMonitor.trackMemoryUsage()
  },

  // Get current metrics
  getMetrics: () => {
    return performanceMonitor.getMetrics()
  },

  // Cleanup
  destroy: () => {
    performanceMonitor.destroy()
  }
}

// Auto-initialize performance tracking
if (typeof window !== 'undefined') {
  // Track initial page load
  window.addEventListener('load', () => {
    trackPerformance.trackBundleSize()
    trackPerformance.trackNetworkConditions()
    trackPerformance.trackResourcePerformance()
  })

  // Track memory usage periodically
  setInterval(() => {
    trackPerformance.trackMemoryUsage()
  }, 30000) // Every 30 seconds
} 