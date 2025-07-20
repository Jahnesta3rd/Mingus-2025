// Smooth scrolling for nav links (with focus management for accessibility)
document.querySelectorAll('a.nav-link').forEach(link => {
  link.addEventListener('click', function(e) {
    const href = this.getAttribute('href');
    if (href && href.startsWith('#')) {
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
        setTimeout(() => target.focus({ preventScroll: true }), 600);
      }
    }
  });
});

// Form validation and loading state
const form = document.getElementById('contact-form');
if (form) {
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    const email = document.getElementById('email');
    const error = document.getElementById('email-error');
    const btn = this.querySelector('button');
    let valid = true;
    if (!email.value || !email.validity.valid) {
      error.textContent = "Please enter a valid email address.";
      email.setAttribute('aria-invalid', 'true');
      email.focus();
      valid = false;
    } else {
      error.textContent = "";
      email.removeAttribute('aria-invalid');
    }
    if (valid) {
      btn.disabled = true;
      btn.setAttribute('aria-disabled', 'true');
      btn.textContent = "Submitting...";
      setTimeout(() => {
        btn.disabled = false;
        btn.removeAttribute('aria-disabled');
        btn.textContent = "Submit";
        alert("Form submitted!");
        form.reset();
      }, 1500);
    }
  });
}

// Fade-in animation on scroll (Intersection Observer)
const fadeEls = document.querySelectorAll('.fade-in');
const fadeInOnScroll = (entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('fade-in-visible');
      observer.unobserve(entry.target);
    }
  });
};
const fadeObserver = new IntersectionObserver(fadeInOnScroll, { threshold: 0.1 });
fadeEls.forEach(el => {
  fadeObserver.observe(el);
});

// Add .fade-in-visible to trigger the end state of fade-in
const style = document.createElement('style');
style.innerHTML = `.fade-in-visible { opacity: 1 !important; transform: none !important; }`;
document.head.appendChild(style);

// If you dynamically create images in JS, add loading="lazy" to them 