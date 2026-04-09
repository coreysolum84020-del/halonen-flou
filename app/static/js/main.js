// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');
if (navToggle && navMenu) {
  navToggle.addEventListener('click', () => {
    const isOpen = navMenu.classList.toggle('open');
    navToggle.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', isOpen);
  });
}

// FAQ accordion
document.querySelectorAll('.faq-question').forEach(question => {
  question.addEventListener('click', () => {
    const item = question.closest('.faq-item');
    if (item) item.classList.toggle('open');
  });
});

// Service option radio cards
document.querySelectorAll('.service-option').forEach(option => {
  option.addEventListener('click', () => {
    document.querySelectorAll('.service-option').forEach(o => o.classList.remove('selected'));
    option.classList.add('selected');
    const radio = option.querySelector('input[type="radio"]');
    if (radio) radio.checked = true;

    // Show/hide custom price input
    const customPriceGroup = document.getElementById('customPriceGroup');
    if (customPriceGroup) {
      customPriceGroup.style.display = radio && radio.value === 'promotion' ? 'block' : 'none';
    }
  });
});

// Fade-in on scroll
const fadeEls = document.querySelectorAll('.fade-in');
if (fadeEls.length) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  fadeEls.forEach(el => observer.observe(el));
}
