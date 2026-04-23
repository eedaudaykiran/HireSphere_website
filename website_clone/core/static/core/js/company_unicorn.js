// ========== CAROUSEL SCRIPT ==========
const track = document.getElementById('track');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const cardWidth = 214;
let currentIndex = 0;

function getVisibleCount() {
    const outerWidth = document.getElementById('trackOuter').offsetWidth;
    return Math.floor(outerWidth / cardWidth);
}

function totalCards() {
    return track.children.length;
}

function slide(dir) {
    const visible = getVisibleCount();
    const maxIndex = Math.max(0, totalCards() - visible);
    currentIndex = Math.min(Math.max(currentIndex + dir, 0), maxIndex);
    track.style.transform = `translateX(-${currentIndex * cardWidth}px)`;
    prevBtn.disabled = currentIndex === 0;
    nextBtn.disabled = currentIndex >= maxIndex;
}

function selectCard(el) {
    document.querySelectorAll('.card').forEach(card => {
        card.classList.remove('active');
        const badge = card.querySelector('.check-badge');
        if (badge) badge.remove();
    });
    el.classList.add('active');
    const badge = document.createElement('div');
    badge.className = 'check-badge';
    badge.innerHTML = `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 13l4 4L19 7" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    el.appendChild(badge);
}

window.addEventListener('resize', () => {
    currentIndex = 0;
    track.style.transform = 'translateX(0)';
    prevBtn.disabled = true;
    nextBtn.disabled = false;
});

setTimeout(() => { slide(0); }, 100);

// ========== FILTER SCRIPTS ==========
const activeFilters = {
    type: new Set(),
    location: new Set(),
    industry: new Set(),
    department: new Set(),
    experience: new Set(),
    nature: new Set(),
    date: new Set()
};

function applyFilters() {
    const cards = document.querySelectorAll('.company-card');
    let visible = 0;
    let totalActive = 0;
    for (const key in activeFilters) totalActive += activeFilters[key].size;
    document.getElementById('applied-count').textContent = totalActive > 0 ? `Applied (${totalActive})` : 'Applied (0)';

    cards.forEach(card => {
        const cardType = card.dataset.type || '';
        const cardIndustry = card.dataset.industry || '';
        const cardTags = card.dataset.tags || '';
        let show = true;

        if (activeFilters.type.size > 0) {
            const match = [...activeFilters.type].some(v => cardType.includes(v) || cardTags.includes(v));
            if (!match) show = false;
        }
        if (activeFilters.industry.size > 0) {
            const match = [...activeFilters.industry].some(v => cardIndustry.includes(v) || cardTags.includes(v));
            if (!match) show = false;
        }
        // Additional filters (location, department, etc.) can be added similarly

        if (show) {
            card.classList.remove('hidden');
            visible++;
        } else {
            card.classList.add('hidden');
        }
    });
    document.getElementById('showing-count').textContent = `Showing ${visible} compan${visible === 1 ? 'y' : 'ies'}`;
}

// Checkbox filters
document.querySelectorAll('input[type="checkbox"][data-filter]').forEach(cb => {
    cb.addEventListener('change', () => {
        const key = cb.dataset.filter;
        if (cb.checked) activeFilters[key].add(cb.value);
        else activeFilters[key].delete(cb.value);
        applyFilters();
    });
});

// Pill filters
function togglePill(pill) {
    const key = pill.dataset.filter;
    const val = pill.dataset.value;
    pill.classList.toggle('active');
    if (pill.classList.contains('active')) activeFilters[key].add(val);
    else activeFilters[key].delete(val);
    applyFilters();
}

// Section collapse
function toggleSection(titleEl) {
    titleEl.classList.toggle('collapsed');
    const body = titleEl.nextElementSibling;
    if (titleEl.classList.contains('collapsed')) {
        body.style.maxHeight = '0';
        body.classList.add('collapsed');
    } else {
        body.style.maxHeight = body.scrollHeight + 'px';
        body.classList.remove('collapsed');
    }
}

// Initialize max-heights for smooth collapse
document.querySelectorAll('.filter-section-body').forEach(body => {
    body.style.maxHeight = body.scrollHeight + 'px';
});

// Search within filter lists
function filterList(input, listId) {
    const q = input.value.toLowerCase();
    const list = document.getElementById(listId);
    list.querySelectorAll('.filter-option').forEach(opt => {
        const label = opt.querySelector('.label').textContent.toLowerCase();
        opt.style.display = label.includes(q) ? '' : 'none';
    });
}

// Clear all filters
function clearAllFilters() {
    for (const key in activeFilters) activeFilters[key].clear();
    document.querySelectorAll('input[type="checkbox"][data-filter]').forEach(cb => cb.checked = false);
    document.querySelectorAll('.pill.active').forEach(p => p.classList.remove('active'));
    applyFilters();
}

// ========== PAGINATION (UI only, scrolls to top) ==========
let currentPage = 1;
const totalPages = 3;

function changePage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;

    document.getElementById('page-label-current').textContent = currentPage;

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.getElementById('btn-p' + i);
        if (btn) btn.classList.toggle('active', i === currentPage);
    }

    const prevBtnPage = document.getElementById('btn-prev');
    const nextBtnPage = document.getElementById('btn-next');
    if (prevBtnPage) prevBtnPage.classList.toggle('disabled', currentPage === 1);
    if (nextBtnPage) nextBtnPage.classList.toggle('disabled', currentPage === totalPages);

    // Smooth scroll to the top of the company listings
    document.getElementById('col2').scrollIntoView({ behavior: 'smooth', block: 'start' });
}