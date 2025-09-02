/**
 * MINGUS Mobile Performance Optimizer
 * Optimized for African American professionals on varying network speeds
 * Target: Sub-1MB page weight, <2s load time on 3G, offline-first functionality
 */

class MobilePerformanceOptimizer {
    constructor() {
        this.config = {
            targetPageWeight: 800 * 1024, // 800KB
            targetLoadTime: {
                '3g': 2500, // 2.5s
                '4g': 1500  // 1.5s
            },
            imageQuality: {
                '3g': 60,
                '4g': 85
            },
            cacheStrategy: {
                '3g': 'aggressive',
                '4g': 'balanced'
            }
        };
        
        this.networkInfo = this.detectNetwork();
        this.deviceInfo = this.detectDevice();
        this.performanceMetrics = {};
        
        this.init();
    }

    init() {
        this.setupNetworkMonitoring();
        this.optimizeImages();
        this.setupLazyLoading();
        this.optimizeFinancialCalculations();
        this.setupPerformanceMonitoring();
        this.enableOfflineSupport();
    }

    /**
     * Network Detection and Adaptation
     */
    detectNetwork() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        
        if (connection) {
            return {
                effectiveType: connection.effectiveType || '4g',
                downlink: connection.downlink || 10,
                rtt: connection.rtt || 50,
                saveData: connection.saveData || false
            };
        }

        // Fallback detection based on user agent and performance
        return this.fallbackNetworkDetection();
    }

    fallbackNetworkDetection() {
        // Detect based on common African American professional network patterns
        const userAgent = navigator.userAgent;
        const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
        
        // Common carriers in African American communities
        const carriers = {
            'verizon': /Verizon/i,
            'att': /AT&T|Cingular/i,
            'tmobile': /T-Mobile/i,
            'sprint': /Sprint/i,
            'metro': /MetroPCS/i,
            'cricket': /Cricket/i
        };

        let detectedCarrier = 'unknown';
        for (const [carrier, pattern] of Object.entries(carriers)) {
            if (pattern.test(userAgent)) {
                detectedCarrier = carrier;
                break;
            }
        }

        // Estimate network quality based on carrier and location patterns
        const networkQuality = this.estimateNetworkQuality(detectedCarrier);
        
        return {
            effectiveType: networkQuality.type,
            downlink: networkQuality.speed,
            rtt: networkQuality.latency,
            saveData: false,
            carrier: detectedCarrier
        };
    }

    estimateNetworkQuality(carrier) {
        // Network quality estimates based on carrier coverage in African American communities
        const carrierProfiles = {
            'verizon': { type: '4g', speed: 8, latency: 60 },
            'att': { type: '4g', speed: 6, latency: 80 },
            'tmobile': { type: '4g', speed: 5, latency: 90 },
            'sprint': { type: '3g', speed: 2, latency: 120 },
            'metro': { type: '3g', speed: 1.5, latency: 150 },
            'cricket': { type: '3g', speed: 1.2, latency: 180 },
            'unknown': { type: '3g', speed: 1.5, latency: 150 }
        };

        return carrierProfiles[carrier] || carrierProfiles['unknown'];
    }

    setupNetworkMonitoring() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        
        if (connection) {
            connection.addEventListener('change', () => {
                this.networkInfo = this.detectNetwork();
                this.adjustOptimizationStrategy();
            });
        }

        // Monitor network performance
        window.addEventListener('online', () => this.handleNetworkChange('online'));
        window.addEventListener('offline', () => this.handleNetworkChange('offline'));
    }

    handleNetworkChange(status) {
        console.log(`Network status changed to: ${status}`);
        
        if (status === 'offline') {
            this.enableOfflineMode();
        } else {
            this.disableOfflineMode();
            this.syncOfflineData();
        }
    }

    adjustOptimizationStrategy() {
        const { effectiveType, downlink } = this.networkInfo;
        
        if (effectiveType === '3g' || downlink < 1.5) {
            this.enableLowBandwidthMode();
        } else {
            this.enableHighBandwidthMode();
        }
    }

    enableLowBandwidthMode() {
        console.log('Enabling low bandwidth mode for 3G networks');
        
        // Reduce image quality
        this.setImageQuality(this.config.imageQuality['3g']);
        
        // Disable animations
        document.body.classList.add('low-bandwidth');
        
        // Reduce prefetching
        this.setPrefetchLimit(2);
        
        // Enable aggressive caching
        this.setCacheStrategy('aggressive');
    }

    enableHighBandwidthMode() {
        console.log('Enabling high bandwidth mode for 4G networks');
        
        // Use high quality images
        this.setImageQuality(this.config.imageQuality['4g']);
        
        // Enable animations
        document.body.classList.remove('low-bandwidth');
        
        // Increase prefetching
        this.setPrefetchLimit(5);
        
        // Use balanced caching
        this.setCacheStrategy('balanced');
    }

    /**
     * Image Optimization
     */
    optimizeImages() {
        const images = document.querySelectorAll('img[data-src]');
        
        images.forEach(img => {
            this.optimizeImage(img);
        });

        // Monitor for dynamically added images
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const images = node.querySelectorAll ? node.querySelectorAll('img[data-src]') : [];
                        images.forEach(img => this.optimizeImage(img));
                    }
                });
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }

    optimizeImage(img) {
        const { effectiveType } = this.networkInfo;
        const quality = this.config.imageQuality[effectiveType];
        
        // Set appropriate image source based on network
        const src = this.getOptimizedImageSrc(img.dataset.src, quality);
        img.src = src;
        
        // Add loading optimization
        img.loading = 'lazy';
        img.decoding = 'async';
        
        // Add error handling
        img.onerror = () => {
            this.handleImageError(img);
        };
    }

    getOptimizedImageSrc(originalSrc, quality) {
        // Convert to WebP if supported and network allows
        if (this.supportsWebP() && quality >= 75) {
            return originalSrc.replace(/\.(jpg|jpeg|png)$/i, '.webp');
        }
        
        // Use progressive JPEG for better perceived performance
        if (originalSrc.match(/\.(jpg|jpeg)$/i)) {
            return originalSrc.replace(/\.(jpg|jpeg)$/i, '-progressive.$1');
        }
        
        return originalSrc;
    }

    supportsWebP() {
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    }

    handleImageError(img) {
        // Fallback to original format
        const fallbackSrc = img.dataset.src.replace(/\.webp$/i, '.jpg');
        img.src = fallbackSrc;
        
        // Track image loading errors
        this.trackPerformanceMetric('image_error', {
            originalSrc: img.dataset.src,
            fallbackSrc: fallbackSrc,
            networkType: this.networkInfo.effectiveType
        });
    }

    setImageQuality(quality) {
        document.documentElement.style.setProperty('--image-quality', quality);
    }

    /**
     * Lazy Loading Implementation
     */
    setupLazyLoading() {
        const lazyElements = document.querySelectorAll('[data-lazy]');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadLazyElement(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.1
        });

        lazyElements.forEach(element => observer.observe(element));
    }

    loadLazyElement(element) {
        const type = element.dataset.lazy;
        
        switch (type) {
            case 'image':
                this.loadLazyImage(element);
                break;
            case 'component':
                this.loadLazyComponent(element);
                break;
            case 'script':
                this.loadLazyScript(element);
                break;
        }
    }

    loadLazyImage(element) {
        const img = element.querySelector('img');
        if (img && img.dataset.src) {
            this.optimizeImage(img);
        }
    }

    loadLazyComponent(element) {
        const componentName = element.dataset.component;
        if (componentName) {
            this.loadComponent(componentName, element);
        }
    }

    loadLazyScript(element) {
        const scriptSrc = element.dataset.src;
        if (scriptSrc) {
            this.loadScript(scriptSrc);
        }
    }

    /**
     * Financial Calculator Optimization
     */
    optimizeFinancialCalculations() {
        // Use Web Workers for heavy calculations
        if (typeof Worker !== 'undefined') {
            this.setupFinancialWorker();
        } else {
            this.setupChunkedCalculations();
        }
    }

    setupFinancialWorker() {
        this.financialWorker = new Worker('/js/financial-calculator-worker.js');
        
        this.financialWorker.onmessage = (event) => {
            this.handleFinancialResult(event.data);
        };
    }

    setupChunkedCalculations() {
        // Fallback for browsers without Web Workers
        this.chunkSize = 100;
        this.calculationQueue = [];
    }

    calculateSalaryComparison(data) {
        if (this.financialWorker) {
            return new Promise((resolve) => {
                this.financialWorker.postMessage({
                    type: 'salary-comparison',
                    data: data,
                    networkType: this.networkInfo.effectiveType
                });
                
                this.financialWorker.onmessage = (event) => {
                    resolve(event.data);
                };
            });
        } else {
            return this.calculateInChunks(data);
        }
    }

    calculateInChunks(data) {
        return new Promise((resolve) => {
            const chunks = this.chunkArray(data, this.chunkSize);
            let results = [];
            let index = 0;

            const processChunk = () => {
                if (index >= chunks.length) {
                    resolve(this.combineResults(results));
                    return;
                }

                setTimeout(() => {
                    const chunkResult = this.processChunk(chunks[index]);
                    results.push(chunkResult);
                    index++;
                    processChunk();
                }, 0);
            };

            processChunk();
        });
    }

    chunkArray(array, size) {
        const chunks = [];
        for (let i = 0; i < array.length; i += size) {
            chunks.push(array.slice(i, i + size));
        }
        return chunks;
    }

    /**
     * Performance Monitoring
     */
    setupPerformanceMonitoring() {
        // Monitor Core Web Vitals
        this.monitorWebVitals();
        
        // Monitor network performance
        this.monitorNetworkPerformance();
        
        // Monitor device performance
        this.monitorDevicePerformance();
        
        // Monitor user interactions
        this.monitorUserInteractions();
    }

    monitorWebVitals() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    this.trackPerformanceMetric(entry.entryType, {
                        name: entry.name,
                        value: entry.startTime || entry.processingStart || entry.value,
                        networkType: this.networkInfo.effectiveType,
                        deviceType: this.deviceInfo.type
                    });
                });
            });

            observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'paint'] });
        }
    }

    monitorNetworkPerformance() {
        // Track resource loading times
        const resources = performance.getEntriesByType('resource');
        
        resources.forEach(resource => {
            this.trackPerformanceMetric('resource_load', {
                name: resource.name,
                duration: resource.duration,
                size: resource.transferSize,
                networkType: this.networkInfo.effectiveType
            });
        });
    }

    monitorDevicePerformance() {
        // Monitor memory usage
        if ('memory' in performance) {
            setInterval(() => {
                this.trackPerformanceMetric('memory_usage', {
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit
                });
            }, 30000); // Every 30 seconds
        }

        // Monitor frame rate
        this.monitorFrameRate();
    }

    monitorFrameRate() {
        let frameCount = 0;
        let lastTime = performance.now();

        const countFrames = () => {
            frameCount++;
            const currentTime = performance.now();
            
            if (currentTime - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                this.trackPerformanceMetric('fps', { value: fps });
                
                frameCount = 0;
                lastTime = currentTime;
            }
            
            requestAnimationFrame(countFrames);
        };

        requestAnimationFrame(countFrames);
    }

    monitorUserInteractions() {
        // Track touch response times
        document.addEventListener('touchstart', (event) => {
            this.trackPerformanceMetric('touch_response', {
                target: event.target.tagName,
                timestamp: performance.now()
            });
        });

        // Track scroll performance
        let scrollTimeout;
        document.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.trackPerformanceMetric('scroll_performance', {
                    timestamp: performance.now()
                });
            }, 100);
        });
    }

    trackPerformanceMetric(type, data) {
        this.performanceMetrics[type] = this.performanceMetrics[type] || [];
        this.performanceMetrics[type].push({
            ...data,
            timestamp: Date.now()
        });

        // Send to analytics if threshold reached
        if (this.performanceMetrics[type].length >= 10) {
            this.sendToAnalytics(type, this.performanceMetrics[type]);
            this.performanceMetrics[type] = [];
        }
    }

    sendToAnalytics(type, data) {
        // Send performance data to analytics
        if (window.gtag) {
            gtag('event', 'performance_metric', {
                event_category: 'performance',
                event_label: type,
                value: data.length,
                custom_map: {
                    'network_type': this.networkInfo.effectiveType,
                    'device_type': this.deviceInfo.type
                }
            });
        }
    }

    /**
     * Offline Support
     */
    enableOfflineSupport() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('Service Worker registered for offline support');
                    this.serviceWorkerRegistration = registration;
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        }
    }

    enableOfflineMode() {
        document.body.classList.add('offline-mode');
        this.showOfflineIndicator();
    }

    disableOfflineMode() {
        document.body.classList.remove('offline-mode');
        this.hideOfflineIndicator();
    }

    showOfflineIndicator() {
        let indicator = document.getElementById('offline-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'offline-indicator';
            indicator.className = 'offline-indicator';
            indicator.innerHTML = `
                <div class="offline-message">
                    <span>📱 Working offline - Core features available</span>
                    <button onclick="this.parentElement.parentElement.remove()">×</button>
                </div>
            `;
            document.body.appendChild(indicator);
        }
        indicator.style.display = 'block';
    }

    hideOfflineIndicator() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    syncOfflineData() {
        // Sync any offline data when connection is restored
        const offlineData = this.getOfflineData();
        if (offlineData.length > 0) {
            this.syncData(offlineData);
        }
    }

    getOfflineData() {
        return JSON.parse(localStorage.getItem('mingus_offline_data') || '[]');
    }

    syncData(data) {
        // Send offline data to server
        fetch('/api/sync-offline-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                localStorage.removeItem('mingus_offline_data');
                console.log('Offline data synced successfully');
            }
        })
        .catch(error => {
            console.error('Failed to sync offline data:', error);
        });
    }

    /**
     * Device Detection
     */
    detectDevice() {
        const userAgent = navigator.userAgent;
        const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
        
        if (isMobile) {
            if (/Android/i.test(userAgent)) {
                return this.detectAndroidDevice(userAgent);
            } else if (/iPhone|iPad|iPod/i.test(userAgent)) {
                return this.detectIOSDevice(userAgent);
            }
        }
        
        return { type: 'desktop', capabilities: 'high' };
    }

    detectAndroidDevice(userAgent) {
        // Detect common Android devices used by African American professionals
        const devicePatterns = {
            'samsung_galaxy_a12': /SM-A125|SM-A127|SM-A125F/i,
            'samsung_galaxy_s21': /SM-G991|SM-G996|SM-G998/i,
            'google_pixel': /Pixel|G-|G9|G8|G7|G6/i,
            'oneplus': /OnePlus/i,
            'motorola': /Moto|XT/i
        };

        for (const [device, pattern] of Object.entries(devicePatterns)) {
            if (pattern.test(userAgent)) {
                return {
                    type: 'android',
                    device: device,
                    capabilities: this.getDeviceCapabilities(device)
                };
            }
        }

        return { type: 'android', device: 'unknown', capabilities: 'medium' };
    }

    detectIOSDevice(userAgent) {
        // Detect iOS devices
        if (/iPhone/i.test(userAgent)) {
            const version = this.getIOSVersion(userAgent);
            return {
                type: 'ios',
                device: 'iphone',
                version: version,
                capabilities: this.getIOSCapabilities(version)
            };
        } else if (/iPad/i.test(userAgent)) {
            return {
                type: 'ios',
                device: 'ipad',
                capabilities: 'high'
            };
        }

        return { type: 'ios', device: 'unknown', capabilities: 'medium' };
    }

    getIOSVersion(userAgent) {
        const match = userAgent.match(/OS (\d+)_/);
        return match ? parseInt(match[1]) : 14;
    }

    getIOSCapabilities(version) {
        if (version >= 15) return 'high';
        if (version >= 12) return 'medium';
        return 'low';
    }

    getDeviceCapabilities(device) {
        const capabilities = {
            'samsung_galaxy_a12': 'low',
            'samsung_galaxy_s21': 'high',
            'google_pixel': 'high',
            'oneplus': 'high',
            'motorola': 'medium'
        };
        
        return capabilities[device] || 'medium';
    }

    /**
     * Utility Methods
     */
    setPrefetchLimit(limit) {
        this.prefetchLimit = limit;
    }

    setCacheStrategy(strategy) {
        this.cacheStrategy = strategy;
    }

    loadComponent(name, element) {
        // Dynamic component loading
        import(`/js/components/${name}.js`)
            .then(module => {
                if (module.default) {
                    module.default(element);
                }
            })
            .catch(error => {
                console.error(`Failed to load component ${name}:`, error);
            });
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    handleFinancialResult(data) {
        // Handle financial calculation results
        const event = new CustomEvent('financial-calculation-complete', {
            detail: data
        });
        document.dispatchEvent(event);
    }

    combineResults(results) {
        // Combine chunked calculation results
        return results.reduce((combined, result) => {
            return { ...combined, ...result };
        }, {});
    }

    processChunk(chunk) {
        // Process a chunk of data
        return chunk.map(item => this.processItem(item));
    }

    processItem(item) {
        // Process individual item (placeholder)
        return item;
    }
}

// Initialize the optimizer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mingusPerformanceOptimizer = new MobilePerformanceOptimizer();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobilePerformanceOptimizer;
}
