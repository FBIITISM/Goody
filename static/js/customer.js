// Goody Customer JavaScript

const CART_KEY = 'goody_cart';

function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY) || '[]');
  } catch (e) {
    return [];
  }
}

function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  window.dispatchEvent(new Event('storage'));
  document.dispatchEvent(new CustomEvent('cartUpdated'));
}

function addToCart(id, name, price) {
  const cart = getCart();
  const existing = cart.find(i => i.id === id);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ id: id, name: name, price: parseFloat(price), qty: 1 });
  }
  saveCart(cart);
  updateCartBadge();
  showAddedToast(name);
}

function updateCartBadge() {
  try {
    const cart = getCart();
    const total = cart.reduce((s, i) => s + i.qty, 0);
    document.querySelectorAll('.cart-count').forEach(el => {
      if (total > 0) {
        el.textContent = total;
        el.classList.remove('d-none');
      } else {
        el.classList.add('d-none');
      }
    });
  } catch (e) {}
}

function showAddedToast(name) {
  const existing = document.getElementById('addToast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'addToast';
  toast.style.cssText = 'position:fixed;bottom:80px;right:20px;z-index:9999;';
  toast.innerHTML = `
    <div class="toast show align-items-center text-white bg-success border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body">✅ <strong>${name}</strong> added to cart!</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
      </div>
    </div>
  `;
  document.body.appendChild(toast);
  setTimeout(() => { if (toast.parentNode) toast.remove(); }, 2000);
}

// Attach click handlers to all Add to Cart buttons
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      addToCart(
        parseInt(this.dataset.id),
        this.dataset.name,
        parseFloat(this.dataset.price)
      );
    });
  });
  updateCartBadge();
});
