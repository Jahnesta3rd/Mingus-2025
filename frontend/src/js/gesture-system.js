/**
 * MINGUS Gesture System
 * Comprehensive gesture support for mobile financial app navigation and interaction
 */

class GestureSystem {
    constructor() {
        this.gestures = new Map();
        this.activeGestures = new Set();
        this.touchStartData = new Map();
        this.gestureThresholds = {
            swipe: 50,
            pinch: 0.1,
            rotate: 15,
            longPress: 500
        };
        
        this.init();
    }
    
    init() {
        this.setupSwipeGestures();
        this.setupPinchToZoom();
        this.setupCarouselGestures();
        this.setupPullToRefresh();
        this.setupLongPressGestures();
        this.setupGestureOptimization();
    }
    
    // ===== SWIPE GESTURES FOR FINANCIAL DATA NAVIGATION =====
    setupSwipeGestures() {
        // Financial data navigation swipes
        this.setupFinancialDataSwipes();
        this.setupChartNavigationSwipes();
        this.setupFormNavigationSwipes();
    }
    
    setupFinancialDataSwipes() {
        const financialContainers = document.querySelectorAll('.financial-data-container, .data-grid, .metrics-panel');
        
        financialContainers.forEach(container => {
            this.addSwipeGesture(container, {
                left: () => this.navigateFinancialData('next'),
                right: () => this.navigateFinancialData('prev'),
                up: () => this.expandFinancialSection(),
                down: () => this.collapseFinancialSection()
            });
        });
    }
    
    setupChartNavigationSwipes() {
        const chartContainers = document.querySelectorAll('.chart-container, .graph-container, .analytics-chart');
        
        chartContainers.forEach(chart => {
            this.addSwipeGesture(chart, {
                left: () => this.navigateChartPeriod('next'),
                right: () => this.navigateChartPeriod('prev'),
                up: () => this.zoomChartIn(),
                down: () => this.zoomChartOut()
            });
        });
    }
    
    setupFormNavigationSwipes() {
        const formSections = document.querySelectorAll('.form-section, .form-step, .wizard-step');
        
        formSections.forEach(section => {
            this.addSwipeGesture(section, {
                left: () => this.navigateFormStep('next'),
                right: () => this.navigateFormStep('prev')
            });
        });
    }
    
    addSwipeGesture(element, callbacks) {
        if (!element) return;
        
        const gestureId = `swipe-${Date.now()}-${Math.random()}`;
        
        element.addEventListener('touchstart', (e) => {
            this.handleSwipeStart(e, gestureId);
        }, { passive: true });
        
        element.addEventListener('touchmove', (e) => {
            this.handleSwipeMove(e, gestureId);
        }, { passive: true });
        
        element.addEventListener('touchend', (e) => {
            this.handleSwipeEnd(e, gestureId, callbacks);
        }, { passive: true });
        
        this.gestures.set(gestureId, {
            element: element,
            type: 'swipe',
            callbacks: callbacks
        });
    }
    
    handleSwipeStart(event, gestureId) {
        const touch = event.touches[0];
        this.touchStartData.set(gestureId, {
            x: touch.clientX,
            y: touch.clientY,
            time: Date.now()
        });
    }
    
    handleSwipeMove(event, gestureId) {
        // Prevent default to avoid scrolling during swipe gestures
        if (this.isSwipeGesture(event, gestureId)) {
            event.preventDefault();
        }
    }
    
    handleSwipeEnd(event, gestureId, callbacks) {
        const startData = this.touchStartData.get(gestureId);
        if (!startData) return;
        
        const touch = event.changedTouches[0];
        const deltaX = touch.clientX - startData.x;
        const deltaY = touch.clientY - startData.y;
        const deltaTime = Date.now() - startData.time;
        
        // Determine swipe direction and velocity
        const isHorizontal = Math.abs(deltaX) > Math.abs(deltaY);
        const isFast = deltaTime < 300;
        const isLong = Math.abs(deltaX) > this.gestureThresholds.swipe || Math.abs(deltaY) > this.gestureThresholds.swipe;
        
        if (isLong && isFast) {
            if (isHorizontal) {
                if (deltaX > 0 && callbacks.right) {
                    callbacks.right();
                } else if (deltaX < 0 && callbacks.left) {
                    callbacks.left();
                }
            } else {
                if (deltaY > 0 && callbacks.down) {
                    callbacks.down();
                } else if (deltaY < 0 && callbacks.up) {
                    callbacks.up();
                }
            }
            
            // Trigger haptic feedback
            if (window.touchManager) {
                window.touchManager.triggerHaptic('navigation');
            }
        }
        
        this.touchStartData.delete(gestureId);
    }
    
    isSwipeGesture(event, gestureId) {
        const startData = this.touchStartData.get(gestureId);
        if (!startData) return false;
        
        const touch = event.touches[0];
        const deltaX = Math.abs(touch.clientX - startData.x);
        const deltaY = Math.abs(touch.clientY - startData.y);
        
        return deltaX > 20 || deltaY > 20;
    }
    
    // ===== PINCH-TO-ZOOM FOR FINANCIAL CHARTS =====
    setupPinchToZoom() {
        const zoomableElements = document.querySelectorAll('.chart-container, .graph-container, .financial-chart, [data-zoomable]');
        
        zoomableElements.forEach(element => {
            this.addPinchToZoom(element);
        });
    }
    
    addPinchToZoom(element) {
        if (!element) return;
        
        let initialDistance = 0;
        let initialScale = 1;
        let currentScale = 1;
        
        element.addEventListener('touchstart', (e) => {
            if (e.touches.length === 2) {
                initialDistance = this.getTouchDistance(e.touches[0], e.touches[1]);
                initialScale = currentScale;
                e.preventDefault();
            }
        }, { passive: false });
        
        element.addEventListener('touchmove', (e) => {
            if (e.touches.length === 2) {
                const currentDistance = this.getTouchDistance(e.touches[0], e.touches[1]);
                const scale = currentDistance / initialDistance;
                currentScale = Math.max(0.5, Math.min(3, initialScale * scale));
                
                this.applyZoom(element, currentScale);
                e.preventDefault();
            }
        }, { passive: false });
        
        element.addEventListener('touchend', (e) => {
            if (e.touches.length < 2) {
                // Snap to reasonable zoom levels
                if (currentScale < 0.8) currentScale = 0.5;
                else if (currentScale > 2.5) currentScale = 3;
                else if (currentScale > 0.8 && currentScale < 1.2) currentScale = 1;
                
                this.applyZoom(element, currentScale);
                
                // Trigger haptic feedback
                if (window.touchManager) {
                    window.touchManager.triggerHaptic('selection');
                }
            }
        }, { passive: true });
    }
    
    getTouchDistance(touch1, touch2) {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    applyZoom(element, scale) {
        element.style.transform = `scale(${scale})`;
        element.style.transformOrigin = 'center center';
        
        // Update chart if it's a financial chart
        if (element.classList.contains('financial-chart') && window.updateChartZoom) {
            window.updateChartZoom(scale);
        }
    }
    
    // ===== TOUCH-FRIENDLY CAROUSEL CONTROLS =====
    setupCarouselGestures() {
        const carousels = document.querySelectorAll('.carousel, .testimonials-carousel, .features-carousel, .financial-products-carousel');
        
        carousels.forEach(carousel => {
            this.addCarouselGestures(carousel);
        });
    }
    
    addCarouselGestures(carousel) {
        if (!carousel) return;
        
        let startX = 0;
        let currentTranslate = 0;
        let prevTranslate = 0;
        let isDragging = false;
        
        const track = carousel.querySelector('.carousel-track') || carousel;
        const items = carousel.querySelectorAll('.carousel-item, .carousel-slide');
        
        if (!track || items.length === 1) return;
        
        carousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
            track.style.transition = 'none';
        }, { passive: true });
        
        carousel.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            
            const currentX = e.touches[0].clientX;
            const diff = currentX - startX;
            currentTranslate = prevTranslate + diff;
            
            // Add resistance at edges
            const maxTranslate = -(items.length - 1) * 100;
            if (currentTranslate > 0) {
                currentTranslate = currentTranslate * 0.3;
            } else if (currentTranslate < maxTranslate) {
                currentTranslate = maxTranslate + (currentTranslate - maxTranslate) * 0.3;
            }
            
            this.updateCarouselPosition(track, currentTranslate);
        }, { passive: true });
        
        carousel.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            
            isDragging = false;
            track.style.transition = 'transform 0.3s ease-out';
            
            // Snap to nearest item
            const itemWidth = 100 / items.length;
            const snapIndex = Math.round(-currentTranslate / itemWidth);
            const snapTranslate = -snapIndex * itemWidth;
            
            currentTranslate = snapTranslate;
            prevTranslate = snapTranslate;
            
            this.updateCarouselPosition(track, currentTranslate);
            
            // Update active indicators
            this.updateCarouselIndicators(carousel, snapIndex);
            
            // Trigger haptic feedback
            if (window.touchManager) {
                window.touchManager.triggerHaptic('selection');
            }
        }, { passive: true });
    }
    
    updateCarouselPosition(track, translate) {
        track.style.transform = `translateX(${translate}%)`;
    }
    
    updateCarouselIndicators(carousel, activeIndex) {
        const indicators = carousel.querySelectorAll('.carousel-indicator, .carousel-dot');
        indicators.forEach((indicator, index) => {
            if (index === activeIndex) {
                indicator.classList.add('active');
                indicator.setAttribute('aria-current', 'true');
            } else {
                indicator.classList.remove('active');
                indicator.setAttribute('aria-current', 'false');
            }
        });
    }
    
    // ===== PULL-TO-REFRESH FOR FINANCIAL DATA =====
    setupPullToRefresh() {
        const refreshableContainers = document.querySelectorAll('.financial-data-container, .dashboard-container, .analytics-container');
        
        refreshableContainers.forEach(container => {
            this.addPullToRefresh(container);
        });
    }
    
    addPullToRefresh(container) {
        if (!container) return;
        
        let startY = 0;
        let currentY = 0;
        let isPulling = false;
        let pullDistance = 0;
        const maxPullDistance = 100;
        
        // Create refresh indicator
        const refreshIndicator = document.createElement('div');
        refreshIndicator.className = 'pull-refresh-indicator';
        refreshIndicator.innerHTML = `
            <div class="refresh-icon">↓</div>
            <div class="refresh-text">Pull to refresh</div>
        `;
        refreshIndicator.style.cssText = `
            position: absolute;
            top: -60px;
            left: 50%;
            transform: translateX(-50%);
            text-align: center;
            color: var(--text-light);
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
            z-index: 1000;
        `;
        
        container.style.position = 'relative';
        container.appendChild(refreshIndicator);
        
        container.addEventListener('touchstart', (e) => {
            if (container.scrollTop === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        }, { passive: true });
        
        container.addEventListener('touchmove', (e) => {
            if (!isPulling) return;
            
            currentY = e.touches[0].clientY;
            pullDistance = Math.max(0, currentY - startY);
            
            if (pullDistance > 0) {
                e.preventDefault();
                
                const pullRatio = Math.min(pullDistance / maxPullDistance, 1);
                const opacity = pullRatio;
                const scale = 0.8 + (pullRatio * 0.2);
                
                refreshIndicator.style.opacity = opacity;
                refreshIndicator.style.transform = `translateX(-50%) scale(${scale})`;
                
                if (pullRatio > 0.8) {
                    refreshIndicator.querySelector('.refresh-text').textContent = 'Release to refresh';
                    refreshIndicator.querySelector('.refresh-icon').textContent = '↑';
                } else {
                    refreshIndicator.querySelector('.refresh-text').textContent = 'Pull to refresh';
                    refreshIndicator.querySelector('.refresh-icon').textContent = '↓';
                }
            }
        }, { passive: false });
        
        container.addEventListener('touchend', (e) => {
            if (!isPulling) return;
            
            isPulling = false;
            
            if (pullDistance > maxPullDistance * 0.8) {
                // Trigger refresh
                this.triggerFinancialDataRefresh(container);
            }
            
            // Reset indicator
            refreshIndicator.style.opacity = '0';
            refreshIndicator.style.transform = 'translateX(-50%) scale(1)';
            refreshIndicator.querySelector('.refresh-text').textContent = 'Pull to refresh';
            refreshIndicator.querySelector('.refresh-icon').textContent = '↓';
            
            pullDistance = 0;
        }, { passive: true });
    }
    
    triggerFinancialDataRefresh(container) {
        // Show loading state
        if (window.touchManager) {
            window.touchManager.showLoading('Refreshing financial data...');
        }
        
        // Trigger refresh event
        const refreshEvent = new CustomEvent('financial-data-refresh', {
            detail: { container: container }
        });
        document.dispatchEvent(refreshEvent);
        
        // Simulate refresh delay
        setTimeout(() => {
            if (window.touchManager) {
                window.touchManager.hideLoading();
            }
            
            // Show success feedback
            this.showRefreshSuccess(container);
        }, 2000);
    }
    
    showRefreshSuccess(container) {
        const successMessage = document.createElement('div');
        successMessage.className = 'refresh-success-message';
        successMessage.textContent = 'Data refreshed successfully!';
        successMessage.style.cssText = `
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--success-color);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: var(--border-radius);
            font-size: 14px;
            z-index: 1000;
            animation: slideInDown 0.3s ease;
        `;
        
        container.appendChild(successMessage);
        
        setTimeout(() => {
            if (successMessage.parentNode) {
                successMessage.parentNode.removeChild(successMessage);
            }
        }, 3000);
    }
    
    // ===== LONG PRESS GESTURES =====
    setupLongPressGestures() {
        const longPressElements = document.querySelectorAll('.financial-data-item, .chart-container, .metric-card');
        
        longPressElements.forEach(element => {
            this.addLongPressGesture(element);
        });
    }
    
    addLongPressGesture(element) {
        if (!element) return;
        
        let longPressTimer = null;
        let hasLongPressed = false;
        
        element.addEventListener('touchstart', (e) => {
            hasLongPressed = false;
            longPressTimer = setTimeout(() => {
                hasLongPressed = true;
                this.handleLongPress(element, e);
            }, this.gestureThresholds.longPress);
        }, { passive: true });
        
        element.addEventListener('touchend', (e) => {
            if (longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
            
            if (!hasLongPressed) {
                // Handle normal tap
                this.handleNormalTap(element, e);
            }
        }, { passive: true });
        
        element.addEventListener('touchmove', (e) => {
            if (longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
        }, { passive: true });
    }
    
    handleLongPress(element, event) {
        // Show context menu or additional options
        this.showContextMenu(element, event);
        
        // Trigger haptic feedback
        if (window.touchManager) {
            window.touchManager.triggerHaptic('heavy');
        }
    }
    
    handleNormalTap(element, event) {
        // Handle normal tap interactions
        if (element.classList.contains('financial-data-item')) {
            this.expandFinancialItem(element);
        }
    }
    
    showContextMenu(element, event) {
        // Create context menu for financial data items
        const contextMenu = document.createElement('div');
        contextMenu.className = 'context-menu';
        contextMenu.innerHTML = `
            <div class="context-menu-item" data-action="export">Export Data</div>
            <div class="context-menu-item" data-action="share">Share</div>
            <div class="context-menu-item" data-action="details">View Details</div>
        `;
        
        contextMenu.style.cssText = `
            position: fixed;
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-heavy);
            z-index: 10000;
            min-width: 150px;
            padding: 0.5rem 0;
        `;
        
        // Position menu
        const rect = element.getBoundingClientRect();
        contextMenu.style.left = `${rect.left}px`;
        contextMenu.style.top = `${rect.bottom + 10}px`;
        
        document.body.appendChild(contextMenu);
        
        // Handle menu item clicks
        contextMenu.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            this.handleContextMenuAction(action, element);
            document.body.removeChild(contextMenu);
        });
        
        // Close menu when clicking outside
        setTimeout(() => {
            document.addEventListener('click', () => {
                if (contextMenu.parentNode) {
                    document.body.removeChild(contextMenu);
                }
            }, { once: true });
        }, 100);
    }
    
    handleContextMenuAction(action, element) {
        switch (action) {
            case 'export':
                this.exportFinancialData(element);
                break;
            case 'share':
                this.shareFinancialData(element);
                break;
            case 'details':
                this.showFinancialDetails(element);
                break;
        }
    }
    
    // ===== GESTURE OPTIMIZATION =====
    setupGestureOptimization() {
        this.optimizeGesturePerformance();
        this.setupGestureThrottling();
    }
    
    optimizeGesturePerformance() {
        // Use passive event listeners where possible
        const gestureElements = document.querySelectorAll('[data-gesture-enabled]');
        
        gestureElements.forEach(element => {
            element.addEventListener('touchstart', () => {}, { passive: true });
            element.addEventListener('touchmove', () => {}, { passive: true });
            element.addEventListener('touchend', () => {}, { passive: true });
        });
    }
    
    setupGestureThrottling() {
        // Throttle gesture processing for better performance
        let gestureTimeout;
        
        document.addEventListener('touchstart', () => {
            clearTimeout(gestureTimeout);
            gestureTimeout = setTimeout(() => {
                this.processActiveGestures();
            }, 16); // ~60fps
        }, { passive: true });
    }
    
    processActiveGestures() {
        // Process any pending gesture operations
        this.activeGestures.forEach(gestureId => {
            const gesture = this.gestures.get(gestureId);
            if (gesture && gesture.process) {
                gesture.process();
            }
        });
    }
    
    // ===== FINANCIAL DATA NAVIGATION METHODS =====
    navigateFinancialData(direction) {
        const event = new CustomEvent('financial-data-navigate', {
            detail: { direction: direction }
        });
        document.dispatchEvent(event);
    }
    
    navigateChartPeriod(direction) {
        const event = new CustomEvent('chart-period-navigate', {
            detail: { direction: direction }
        });
        document.dispatchEvent(event);
    }
    
    expandFinancialSection() {
        const event = new CustomEvent('financial-section-expand');
        document.dispatchEvent(event);
    }
    
    collapseFinancialSection() {
        const event = new CustomEvent('financial-section-collapse');
        document.dispatchEvent(event);
    }
    
    zoomChartIn() {
        const event = new CustomEvent('chart-zoom', { detail: { direction: 'in' } });
        document.dispatchEvent(event);
    }
    
    zoomChartOut() {
        const event = new CustomEvent('chart-zoom', { detail: { direction: 'out' } });
        document.dispatchEvent(event);
    }
    
    navigateFormStep(direction) {
        const event = new CustomEvent('form-step-navigate', {
            detail: { direction: direction }
        });
        document.dispatchEvent(event);
    }
    
    expandFinancialItem(element) {
        element.classList.toggle('expanded');
        
        // Trigger haptic feedback
        if (window.touchManager) {
            window.touchManager.triggerHaptic('selection');
        }
    }
    
    exportFinancialData(element) {
        // Handle data export
        console.log('Exporting financial data from:', element);
    }
    
    shareFinancialData(element) {
        // Handle data sharing
        console.log('Sharing financial data from:', element);
    }
    
    showFinancialDetails(element) {
        // Show detailed financial information
        console.log('Showing financial details for:', element);
    }
}

// Initialize gesture system
document.addEventListener('DOMContentLoaded', () => {
    window.gestureSystem = new GestureSystem();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GestureSystem;
}
