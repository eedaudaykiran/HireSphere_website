document.addEventListener("DOMContentLoaded", function () {

    /* =========================================
       1) ROLES SLIDER
    ========================================= */
    const rolesSlider = document.getElementById("rolesSlider");
    const rolesNextBtn = document.getElementById("nextBtn");
    const roleDots = document.querySelectorAll(".dot");

    let rolesIndex = 0;
    const totalRoleSlides = 2;

    function updateRolesSlider() {
        if (!rolesSlider) return;
        rolesSlider.style.transform = `translateX(-${rolesIndex * 100}%)`;

        roleDots.forEach(dot => dot.classList.remove("active"));
        if (roleDots[rolesIndex]) {
            roleDots[rolesIndex].classList.add("active");
        }
    }

    if (rolesNextBtn && rolesSlider) {
        rolesNextBtn.addEventListener("click", function () {
            rolesIndex++;
            if (rolesIndex >= totalRoleSlides) {
                rolesIndex = 0;
            }
            updateRolesSlider();
        });
    }

    roleDots.forEach(dot => {
        dot.addEventListener("click", function () {
            rolesIndex = parseInt(this.getAttribute("data-slide"));
            updateRolesSlider();
        });
    });

    updateRolesSlider();


    /* =========================================
       2) SPONSORED TAGS ACTIVE STATE
    ========================================= */
    const sponsoredTags = document.querySelectorAll(".sponsored-tag");

    sponsoredTags.forEach(tag => {
        tag.addEventListener("click", function (e) {
            e.preventDefault();
            sponsoredTags.forEach(item => item.classList.remove("active"));
            this.classList.add("active");
        });
    });


    /* =========================================
       3) UPCOMING EVENTS SLIDER
    ========================================= */
    const eventsTrack = document.getElementById("eventsTrack");
    const eventsNextBtn = document.getElementById("eventsNextBtn");

    if (eventsTrack && eventsNextBtn) {
        let offset = 0;
        const cardWidth = 320; // 300 card + 20 gap

        function getMaxOffset() {
            const visibleWidth = eventsTrack.parentElement.offsetWidth;
            const totalWidth = eventsTrack.scrollWidth;
            return Math.max(0, totalWidth - visibleWidth);
        }

        eventsNextBtn.addEventListener("click", function () {
            if (offset + cardWidth >= getMaxOffset()) {
                offset = 0;
            } else {
                offset += cardWidth;
            }

            eventsTrack.style.transform = `translateX(-${offset}px)`;
        });
    }


    /* =========================================
       4) SPONSORED COMPANY CAROUSEL
       (8 cards per page, 3 pages)
    ========================================= */
    const companiesData = [
        {
            name: "ESolutionsFirst",
            rating: 4.0,
            reviews: "2",
            tags: ["IT Services & Consulting"],
            bg: "#fff5f5",
            color: "#c0392b",
            letter: "E"
        },
        {
            name: "Hexaware Technologies",
            rating: 3.4,
            reviews: "7.6K+",
            tags: ["B2B", "Corporate", "Fortune India 500 (2023)"],
            bg: "#eaf4fb",
            color: "#2980b9",
            letter: "H"
        },
        {
            name: "DTCC",
            rating: 3.8,
            reviews: "112",
            tags: ["Private", "B2B", "Foreign MNC", "Financial Services"],
            bg: "#e8f8f0",
            color: "#1a7a4a",
            letter: "D"
        },
        {
            name: "Toast",
            rating: 4.1,
            reviews: "99",
            tags: ["Software Product", "FinTech / Payments"],
            bg: "#fff8f0",
            color: "#e67e22",
            letter: "T"
        },
        {
            name: "Tieto",
            rating: 4.1,
            reviews: "1.4K+",
            tags: ["Software Product", "IT Services & Consulting", "B2B"],
            bg: "#fffde7",
            color: "#f9a825",
            letter: "Ti"
        },
        {
            name: "Hetero",
            rating: 3.9,
            reviews: "4.5K+",
            tags: ["Medical Services / Hospital", "Clinical Research / Contract Research"],
            bg: "#fce4ec",
            color: "#c2185b",
            letter: "H"
        },
        {
            name: "Vertafore",
            rating: 3.8,
            reviews: "191",
            tags: ["Product", "B2B", "Foreign MNC", "Private", "IT Services & Consulting"],
            bg: "#fef3e2",
            color: "#e65100",
            letter: "V"
        },
        {
            name: "Britannia",
            rating: 4.0,
            reviews: "2.8K+",
            tags: ["Conglomerate", "B2B", "Corporate", "FMCG", "Fortune India 500"],
            bg: "#fce4e4",
            color: "#b71c1c",
            letter: "B"
        },

        {
            name: "Infosys",
            rating: 3.7,
            reviews: "55K+",
            tags: ["IT Services & Consulting", "B2B", "Fortune India 500"],
            bg: "#e3f2fd",
            color: "#0d47a1",
            letter: "I"
        },
        {
            name: "Wipro",
            rating: 3.6,
            reviews: "42K+",
            tags: ["IT Services & Consulting", "B2B"],
            bg: "#e8f5e9",
            color: "#2e7d32",
            letter: "W"
        },
        {
            name: "TCS",
            rating: 3.8,
            reviews: "80K+",
            tags: ["IT Services & Consulting", "B2B", "Corporate"],
            bg: "#ede7f6",
            color: "#4527a0",
            letter: "T"
        },
        {
            name: "HCL Tech",
            rating: 3.9,
            reviews: "30K+",
            tags: ["IT Services & Consulting", "B2B", "Fortune India 500"],
            bg: "#e0f7fa",
            color: "#00695c",
            letter: "H"
        },
        {
            name: "Zoho",
            rating: 4.2,
            reviews: "12K+",
            tags: ["Software Product", "SaaS"],
            bg: "#fff3e0",
            color: "#ef6c00",
            letter: "Z"
        },
        {
            name: "Accenture",
            rating: 4.0,
            reviews: "65K+",
            tags: ["Consulting", "Corporate"],
            bg: "#f3e5f5",
            color: "#6a1b9a",
            letter: "A"
        },
        {
            name: "Cognizant",
            rating: 3.9,
            reviews: "48K+",
            tags: ["IT Services", "B2B"],
            bg: "#e8f5e9",
            color: "#1b5e20",
            letter: "C"
        },
        {
            name: "Capgemini",
            rating: 3.8,
            reviews: "27K+",
            tags: ["Corporate", "Technology"],
            bg: "#e3f2fd",
            color: "#1565c0",
            letter: "C"
        },

        {
            name: "IBM",
            rating: 4.1,
            reviews: "20K+",
            tags: ["Technology", "Enterprise"],
            bg: "#e8eaf6",
            color: "#283593",
            letter: "I"
        },
        {
            name: "Oracle",
            rating: 4.0,
            reviews: "18K+",
            tags: ["Software Product", "Enterprise"],
            bg: "#ffebee",
            color: "#c62828",
            letter: "O"
        },
        {
            name: "Adobe",
            rating: 4.4,
            reviews: "14K+",
            tags: ["Software Product", "Creative Tech"],
            bg: "#fff3e0",
            color: "#e65100",
            letter: "A"
        },
        {
            name: "SAP",
            rating: 4.2,
            reviews: "16K+",
            tags: ["Enterprise", "Product"],
            bg: "#e1f5fe",
            color: "#0277bd",
            letter: "S"
        },
        {
            name: "Flipkart",
            rating: 4.0,
            reviews: "22K+",
            tags: ["E-commerce", "Product"],
            bg: "#fffde7",
            color: "#f9a825",
            letter: "F"
        },
        {
            name: "Tech Mahindra",
            rating: 3.8,
            reviews: "26K+",
            tags: ["IT Services", "Corporate"],
            bg: "#ede7f6",
            color: "#5e35b1",
            letter: "T"
        },
        {
            name: "Mindtree",
            rating: 3.9,
            reviews: "10K+",
            tags: ["Technology", "Corporate"],
            bg: "#f1f8e9",
            color: "#558b2f",
            letter: "M"
        },
        {
            name: "Deloitte",
            rating: 4.1,
            reviews: "24K+",
            tags: ["Consulting", "Corporate"],
            bg: "#f1f8e9",
            color: "#2e7d32",
            letter: "D"
        }
    ];

    const PER_PAGE = 8;
    let companyPage = 0;
    const totalCompanyPages = Math.ceil(companiesData.length / PER_PAGE);

    const companiesGrid = document.getElementById("companiesGrid");
    const companyNextBtn = document.getElementById("companyNextBtn");
    const companyPrevBtn = document.getElementById("companyPrevBtn");

    function getStars(rating) {
        return `<span style="color:#f4b400;">★</span>`;
    }

    function renderCompanies() {
        if (!companiesGrid) return;

        const start = companyPage * PER_PAGE;
        const end = start + PER_PAGE;
        const currentCompanies = companiesData.slice(start, end);

        companiesGrid.innerHTML = currentCompanies.map(company => `
            <div class="company-card">
                <div class="logo-wrap" style="background:${company.bg};">
                    <span class="logo-text" style="color:${company.color};">${company.letter}</span>
                </div>

                <h3 class="company-name">${company.name}</h3>

                <p class="rating-row">
                    ${getStars(company.rating)}
                    <span class="rating-value">${company.rating}</span>
                    <span class="review-text">${company.reviews} reviews</span>
                </p>

                <div class="tags-wrap">
                    ${company.tags.map(tag => `<span class="tag">${tag}</span>`).join("")}
                </div>
            </div>
        `).join("");

        if (companyPrevBtn) {
            companyPrevBtn.disabled = companyPage === 0;
        }

        if (companyNextBtn) {
            companyNextBtn.disabled = companyPage === totalCompanyPages - 1;
        }
    }

    if (companyNextBtn) {
        companyNextBtn.addEventListener("click", function () {
            if (companyPage < totalCompanyPages - 1) {
                companyPage++;
                renderCompanies();
            }
        });
    }

    if (companyPrevBtn) {
        companyPrevBtn.addEventListener("click", function () {
            if (companyPage > 0) {
                companyPage--;
                renderCompanies();
            }
        });
    }

    renderCompanies();

});

// ========== Sponsored Tags Active State ==========
const sponsoredTags = document.querySelectorAll(".sponsored-tag");
sponsoredTags.forEach(tag => {
    tag.addEventListener("click", function (e) {
        e.preventDefault();
        sponsoredTags.forEach(item => item.classList.remove("active"));
        this.classList.add("active");
    });
});

// ========== Upcoming Events Slider ==========
const eventsTrack = document.getElementById('eventsTrack');
const eventsNextBtn = document.getElementById('eventsNextBtn');

if (eventsTrack && eventsNextBtn) {
    const cardWidth = 300 + 20; // card width (300px) + gap (20px)
    let offset = 0;

    function getMaxOffset() {
        const visible = eventsTrack.parentElement.offsetWidth;
        const total = eventsTrack.scrollWidth;
        return Math.max(0, total - visible);
    }

    eventsNextBtn.addEventListener('click', () => {
        // Move by one card width; if at end, reset to 0
        if (offset + cardWidth >= getMaxOffset()) {
            offset = 0;
        } else {
            offset += cardWidth;
        }
        eventsTrack.style.transform = `translateX(-${offset}px)`;
        // Optional: change arrow icon (optional, but keeps original behavior)
        eventsNextBtn.textContent = offset === 0 ? '›' : '‹';
    });
}

// ========== Company Carousel (8 items per page) ==========
const companiesData = [
    {
        name: "ESolutionsFirst",
        rating: 4.0,
        reviews: "2",
        tags: ["IT Services & Consulting"],
        bg: "#fff5f5",
        color: "#c0392b",
        letter: "E",
    },
    {
        name: "Hexaware Technologies",
        rating: 3.4,
        reviews: "7.6K+",
        tags: ["B2B", "Corporate", "Fortune India 500 (2023)"],
        bg: "#eaf4fb",
        color: "#2980b9",
        letter: "H",
    },
    {
        name: "DTCC",
        rating: 3.8,
        reviews: "112",
        tags: ["Private", "B2B", "Foreign MNC", "Financial Services"],
        bg: "#e8f8f0",
        color: "#1a7a4a",
        letter: "D",
    },
    {
        name: "Toast",
        rating: 4.1,
        reviews: "99",
        tags: ["Software Product", "FinTech / Payments"],
        bg: "#fff8f0",
        color: "#e67e22",
        letter: "T",
    },
    {
        name: "Tieto",
        rating: 4.1,
        reviews: "1.4K+",
        tags: ["Software Product", "IT Services & Consulting", "B2B"],
        bg: "#fffde7",
        color: "#f9a825",
        letter: "Ti",
    },
    {
        name: "Hetero",
        rating: 3.9,
        reviews: "4.5K+",
        tags: ["Medical Services / Hospital", "Clinical Research / Contract Research"],
        bg: "#fce4ec",
        color: "#c2185b",
        letter: "H",
    },
    {
        name: "Vertafore",
        rating: 3.8,
        reviews: "191",
        tags: ["Product", "B2B", "Foreign MNC", "Private", "IT Services & Consulting"],
        bg: "#fef3e2",
        color: "#e65100",
        letter: "V",
    },
    {
        name: "Britannia",
        rating: 4.0,
        reviews: "2.8K+",
        tags: ["Conglomerate", "B2B", "Corporate", "FMCG", "Fortune India 500"],
        bg: "#fce4e4",
        color: "#b71c1c",
        letter: "B",
    },
    {
        name: "Infosys",
        rating: 3.7,
        reviews: "55K+",
        tags: ["IT Services & Consulting", "B2B", "Fortune India 500"],
        bg: "#e3f2fd",
        color: "#0d47a1",
        letter: "I",
    },
    {
        name: "Wipro",
        rating: 3.6,
        reviews: "42K+",
        tags: ["IT Services & Consulting", "B2B"],
        bg: "#e8f5e9",
        color: "#2e7d32",
        letter: "W",
    },
    {
        name: "TCS",
        rating: 3.8,
        reviews: "80K+",
        tags: ["IT Services & Consulting", "B2B", "Corporate"],
        bg: "#ede7f6",
        color: "#4527a0",
        letter: "T",
    },
    {
        name: "HCL Tech",
        rating: 3.9,
        reviews: "30K+",
        tags: ["IT Services & Consulting", "B2B", "Fortune India 500"],
        bg: "#e0f7fa",
        color: "#00695c",
        letter: "H",
    },
    {
        name: "ESolutionsFirst",
        rating: 4.0,
        reviews: "2",
        tags: ["IT Services & Consulting"],
        bg: "#fff5f5",
        color: "#c0392b",
        letter: "E",
    },
    {
        name: "Hexaware Technologies",
        rating: 3.4,
        reviews: "7.6K+",
        tags: ["B2B", "Corporate", "Fortune India 500 (2023)"],
        bg: "#eaf4fb",
        color: "#2980b9",
        letter: "H",
    },
    {
        name: "DTCC",
        rating: 3.8,
        reviews: "112",
        tags: ["Private", "B2B", "Foreign MNC", "Financial Services"],
        bg: "#e8f8f0",
        color: "#1a7a4a",
        letter: "D",
    },
    {
        name: "Toast",
        rating: 4.1,
        reviews: "99",
        tags: ["Software Product", "FinTech / Payments"],
        bg: "#fff8f0",
        color: "#e67e22",
        letter: "T",
    },
    {
        name: "Tieto",
        rating: 4.1,
        reviews: "1.4K+",
        tags: ["Software Product", "IT Services & Consulting", "B2B"],
        bg: "#fffde7",
        color: "#f9a825",
        letter: "Ti",
    },
    {
        name: "Hetero",
        rating: 3.9,
        reviews: "4.5K+",
        tags: ["Medical Services / Hospital", "Clinical Research / Contract Research"],
        bg: "#fce4ec",
        color: "#c2185b",
        letter: "H",
    },
    {
        name: "Vertafore",
        rating: 3.8,
        reviews: "191",
        tags: ["Product", "B2B", "Foreign MNC", "Private", "IT Services & Consulting"],
        bg: "#fef3e2",
        color: "#e65100",
        letter: "V",
    },
    {
        name: "Britannia",
        rating: 4.0,
        reviews: "2.8K+",
        tags: ["Conglomerate", "B2B", "Corporate", "FMCG", "Fortune India 500"],
        bg: "#fce4e4",
        color: "#b71c1c",
        letter: "B",
    },
    {
        name: "Infosys",
        rating: 3.7,
        reviews: "55K+",
        tags: ["IT Services & Consulting", "B2B", "Fortune India 500"],
        bg: "#e3f2fd",
        color: "#0d47a1",
        letter: "I",
    },
    {
        name: "Wipro",
        rating: 3.6,
        reviews: "42K+",
        tags: ["IT Services & Consulting", "B2B"],
        bg: "#e8f5e9",
        color: "#2e7d32",
        letter: "W",
    },
    {
        name: "TCS",
        rating: 3.8,
        reviews: "80K+",
        tags: ["IT Services & Consulting", "B2B", "Corporate"],
        bg: "#ede7f6",
        color: "#4527a0",
        letter: "T",
    },
    {
        name: "HCL Tech",
        rating: 3.9,
        reviews: "30K+",
        tags: ["IT Services & Consulting", "B2B", "Fortune India 500"],
        bg: "#e0f7fa",
        color: "#00695c",
        letter: "H",
    },
];

const PER_PAGE = 8; // 8 cards per page
let currentPage = 0;
const totalPages = Math.ceil(companiesData.length / PER_PAGE);

function starHtml(rating) {
    const full = Math.floor(rating);
    let html = '';
    for (let i = 0; i < 5; i++) {
        html += `<span style="color:${i < full ? '#f59e0b' : '#d1d5db'}; font-size:.9rem;">★</span>`;
    }
    return html;
}

function renderCarouselCards() {
    const grid = document.getElementById('companiesGrid');
    if (!grid) return;
    const start = currentPage * PER_PAGE;
    const slice = companiesData.slice(start, start + PER_PAGE);

    grid.innerHTML = slice.map((c, i) => `
        <div class="company-card" style="animation-delay:${(i * 0.05) + 0.05}s">
            <div class="logo-wrap" style="background:${c.bg}">
                <span class="logo-text" style="color:${c.color}">${c.letter}</span>
            </div>
            <div class="company-name">${c.name}</div>
            <div class="rating-row">
                ${starHtml(c.rating)}
                <span class="rating-value">${c.rating}</span>
                <span class="divider-dot">|</span>
                <span>${c.reviews} reviews</span>
            </div>
            <div class="tags-wrap">
                ${c.tags.map(t => `<span class="tag">${t}</span>`).join('')}
            </div>
        </div>
    `).join('');

    const prevBtn = document.getElementById('companyPrevBtn');
    const nextBtn = document.getElementById('companyNextBtn');
    if (prevBtn) prevBtn.disabled = currentPage === 0;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages - 1;
}

function slideCarousel(dir) {
    currentPage = Math.max(0, Math.min(totalPages - 1, currentPage + dir));
    renderCarouselCards();
}

// Initialize carousel when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const prevBtn = document.getElementById('companyPrevBtn');
    const nextBtn = document.getElementById('companyNextBtn');
    if (prevBtn) prevBtn.addEventListener('click', () => slideCarousel(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => slideCarousel(1));
    renderCarouselCards();
});

console.log("Django Naukri Clone Loaded");




