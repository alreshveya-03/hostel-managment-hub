/* ============================================================
   HOSTEL HUB  –  app.js
   Global interactive utilities
   ============================================================ */

/* ── Modal toggle ───────────────────────────────────────────── */
function toggleModal(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('hidden');
}

/* Close modal on backdrop click */
document.addEventListener('click', function (e) {
  if (e.target.classList.contains('modal')) {
    e.target.classList.add('hidden');
  }
});

/* Close modal on Escape */
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal:not(.hidden)').forEach(m => m.classList.add('hidden'));
  }
});

/* ── Tab switching ──────────────────────────────────────────── */
function showTab(tabId, btn) {
  const container = btn.closest('.profile-form-section') ||
                    btn.closest('.tab-container') ||
                    document.body;
  container.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
  container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  const tab = document.getElementById(tabId);
  if (tab) tab.classList.remove('hidden');
  btn.classList.add('active');
}

/* ── Flash auto-dismiss ─────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.alert').forEach(function (alert) {
    setTimeout(() => {
      alert.style.transition = 'opacity .5s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
});

/* ── Chart.js defaults (if available) ──────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  if (typeof Chart === 'undefined') return;
  Chart.defaults.color = '#7878a0';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.07)';
  Chart.defaults.font.family = "'Sora', sans-serif";
  Chart.defaults.font.size   = 12;
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.legend.labels.padding  = 16;
  Chart.defaults.plugins.tooltip.backgroundColor = '#1a1a2e';
  Chart.defaults.plugins.tooltip.borderColor     = 'rgba(99,102,241,0.4)';
  Chart.defaults.plugins.tooltip.borderWidth     = 1;
  Chart.defaults.plugins.tooltip.padding         = 10;
  Chart.defaults.plugins.tooltip.titleColor      = '#e8e8f0';
  Chart.defaults.plugins.tooltip.bodyColor       = '#7878a0';
});
