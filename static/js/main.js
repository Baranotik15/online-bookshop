document.addEventListener('DOMContentLoaded', () => {

    // ─── Profile dropdown ─────────────────────────────────────
    const profileMenu = document.getElementById('profileMenu');
    if (profileMenu) {
        const dropdown = profileMenu.querySelector('.profile-dropdown');
        profileMenu.addEventListener('click', e => {
            e.stopPropagation();
            dropdown.classList.toggle('open');
        });
        document.addEventListener('click', () => dropdown.classList.remove('open'));
    }

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
        toast.classList.remove('show');
        void toast.offsetWidth;
        toast.classList.add('show');
    }

    // ─── Cart count ───────────────────────────────────────────
    const cartCount = document.getElementById('cartCount');
    const cartSum   = document.getElementById('cartSum');

    function updateCartCount(n) {
        if (cartCount) cartCount.textContent = n;
    }

    function updateCartSum(total) {
        if (!cartSum) return;
        const n = parseFloat(total);
        cartSum.textContent = n > 0 ? Math.round(n) + ' ₴' : '';
    }

    if (cartCount) {
        fetch('/api/cart/')
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (data) {
                    updateCartCount(data.items.length);
                    updateCartSum(data.total_price);
                }
            })
            .catch(() => {});
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
            updateCartSum(data.total_price);
            showToast('Додано до кошика ✓');
        } catch {
            showToast('Помилка з\'єднання', true);
        }
    }

    // ─── Fuzzy search ─────────────────────────────────────────
    function levenshtein(a, b) {
        const m = a.length, n = b.length;
        const prev = Array.from({length: n + 1}, (_, j) => j);
        const curr = new Array(n + 1);
        for (let i = 1; i <= m; i++) {
            curr[0] = i;
            for (let j = 1; j <= n; j++) {
                curr[j] = a[i-1] === b[j-1]
                    ? prev[j-1]
                    : 1 + Math.min(prev[j], curr[j-1], prev[j-1]);
            }
            prev.splice(0, n + 1, ...curr);
        }
        return prev[n];
    }

    function fuzzyScore(query, title) {
        const q = query.toLowerCase().trim();
        const t = title.toLowerCase();
        if (!q) return 100;
        if (t.includes(q)) return 100;

        const qWords = q.split(/\s+/).filter(Boolean);
        const tWords = t.split(/\s+/).filter(Boolean);
        let total = 0;

        for (const qw of qWords) {
            let best = 0;
            for (const tw of tWords) {
                if (tw === qw)         { best = 100; break; }
                if (tw.startsWith(qw)) { best = Math.max(best, 85); continue; }
                if (tw.includes(qw))   { best = Math.max(best, 70); continue; }

                const dist = levenshtein(qw, tw);
                const maxDist = Math.max(qw.length, tw.length) <= 4 ? 1
                              : Math.max(qw.length, tw.length) <= 7 ? 2
                              : 3;
                if (dist <= maxDist) best = Math.max(best, Math.max(10, 65 - dist * 15));

                if (qw.length >= 3) {
                    const sub = tw.slice(0, qw.length);
                    const subDist = levenshtein(qw, sub);
                    if (subDist <= 1) best = Math.max(best, 60);
                }
            }
            if (best === 0) return 0;
            total += best;
        }
        return total / qWords.length;
    }

    const searchInput  = document.getElementById('searchInput');
    const bookCount    = document.getElementById('bookCount');
    const allCards     = document.querySelectorAll('.book-card');
    const PAGE_SIZE    = 12;
    let currentPage    = 1;
    let matchingCards  = [];
    const priceMinEl   = document.getElementById('priceMin');
    const priceMaxEl   = document.getElementById('priceMax');
    const priceMinVal  = document.getElementById('priceMinVal');
    const priceMaxVal  = document.getElementById('priceMaxVal');
    const rangeFill    = document.getElementById('rangeFill');
    const activeGenres  = new Set();
    const genreTagsContainer = document.getElementById('genreTags');

    function attachGenreTag(tag) {
        tag.addEventListener('click', () => {
            const id = tag.dataset.genreId;
            if (activeGenres.has(id)) { activeGenres.delete(id); tag.classList.remove('active'); }
            else                      { activeGenres.add(id);    tag.classList.add('active'); }
            applyFilters();
        });
    }

    if (genreTagsContainer) {
        fetch('/api/genres/')
            .then(r => r.ok ? r.json() : [])
            .then(data => {
                const genres = Array.isArray(data) ? data : (data.results || []);
                genres.forEach(g => {
                    const btn = document.createElement('button');
                    btn.className = 'genre-tag';
                    btn.dataset.genreId = String(g.id);
                    btn.textContent = g.name;
                    attachGenreTag(btn);
                    genreTagsContainer.appendChild(btn);
                });
            })
            .catch(() => {});
    }

    const authorDropdown = document.getElementById('authorDropdown');
    const authorDropdownBtn = document.getElementById('authorDropdownBtn');
    const authorDropdownMenu = document.getElementById('authorDropdownMenu');
    const authorSearchEl = document.getElementById('authorSearch');
    const authorDropdownLabel = document.getElementById('authorDropdownLabel');

    if (priceMinEl && allCards.length) {
        const prices    = Array.from(allCards).map(c => parseFloat(c.dataset.price));
        const globalMin = Math.floor(Math.min(...prices));
        const globalMax = Math.ceil(Math.max(...prices));

        [priceMinEl, priceMaxEl].forEach(el => {
            el.min = globalMin; el.max = globalMax;
        });
        priceMinEl.value = globalMin;
        priceMaxEl.value = globalMax;
        priceMinVal.textContent = globalMin;
        priceMaxVal.textContent = globalMax;
        rangeFill.style.left  = '0%';
        rangeFill.style.width = '100%';
    }

    function getSelectedAuthors() {
        if (!authorDropdown) return new Set();
        return new Set(
            Array.from(authorDropdown.querySelectorAll('input[type="checkbox"]:checked'))
                 .map(cb => cb.value)
        );
    }

    function updateAuthorLabel() {
        const selected = getSelectedAuthors();
        authorDropdownLabel.textContent = selected.size === 0
            ? 'Усі автори'
            : selected.size === 1
                ? authorDropdown.querySelector(`input[value="${[...selected][0]}"]+*`)?.textContent.trim()
                  ?? `1 автор`
                : `${selected.size} автори`;
    }

    function applyFilters() {
        const q       = searchInput ? searchInput.value.trim() : '';
        const min     = priceMinEl ? parseFloat(priceMinEl.value) : 0;
        const max     = priceMaxEl ? parseFloat(priceMaxEl.value) : Infinity;
        const authors = getSelectedAuthors();
        matchingCards = [];
        allCards.forEach(card => {
            const score = fuzzyScore(q, card.dataset.title);
            const price = parseFloat(card.dataset.price);
            const cardGenres = new Set(card.dataset.genres ? card.dataset.genres.split(',') : []);
            const match = score > 0 && price >= min && price <= max
                       && (authors.size === 0 || authors.has(card.dataset.authorId))
                       && (activeGenres.size === 0 || [...activeGenres].every(g => cardGenres.has(g)));
            if (match) matchingCards.push(card);
            else card.style.display = 'none';
        });
        if (bookCount) bookCount.textContent = matchingCards.length + ' книг';
        renderPage(1);
    }

    function renderPage(page) {
        currentPage = page;
        const start = (page - 1) * PAGE_SIZE;
        const end   = start + PAGE_SIZE;
        matchingCards.forEach((card, i) => {
            card.style.display = (i >= start && i < end) ? '' : 'none';
        });
        renderPagination();
    }

    function renderPagination() {
        const container = document.getElementById('pagination');
        if (!container) return;
        const totalPages = Math.ceil(matchingCards.length / PAGE_SIZE);
        container.innerHTML = '';
        if (totalPages <= 1) return;

        const prev = document.createElement('button');
        prev.className = 'page-btn';
        prev.innerHTML = '&larr;';
        prev.disabled = currentPage === 1;
        prev.addEventListener('click', () => renderPage(currentPage - 1));
        container.appendChild(prev);

        for (let i = 1; i <= totalPages; i++) {
            const btn = document.createElement('button');
            btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
            btn.textContent = i;
            const p = i;
            btn.addEventListener('click', () => renderPage(p));
            container.appendChild(btn);
        }

        const next = document.createElement('button');
        next.className = 'page-btn';
        next.innerHTML = '&rarr;';
        next.disabled = currentPage === totalPages;
        next.addEventListener('click', () => renderPage(currentPage + 1));
        container.appendChild(next);
    }

    function updateSlider() {
        let min = parseFloat(priceMinEl.value);
        let max = parseFloat(priceMaxEl.value);
        if (min > max) { priceMinEl.value = max; min = max; }
        if (max < min) { priceMaxEl.value = min; max = min; }
        const globalMin = parseFloat(priceMinEl.min);
        const globalMax = parseFloat(priceMinEl.max);
        const pct1 = (min - globalMin) / (globalMax - globalMin) * 100;
        const pct2 = (max - globalMin) / (globalMax - globalMin) * 100;
        rangeFill.style.left  = pct1 + '%';
        rangeFill.style.width = (pct2 - pct1) + '%';
        priceMinVal.textContent = Math.round(min);
        priceMaxVal.textContent = Math.round(max);
        applyFilters();
    }

    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (priceMinEl)  priceMinEl.addEventListener('input', updateSlider);
    if (priceMaxEl)  priceMaxEl.addEventListener('input', updateSlider);

    if (authorDropdown) {
        const authorClearBtn = document.getElementById('authorClearBtn');

        function updateClearBtn() {
            const hasChecked = authorDropdown.querySelectorAll('input[type="checkbox"]:checked').length > 0;
            authorClearBtn.style.display = hasChecked ? '' : 'none';
        }

        authorDropdownBtn.addEventListener('click', e => {
            e.stopPropagation();
            authorDropdown.classList.toggle('open');
        });
        document.addEventListener('click', e => {
            if (!authorDropdown.contains(e.target)) authorDropdown.classList.remove('open');
        });
        authorSearchEl.addEventListener('input', () => {
            const q = authorSearchEl.value.toLowerCase();
            authorDropdown.querySelectorAll('.author-option').forEach(opt => {
                opt.style.display = opt.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        });
        authorClearBtn.addEventListener('click', () => {
            authorDropdown.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            updateAuthorLabel();
            updateClearBtn();
            applyFilters();
        });
        authorDropdown.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', () => {
                updateAuthorLabel();
                updateClearBtn();
                applyFilters();
            });
        });
    }

    if (allCards.length) applyFilters();

    // ─── Book modal ───────────────────────────────────────────
    const overlay   = document.getElementById('bookModal');
    if (!overlay) return;

    const closeBtn  = document.getElementById('modalClose');
    const cover     = document.getElementById('modalCover');
    const titleEl   = document.getElementById('modalTitle');
    const authorEl  = document.getElementById('modalAuthor');
    const priceEl   = document.getElementById('modalPrice');
    const stockEl   = document.getElementById('modalStock');
    const genresEl  = document.getElementById('modalGenres');
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

        if (genresEl) {
            const names = card.dataset.genreNames ? card.dataset.genreNames.split(',') : [];
            genresEl.innerHTML = names.map(n => `<span class="modal-genre-tag">${n.trim()}</span>`).join('');
        }

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
