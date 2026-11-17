document.addEventListener('DOMContentLoaded', () => {
  const menuBtn = document.getElementById('menuBtn');
  const mobileMenu = document.getElementById('mobileMenu');
  if (menuBtn && mobileMenu) menuBtn.addEventListener('click', () => mobileMenu.classList.toggle('hidden'));

  document.querySelectorAll('[data-tab-target]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-tab-target]').forEach(b => b.classList.remove('active-tab'));
      document.querySelectorAll('[data-tab]').forEach(panel => panel.classList.add('hidden'));
      btn.classList.add('active-tab');
      const target = document.querySelector(`[data-tab="${btn.dataset.tabTarget}"]`);
      if (target) target.classList.remove('hidden');
    });
  });

  document.querySelectorAll('.seat-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.disabled) return;
      document.querySelectorAll('.seat-btn').forEach(b => b.classList.remove('selected-seat'));
      btn.classList.add('selected-seat');
      const input = document.querySelector('input[name="seat_number"]');
      const label = document.getElementById('seatLabel');
      if (input) input.value = btn.dataset.seat;
      if (label) label.textContent = btn.dataset.seat;
    });
  });

  document.querySelectorAll('[data-loading]').forEach(form => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) { btn.innerHTML = 'Processing <span class="loader-dot"></span>'; btn.disabled = true; }
    });
  });
});
