/* ═══════════════════════════════════════════════════════════
   Cinema Caribe — Main JS
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Auto-dismiss alerts after 5 s ────────────────── */
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert?.close();
    }, 5000);
  });

  /* ── Scroll-reveal animation ─────────────────────── */
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('fade-in-up');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  /* ── Navbar scroll effect ────────────────────────── */
  const navbar = document.querySelector('.cc-navbar');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar?.classList.add('scrolled');
    } else {
      navbar?.classList.remove('scrolled');
    }
  });

});

/* ═══════════════════════════════════════════════════════════
   SEAT SELECTION MODULE
   ═══════════════════════════════════════════════════════════ */
const SeatSelection = (() => {
  let selected = new Set();
  let precio   = 0;

  function init(precioFuncion) {
    precio = precioFuncion;
    document.querySelectorAll('.cc-seat.disponible').forEach(btn => {
      btn.addEventListener('click', toggleSeat);
    });
    updateSummary();
  }

  function toggleSeat(e) {
    const btn = e.currentTarget;
    const id  = btn.dataset.id;
    const num = btn.dataset.numero;

    if (selected.has(id)) {
      selected.delete(id);
      btn.classList.remove('seleccionado');
    } else {
      if (selected.size >= 10) {
        showToast('Máximo 10 asientos por compra.', 'warning');
        return;
      }
      selected.add(id);
      btn.classList.add('seleccionado');
    }
    updateSummary();
    updateHiddenInputs();
  }

  function updateSummary() {
    const count = selected.size;
    const total = count * precio;

    const countEl = document.getElementById('seat-count');
    const totalEl = document.getElementById('seat-total');
    const btnCompra = document.getElementById('btn-compra');

    if (countEl) countEl.textContent = count;
    if (totalEl) totalEl.textContent = formatPeso(total);
    if (btnCompra) {
      btnCompra.disabled = count === 0;
      btnCompra.textContent = count === 0
        ? 'Selecciona asientos'
        : `Comprar ${count} asiento${count > 1 ? 's' : ''} — ${formatPeso(total)}`;
    }

    // Update selected list display
    const listEl = document.getElementById('selected-seats-list');
    if (listEl) {
      const nums = Array.from(document.querySelectorAll('.cc-seat.seleccionado'))
                        .map(b => b.dataset.numero);
      listEl.textContent = nums.length ? nums.join(', ') : '—';
    }
  }

  function updateHiddenInputs() {
    const container = document.getElementById('hidden-asientos');
    if (!container) return;
    container.innerHTML = '';
    selected.forEach(id => {
      const inp = document.createElement('input');
      inp.type  = 'hidden';
      inp.name  = 'asiento_ids[]';
      inp.value = id;
      container.appendChild(inp);
    });
  }

  function formatPeso(v) {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency', currency: 'COP', minimumFractionDigits: 0
    }).format(v);
  }

  return { init };
})();

/* ═══════════════════════════════════════════════════════════
   TOAST HELPER
   ═══════════════════════════════════════════════════════════ */
function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container') || createToastContainer();
  const id = 'toast-' + Date.now();
  const icons = { success: 'check-circle', warning: 'exclamation-triangle',
                  danger: 'x-circle', info: 'info-circle' };
  container.insertAdjacentHTML('beforeend', `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body">
          <i class="bi bi-${icons[type] || 'info-circle'} me-2"></i>${msg}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>
  `);
  const el = document.getElementById(id);
  const toast = new bootstrap.Toast(el, { delay: 4000 });
  toast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

function createToastContainer() {
  const div = document.createElement('div');
  div.id = 'toast-container';
  div.className = 'toast-container position-fixed bottom-0 end-0 p-3';
  div.style.zIndex = 9999;
  document.body.appendChild(div);
  return div;
}

/* ═══════════════════════════════════════════════════════════
   QR SCANNER (via camera, for validation page)
   ═══════════════════════════════════════════════════════════ */
function initQrInput() {
  const input = document.getElementById('codigo-input');
  if (input) input.focus();
}
