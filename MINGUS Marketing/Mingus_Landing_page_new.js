// MINGUS Landing Page - Interactive JavaScript

class MingusLandingPage {
  constructor() {
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.initializeAnimations();
    this.setupIntersectionObserver();
    this.initializeProgressBars();
    this.setupSmoothScrolling();
    this.setupFAQAccordion();
    this.setupFormHandling();
    this.setupAnalytics();
  }

  setupEventListeners() {
    // CTA button clicks
    document.querySelectorAll('.main-cta, .feature-cta, .final-cta').forEach(button => {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleCTAClick(e.target);
      });
    });

    // Dropdown interactions
    document.querySelectorAll('.dropdown-header').forEach(header => {
      header.addEventListener('click', (e) => {
        this.toggleDropdown(e.target.closest('.dropdown-header'));
      });
    });

    // FAQ interactions
    document.querySelectorAll('.faq-question').forEach(question => {
      question.addEventListener('click', (e) => {
        this.toggleFAQ(e.target.closest('.faq-question'));
      });
    });

    // Form submissions
    const assessmentForm = document.getElementById('assessment-form');
    if (assessmentForm) {
      assessmentForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleAssessmentSubmission(e);
      });
    }

    // Scroll to top button
    const scrollToTopBtn = document.getElementById('scroll-to-top');
    if (scrollToTopBtn) {
      scrollToTopBtn.addEventListener('click', () => {
        this.scrollToTop();
      });
    }
  }

  initializeAnimations() {
    // Animate progress bars on load
    this.animateProgressBars();
    
    // Animate numbers
    this.animateNumbers();
    
    // Parallax effect for hero section
    this.setupParallax();
  }

  setupIntersectionObserver() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          
          // Special animations for specific sections
          if (entry.target.classList.contains('hero')) {
            this.animateHeroSection(entry.target);
          }
          
          if (entry.target.classList.contains('performance-dashboard')) {
            this.animateDashboard(entry.target);
          }
          
          if (entry.target.classList.contains('testimonials-section')) {
            this.animateTestimonials(entry.target);
          }
        }
      });
    }, observerOptions);

    document.querySelectorAll('.fade-in').forEach(el => {
      observer.observe(el);
    });
  }

  initializeProgressBars() {
    const progressBars = document.querySelectorAll('.progress-fill');
    
    progressBars.forEach(bar => {
      const targetWidth = bar.style.getPropertyValue('--target-width') || '0%';
      bar.style.width = '0%';
      
      // Store target width for later animation
      bar.dataset.targetWidth = targetWidth;
    });
  }

  animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-fill');
    
    progressBars.forEach((bar, index) => {
      const targetWidth = bar.dataset.targetWidth || '0%';
      
      setTimeout(() => {
        bar.style.width = targetWidth;
      }, 500 + (index * 200));
    });
  }

  animateNumbers() {
    const numberElements = document.querySelectorAll('.social-proof-number');
    
    numberElements.forEach(element => {
      const finalNumber = parseInt(element.textContent.replace(/,/g, ''));
      const duration = 2000; // 2 seconds
      const steps = 60;
      const increment = finalNumber / steps;
      let currentNumber = 0;
      
      const timer = setInterval(() => {
        currentNumber += increment;
        if (currentNumber >= finalNumber) {
          currentNumber = finalNumber;
          clearInterval(timer);
        }
        
        element.textContent = Math.floor(currentNumber).toLocaleString();
      }, duration / steps);
    });
  }

  setupParallax() {
    window.addEventListener('scroll', () => {
      const scrolled = window.pageYOffset;
      const parallaxElements = document.querySelectorAll('.hero, .visual-section');
      
      parallaxElements.forEach(element => {
        const speed = 0.5;
        const yPos = -(scrolled * speed);
        element.style.transform = `translateY(${yPos}px)`;
      });
    });
  }

  animateHeroSection(heroSection) {
    const cta = heroSection.querySelector('.main-cta');
    if (cta) {
      setTimeout(() => {
        cta.style.transform = 'scale(1.05)';
        setTimeout(() => {
          cta.style.transform = 'scale(1)';
        }, 200);
      }, 1000);
    }
  }

  animateDashboard(dashboard) {
    const progressBars = dashboard.querySelectorAll('.progress-fill');
    
    progressBars.forEach((bar, index) => {
      setTimeout(() => {
        const targetWidth = bar.dataset.targetWidth || '0%';
        bar.style.width = targetWidth;
      }, index * 300);
    });
  }

  animateTestimonials(testimonialsSection) {
    const cards = testimonialsSection.querySelectorAll('.testimonial-card');
    
    cards.forEach((card, index) => {
      setTimeout(() => {
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }, index * 200);
    });
  }

  setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }

  setupFAQAccordion() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
      const question = item.querySelector('.faq-question');
      const arrow = item.querySelector('.faq-arrow');
      
      question.addEventListener('click', () => {
        const isOpen = item.classList.contains('open');
        
        // Close all other items
        faqItems.forEach(otherItem => {
          otherItem.classList.remove('open');
          const otherArrow = otherItem.querySelector('.faq-arrow');
          if (otherArrow) {
            otherArrow.style.transform = 'rotate(0deg)';
          }
        });
        
        // Toggle current item
        if (!isOpen) {
          item.classList.add('open');
          if (arrow) {
            arrow.style.transform = 'rotate(180deg)';
          }
        }
      });
    });
  }

  toggleDropdown(header) {
    const isOpen = header.classList.contains('open');
    
    // Close all other dropdowns
    document.querySelectorAll('.dropdown-header').forEach(otherHeader => {
      otherHeader.classList.remove('open');
      const otherArrow = otherHeader.querySelector('.dropdown-arrow');
      if (otherArrow) {
        otherArrow.style.transform = 'rotate(0deg)';
      }
    });
    
    // Toggle current dropdown
    if (!isOpen) {
      header.classList.add('open');
      const arrow = header.querySelector('.dropdown-arrow');
      if (arrow) {
        arrow.style.transform = 'rotate(180deg)';
      }
    }
  }

  toggleFAQ(question) {
    const faqItem = question.closest('.faq-item');
    const isOpen = faqItem.classList.contains('open');
    const arrow = question.querySelector('.faq-arrow');
    
    // Close all other FAQ items
    document.querySelectorAll('.faq-item').forEach(otherItem => {
      otherItem.classList.remove('open');
      const otherArrow = otherItem.querySelector('.faq-arrow');
      if (otherArrow) {
        otherArrow.style.transform = 'rotate(0deg)';
      }
    });
    
    // Toggle current FAQ item
    if (!isOpen) {
      faqItem.classList.add('open');
      if (arrow) {
        arrow.style.transform = 'rotate(180deg)';
      }
    }
  }

  handleCTAClick(button) {
    // Track CTA click
    this.trackEvent('cta_click', {
      button_text: button.textContent,
      button_location: this.getButtonLocation(button)
    });
    
    // Show loading state
    button.classList.add('loading');
    
    // Simulate redirect to assessment
    setTimeout(() => {
      window.location.href = '/assessment';
    }, 500);
  }

  setupFormHandling() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleFormSubmission(form);
      });
    });
  }

  handleFormSubmission(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // Track form submission
    this.trackEvent('form_submission', {
      form_type: form.id || 'unknown',
      form_data: data
    });
    
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
      submitButton.classList.add('loading');
      submitButton.textContent = 'Submitting...';
    }
    
    // Simulate API call
    setTimeout(() => {
      this.showSuccessMessage(form);
    }, 1000);
  }

  handleAssessmentSubmission(event) {
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);
    
    // Track assessment start
    this.trackEvent('assessment_started', {
      email: data.email,
      source: 'landing_page'
    });
    
    // Redirect to assessment
    window.location.href = `/assessment?email=${encodeURIComponent(data.email)}`;
  }

  showSuccessMessage(form) {
    const successMessage = document.createElement('div');
    successMessage.className = 'success-message';
    successMessage.innerHTML = `
      <div style="background: #10b981; color: white; padding: 16px; border-radius: 8px; margin-top: 16px;">
        ✅ Thank you! We'll be in touch soon.
      </div>
    `;
    
    form.appendChild(successMessage);
    
    // Reset form
    form.reset();
    
    // Remove loading state
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
      submitButton.classList.remove('loading');
      submitButton.textContent = 'Submit';
    }
  }

  getButtonLocation(button) {
    if (button.classList.contains('main-cta')) return 'hero';
    if (button.classList.contains('feature-cta')) return 'feature';
    if (button.classList.contains('final-cta')) return 'final';
    return 'unknown';
  }

  setupAnalytics() {
    // Track page view
    this.trackEvent('page_view', {
      page: 'landing_page',
      url: window.location.href
    });
    
    // Track scroll depth
    this.trackScrollDepth();
    
    // Track time on page
    this.trackTimeOnPage();
  }

  trackEvent(eventName, data) {
    // Google Analytics 4
    if (window.gtag) {
      window.gtag('event', eventName, data);
    }
    
    // Custom analytics
    console.log('Analytics Event:', eventName, data);
    
    // Send to your analytics endpoint
    fetch('/api/analytics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        event: eventName,
        data: data,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      })
    }).catch(error => {
      console.error('Analytics error:', error);
    });
  }

  trackScrollDepth() {
    let maxScroll = 0;
    
    window.addEventListener('scroll', () => {
      const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
      
      if (scrollPercent > maxScroll) {
        maxScroll = scrollPercent;
        
        // Track at 25%, 50%, 75%, 100%
        if (maxScroll >= 25 && maxScroll < 50) {
          this.trackEvent('scroll_depth', { depth: 25 });
        } else if (maxScroll >= 50 && maxScroll < 75) {
          this.trackEvent('scroll_depth', { depth: 50 });
        } else if (maxScroll >= 75 && maxScroll < 100) {
          this.trackEvent('scroll_depth', { depth: 75 });
        } else if (maxScroll >= 100) {
          this.trackEvent('scroll_depth', { depth: 100 });
        }
      }
    });
  }

  trackTimeOnPage() {
    const startTime = Date.now();
    
    window.addEventListener('beforeunload', () => {
      const timeOnPage = Math.round((Date.now() - startTime) / 1000);
      this.trackEvent('time_on_page', { seconds: timeOnPage });
    });
  }

  scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }

  // Utility methods
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new MingusLandingPage();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MingusLandingPage;
} 