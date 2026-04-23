console.log("Naukri Clone Home Page Loaded");

// =========================
// SEARCH BUTTON
// =========================
const searchBtn = document.querySelector(".search-btn");

if (searchBtn) {
    searchBtn.addEventListener("click", function () {
        alert("Search feature will be connected with Django backend later.");
    });
}

// =========================
// TOP COMPANIES CAROUSEL
// =========================
const topRow = document.getElementById("topCompaniesRow");
const topPrevBtn = document.getElementById("topPrevBtn");
const topNextBtn = document.getElementById("topNextBtn");

if (topRow && topPrevBtn && topNextBtn) {
    const scrollAmount = 300;

    topPrevBtn.addEventListener("click", () => {
        topRow.scrollBy({
            left: -scrollAmount,
            behavior: "smooth"
        });
    });

    topNextBtn.addEventListener("click", () => {
        topRow.scrollBy({
            left: scrollAmount,
            behavior: "smooth"
        });
    });
}

// =========================
// FEATURED COMPANIES CAROUSEL
// =========================
const featuredRow = document.getElementById("featuredRow");
const featuredPrevBtn = document.getElementById("featuredPrevBtn");
const featuredNextBtn = document.getElementById("featuredNextBtn");

if (featuredRow && featuredPrevBtn && featuredNextBtn) {
    const featuredScrollAmount = 300;

    featuredPrevBtn.addEventListener("click", () => {
        featuredRow.scrollBy({
            left: -featuredScrollAmount,
            behavior: "smooth"
        });
    });

    featuredNextBtn.addEventListener("click", () => {
        featuredRow.scrollBy({
            left: featuredScrollAmount,
            behavior: "smooth"
        });
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const jobCategoryRow = document.getElementById("jobCategoryRow");
    const categoryNextBtn = document.getElementById("categoryNextBtn");
    const categoryPrevBtn = document.getElementById("categoryPrevBtn");

    if (jobCategoryRow && categoryNextBtn && categoryPrevBtn) {

        categoryNextBtn.addEventListener("click", function () {
            jobCategoryRow.scrollBy({
                left: 320,
                behavior: "smooth"
            });
        });

        categoryPrevBtn.addEventListener("click", function () {
            jobCategoryRow.scrollBy({
                left: -320,
                behavior: "smooth"
            });
        });

    }
});

console.log("Remote Jobs Page Loaded");

// Save button click
const saveButtons = document.querySelectorAll(".save-btn");

saveButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
        if (btn.innerHTML.includes("Save")) {
            btn.innerHTML = "✅ Saved";
        } else {
            btn.innerHTML = "🔖 Save";
        }
    });
});

// Job title click
const jobTitles = document.querySelectorAll(".job-title");

jobTitles.forEach((title) => {
    title.addEventListener("click", function () {
        alert("Job details page will connect later with Django backend.");
    });
});

// Sort button click
const sortBtn = document.querySelector(".sort-btn");

if (sortBtn) {
    sortBtn.addEventListener("click", function () {
        alert("Sort feature will be added later.");
    });
}

const workModeBtn = document.getElementById("workModeBtn");
const workModeOptions = document.getElementById("workModeOptions");
const arrowIcon = document.getElementById("arrowIcon");

if (workModeBtn) {
    workModeBtn.addEventListener("click", function () {
        if (workModeOptions.style.display === "none") {
            workModeOptions.style.display = "block";
            arrowIcon.innerHTML = "&#8963;";
        } else {
            workModeOptions.style.display = "none";
            arrowIcon.innerHTML = "&#8964;";
        }
    });
}
