// FEDERAL WORKER CRISIS Landing Page JavaScript

// Modal functionality
function openModal() {
    document.getElementById('emailModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('emailModal').style.display = 'none';
}

function submitEmail(event) {
    event.preventDefault();
    
    const email = document.getElementById('emailInput').value;
    const agency = document.getElementById('agencyInput').value;
    const status = document.getElementById('statusInput').value;
    
    // Here you would typically send this data to your email service
    console.log('Email submission:', { email, agency, status });
    
    // For demo purposes, show success message
    alert('Thank you! Your Federal Worker Crisis Recovery Guide is being sent to your email. Check your inbox in the next few minutes.');
    
    closeModal();
    
    // Reset form
    document.getElementById('emailInput').value = '';
    document.getElementById('agencyInput').value = '';
    document.getElementById('statusInput').value = '';
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('emailModal');
    if (event.target == modal) {
        closeModal();
    }
}

// Add interactive behavior for FAQ
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.faq-question').forEach(question => {
        question.addEventListener('click', function() {
            const arrow = this.querySelector('.faq-arrow');
            if (arrow.style.transform === 'rotate(180deg)') {
                arrow.style.transform = 'rotate(0deg)';
            } else {
                arrow.style.transform = 'rotate(180deg)';
            }
        });
    });

    // Add fade-in animation on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all major sections
    document.querySelectorAll('.crisis-timeline, .benefits-section, .testimonials-section, .faq-section').forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(section);
    });
}); 