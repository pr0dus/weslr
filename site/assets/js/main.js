// WESLR V1 Static Website - Minimal JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Mobile navigation toggle
  const mobileNavToggle = document.getElementById('mobile-nav-toggle');
  const nav = document.getElementById('nav');
  
  if (mobileNavToggle && nav) {
    mobileNavToggle.addEventListener('click', function() {
      nav.classList.toggle('open');
      const isOpen = nav.classList.contains('open');
      mobileNavToggle.setAttribute('aria-expanded', isOpen);
      mobileNavToggle.textContent = isOpen ? '✕' : '☰';
      
      // Prevent body scroll when nav is open
      if (isOpen) {
        document.body.classList.add('nav-open');
      } else {
        document.body.classList.remove('nav-open');
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