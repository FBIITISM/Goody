// Goody Kitchen Dashboard JavaScript

let lastUpdate = new Date().toISOString();
let refreshInterval = null;

function startAutoRefresh(intervalMs = 15000) {
  if (refreshInterval) clearInterval(refreshInterval);
  refreshInterval = setInterval(refreshOrders, intervalMs);
}

async function refreshOrders() {
  try {
    const res = await fetch(`/kitchen/orders?since=${encodeURIComponent(lastUpdate)}`);
    if (!res.ok) return;
    const orders = await res.json();

    if (orders.length > 0) {
      lastUpdate = new Date().toISOString();
      // Reload page to get fresh HTML-rendered order cards
      window.location.reload();
    }

    // Update live badge
    const badge = document.getElementById('liveBadge');
    if (badge) {
      badge.textContent = '● Live';
      badge.className = 'badge bg-success';
    }
  } catch (e) {
    const badge = document.getElementById('liveBadge');
    if (badge) {
      badge.textContent = '● Offline';
      badge.className = 'badge bg-danger';
    }
  }
}

async function updateOrderStatus(orderId, newStatus) {
  const btn = event.currentTarget;
  const orig = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

  try {
    const res = await fetch(`/kitchen/order/${orderId}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    const data = await res.json();
    if (data.success) {
      window.location.reload();
    } else {
      alert('Update failed: ' + (data.error || 'Unknown'));
      btn.disabled = false;
      btn.innerHTML = orig;
    }
  } catch (e) {
    alert('Network error.');
    btn.disabled = false;
    btn.innerHTML = orig;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  startAutoRefresh(15000);

  // Sound notification for new orders (if browser supports)
  const audioCtx = window.AudioContext || window.webkitAudioContext;
  if (audioCtx) {
    window.playNotif = function () {
      const ctx = new audioCtx();
      const osc = ctx.createOscillator();
      osc.connect(ctx.destination);
      osc.frequency.value = 880;
      osc.start();
      osc.stop(ctx.currentTime + 0.2);
    };
  }
});
