// WESLR V1 Static Website - Minimal JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Mobile navigation toggle
  const mobileNavToggle = document.getElementById('mobile-nav-toggle');
  const nav = document.getElementById('nav');
  
  if (mobileNavToggle && nav) {
    // Toggle menu
    mobileNavToggle.addEventListener('click', function(e) {
      e.stopPropagation();
      const isOpen = nav.classList.contains('open');
      
      if (isOpen) {
        nav.classList.remove('open');
        mobileNavToggle.setAttribute('aria-expanded', 'false');
        mobileNavToggle.textContent = '☰';
        document.body.classList.remove('nav-open');
      } else {
        nav.classList.add('open');
        mobileNavToggle.setAttribute('aria-expanded', 'true');
        mobileNavToggle.textContent = '✕';
        document.body.classList.add('nav-open');
      }
    });
    
    // Close nav when clicking a link
    nav.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        nav.classList.remove('open');
        mobileNavToggle.setAttribute('aria-expanded', 'false');
        mobileNavToggle.textContent = '☰';
        document.body.classList.remove('nav-open');
      });
    });
    
    // Close nav when clicking outside (on the page content)
    document.addEventListener('click', function(e) {
      if (nav.classList.contains('open')) {
        if (!nav.contains(e.target) && !mobileNavToggle.contains(e.target)) {
          nav.classList.remove('open');
          mobileNavToggle.setAttribute('aria-expanded', 'false');
          mobileNavToggle.textContent = '☰';
          document.body.classList.remove('nav-open');
        }
      }
    });
  }
  
  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href && href.length > 1) {
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  });
});