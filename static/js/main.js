document.addEventListener('DOMContentLoaded', () => {

    // ─── Active nav ───────────────────────────────────────────
    const path = window.location.pathname;
    document.querySelectorAll('nav a').forEach(link => {
        if (link.getAttribute('href') === path) link.classList.add('active');
    });

    // ─── Toast ────────────────────────────────────────────────
    const toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);

    function showToast(msg, isError = false) {
        toast.textContent = msg;
        toast.style.background = isError ? '#b91c1c' : '#1e293b';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2500);
    }

    // ─── Cart count ───────────────────────────────────────────
    const cartCount = document.getElementById('cartCount');

    function updateCartCount(n) {
        if (cartCount) cartCount.textContent = n;
    }

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? match[2] : null;
    }

    async function addToCart(bookId) {
        try {
            const res = await fetch('/api/cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ book_id: bookId, quantity: 1 }),
            });

            if (res.status === 403) { showToast('Увійдіть, щоб додати до кошика', true); return; }
            if (!res.ok) { showToast('Помилка сервера', true); return; }

            const data = await res.json();
            updateCartCount(data.total_items);
            showToast('Додано до кошика ✓');
        } catch {
            showToast('Помилка з\'єднання', true);
        }
    }

    // ─── Book modal ───────────────────────────────────────────
    const overlay   = document.getElementById('bookModal');
    if (!overlay) return;

    const closeBtn  = document.getElementById('modalClose');
    const cover     = document.getElementById('modalCover');
    const titleEl   = document.getElementById('modalTitle');
    const authorEl  = document.getElementById('modalAuthor');
    const priceEl   = document.getElementById('modalPrice');
    const stockEl   = document.getElementById('modalStock');
    const descEl    = document.getElementById('modalDescription');
    const addBtn    = document.getElementById('addToCart');

    let activeBookId = null;

    function openModal(card) {
        activeBookId = card.dataset.id;

        titleEl.textContent  = card.dataset.title;
        authorEl.textContent = 'Автор: ' + card.dataset.author;
        priceEl.textContent  = card.dataset.price + ' ₴';
        descEl.textContent   = card.dataset.description || '';

        const qty = parseInt(card.dataset.stock, 10);
        stockEl.innerHTML = qty > 0
            ? `<span class="stock-badge in-stock">&#10003; В наявності (${qty} шт.)</span>`
            : `<span class="stock-badge out-of-stock">&#10007; Немає в наявності</span>`;

        if (addBtn) addBtn.disabled = qty === 0;

        const img = card.dataset.image;
        cover.innerHTML = img
            ? `<img src="${img}" alt="${card.dataset.title}">`
            : `<span class="no-cover">📖</span>`;

        overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        overlay.classList.remove('open');
        document.body.style.overflow = '';
        activeBookId = null;
    }

    document.querySelectorAll('.book-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('.btn-cart')) return;
            openModal(card);
        });
    });

    document.querySelectorAll('.btn-cart').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            addToCart(btn.dataset.bookId);
        });
    });

    if (addBtn) {
        addBtn.addEventListener('click', () => {
            if (activeBookId) addToCart(activeBookId);
        });
    }

    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
});
