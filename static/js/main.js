// Custom PC Builder Global Client Script

document.addEventListener("DOMContentLoaded", function() {
    // 1. Lazy Image Loading
    const lazyImages = document.querySelectorAll("img.lazy");
    if ("IntersectionObserver" in window) {
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const image = entry.target;
                    image.src = image.dataset.src;
                    image.classList.add("loaded");
                    imageObserver.unobserve(image);
                }
            });
        });
        lazyImages.forEach(function(image) {
            imageObserver.observe(image);
        });
    } else {
        // Fallback for older browsers
        lazyImages.forEach(function(image) {
            image.src = image.dataset.src;
            image.classList.add("loaded");
        });
    }

    // 3. Search Autocomplete (AJAX powered)
    const searchInput = document.getElementById("global-search");
    const searchResults = document.getElementById("search-results-dropdown");

    if (searchInput && searchResults) {
        searchInput.addEventListener("input", function() {
            const query = searchInput.value.trim();
            if (query.length >= 2) {
                fetch(`/products/search-autocomplete/?term=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        searchResults.innerHTML = "";
                        if (data.length > 0) {
                            searchResults.style.display = "block";
                            data.forEach(item => {
                                const row = document.createElement("a");
                                row.href = item.url;
                                row.className = "dropdown-item d-flex align-items-center justify-content-between p-2";
                                row.innerHTML = `
                                    <div class="d-flex align-items-center">
                                        <img src="${item.image}" width="36" height="36" class="rounded me-2" style="object-fit:cover;">
                                        <span>${item.label}</span>
                                    </div>
                                    <span class="text-gradient fw-bold">${item.price}</span>
                                `;
                                searchResults.appendChild(row);
                            });
                        } else {
                            searchResults.style.display = "none";
                        }
                    });
            } else {
                searchResults.style.display = "none";
            }
        });

        // Hide search results on click outside
        document.addEventListener("click", function(e) {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = "none";
            }
        });
    }

    // 4. Voice Search Integration
    const voiceSearchBtn = document.getElementById("voice-search-btn");
    if (voiceSearchBtn) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            voiceSearchBtn.addEventListener("click", function() {
                voiceSearchBtn.classList.add("text-danger");
                recognition.start();
            });

            recognition.onresult = function(event) {
                const speechResult = event.results[0][0].transcript;
                if (searchInput) {
                    searchInput.value = speechResult;
                    // Trigger search submit or catalog filtering
                    const form = searchInput.closest("form");
                    if (form) {
                        form.submit();
                    }
                }
                voiceSearchBtn.classList.remove("text-danger");
            };

            recognition.onspeechend = function() {
                recognition.stop();
                voiceSearchBtn.classList.remove("text-danger");
            };

            recognition.onerror = function() {
                voiceSearchBtn.classList.remove("text-danger");
                Swal.fire({
                    icon: 'error',
                    title: 'Voice Search Error',
                    text: 'Speech recognition failed or was blocked. Try typing your search!'
                });
            };
        } else {
            // Disable or hide mic button if API is not supported in browser
            voiceSearchBtn.style.display = "none";
        }
    }

    // 5. Hide Skeleton Loaders
    const skeletons = document.querySelectorAll(".skeleton-container");
    skeletons.forEach(function(el) {
        el.style.display = "none";
    });
    
    const mainContent = document.querySelectorAll(".main-content-loaded");
    mainContent.forEach(function(el) {
        el.classList.remove("d-none");
    });

    // 6. Global Cart Add Interceptor (No Redirect, SweetAlert notification)
    document.body.addEventListener("submit", function(e) {
        const form = e.target;
        if (form && (form.action.includes("/cart/add/") || form.action.includes("/cart/add-build/"))) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const actionUrl = form.action;
            
            fetch(actionUrl, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": formData.get("csrfmiddlewaretoken")
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    Swal.fire({
                        icon: 'success',
                        title: 'Added to Cart!',
                        text: data.message,
                        timer: 2000,
                        showConfirmButton: false,
                        background: '#0f172a',
                        color: '#f8fafc'
                    });
                    
                    // Dynamically create or update cart count badge on cart icon
                    let cartBadge = document.querySelector(".navbar-premium a[href*='/orders/cart/'] .badge");
                    if (!cartBadge) {
                        const cartLink = document.querySelector(".navbar-premium a[href*='/orders/cart/']");
                        if (cartLink) {
                            cartLink.style.position = 'relative';
                            cartBadge = document.createElement("span");
                            cartBadge.className = "position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger";
                            cartLink.appendChild(cartBadge);
                        }
                    }
                    if (cartBadge) {
                        // Increment count locally or update if server provided count
                        if (data.cart_count) {
                            cartBadge.innerText = data.cart_count;
                        } else {
                            const currentVal = parseInt(cartBadge.innerText) || 0;
                            const addedQty = parseInt(formData.get("quantity")) || 1;
                            cartBadge.innerText = currentVal + addedQty;
                        }
                    }
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Unable to Add',
                        text: data.message,
                        background: '#0f172a',
                        color: '#f8fafc'
                    });
                }
            })
            .catch(error => {
                console.error("Cart action failed:", error);
                form.submit(); // fallback to standard redirect submission
            });
        }
    });

    // 6. Auto-dismiss message alerts after 3.5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 3500);
    });
});

// Helper for Swapping Country via Selector Dropdown
function changeCountry(countryId) {
    window.location.href = `/products/select-country/${countryId}/`;
}

// Helper for Swapping Currency via Selector Dropdown
function changeCurrency(currencyId) {
    window.location.href = `/products/select-currency/${currencyId}/`;
}
