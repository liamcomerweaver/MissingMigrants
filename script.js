/* Nav scroll + mobile toggle */
(function () {
  var nav = document.getElementById('nav');
  var toggle = document.getElementById('nav-toggle');
  var links = document.getElementById('nav-links');

  window.addEventListener('scroll', function () {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  });

  toggle.addEventListener('click', function () {
    toggle.classList.toggle('active');
    links.classList.toggle('open');
  });

  links.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () {
      toggle.classList.remove('active');
      links.classList.remove('open');
    });
  });
})();

/* Scroll reveal */
(function () {
  var els = document.querySelectorAll('.reveal, .reveal-stagger');

  function check() {
    var h = window.innerHeight;
    els.forEach(function (el) {
      if (el.getBoundingClientRect().top < h - 60) {
        el.classList.add('visible');
      }
    });
  }

  window.addEventListener('scroll', check);
  window.addEventListener('load', check);
  check();
})();

/* Smooth scroll */
document.querySelectorAll('a[href^="#"]').forEach(function (a) {
  a.addEventListener('click', function (e) {
    var t = document.querySelector(this.getAttribute('href'));
    if (t) {
      e.preventDefault();
      t.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

/* Contact form */
(function () {
  var f = document.getElementById('contact-form');
  if (!f) return;

  f.addEventListener('submit', function (e) {
    e.preventDefault();
    var b = f.querySelector('button[type="submit"]');
    var t = b.textContent;
    b.textContent = 'Message Sent!';
    b.disabled = true;
    b.style.opacity = '0.6';
    setTimeout(function () {
      b.textContent = t;
      b.disabled = false;
      b.style.opacity = '1';
      f.reset();
    }, 2500);
  });
})();
