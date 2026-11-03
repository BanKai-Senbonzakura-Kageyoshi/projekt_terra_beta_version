document.addEventListener('DOMContentLoaded', function () {
    const header = document.querySelector('[data-header]');
    const bookingDialog = document.querySelector('[data-booking-dialog]');
    const lightbox = document.querySelector('[data-lightbox]');
    const lightboxImage = document.querySelector('[data-lightbox-image]');
    const mainNavigation = document.querySelector('[data-main-nav]');
    const menuToggle = document.querySelector('[data-menu-toggle]');

    function updateHeader() {
        if (header) {
            header.classList.toggle('is-scrolled', window.scrollY > 24);
        }
    }

    updateHeader();
    window.addEventListener('scroll', updateHeader, { passive: true });

    document.querySelectorAll('[data-open-booking]').forEach(function (button) {
        button.addEventListener('click', function () {
            if (bookingDialog) {
                const restaurantSelect = bookingDialog.querySelector('[name="restaurant"]');
                if (restaurantSelect && button.dataset.bookRestaurant) {
                    restaurantSelect.value = button.dataset.bookRestaurant;
                }
                bookingDialog.showModal();
            }
        });
    });

    document.querySelectorAll('[data-close-booking]').forEach(function (button) {
        button.addEventListener('click', function () {
            bookingDialog.close();
        });
    });

    document.querySelectorAll('[data-gallery-image]').forEach(function (button) {
        button.addEventListener('click', function () {
            lightboxImage.src = button.dataset.galleryImage;
            lightboxImage.alt = button.dataset.galleryAlt;
            lightbox.showModal();
        });
    });

    document.querySelectorAll('[data-close-lightbox]').forEach(function (button) {
        button.addEventListener('click', function () {
            lightbox.close();
        });
    });

    [bookingDialog, lightbox].forEach(function (dialog) {
        if (dialog) {
            dialog.addEventListener('click', function (event) {
                if (event.target === dialog) {
                    dialog.close();
                }
            });
        }
    });

    if (menuToggle && mainNavigation) {
        menuToggle.addEventListener('click', function () {
            const isOpen = mainNavigation.classList.toggle('is-open');
            menuToggle.setAttribute('aria-expanded', String(isOpen));
        });

        mainNavigation.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                mainNavigation.classList.remove('is-open');
                menuToggle.setAttribute('aria-expanded', 'false');
            });
        });
    }

    const revealElements = document.querySelectorAll('[data-reveal]');
    if ('IntersectionObserver' in window) {
        const revealObserver = new IntersectionObserver(function (entries, observer) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });

        revealElements.forEach(function (element) {
            revealObserver.observe(element);
        });
    } else {
        revealElements.forEach(function (element) {
            element.classList.add('is-visible');
        });
    }

    const today = new Date();
    const localDate = new Date(today.getTime() - today.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 10);
    document.querySelectorAll('[data-date-field]').forEach(function (field) {
        field.min = localDate;
    });

    document.querySelectorAll('[data-submit-button]').forEach(function (button) {
        button.form.addEventListener('submit', function () {
            button.disabled = true;
            button.textContent = document.documentElement.lang === 'en'
                ? 'Sending...'
                : 'Отправляем...';
        });
    });

    document.querySelectorAll('[data-image-preview]').forEach(function (input) {
        input.addEventListener('change', function () {
            const preview = input
                .closest('.form-field')
                .querySelector('[data-upload-preview]');
            const file = input.files[0];
            if (!preview || !file) {
                return;
            }
            if (preview.dataset.objectUrl) {
                URL.revokeObjectURL(preview.dataset.objectUrl);
            }
            const objectUrl = URL.createObjectURL(file);
            preview.dataset.objectUrl = objectUrl;
            preview.src = objectUrl;
            preview.hidden = false;
        });
    });

    document.querySelectorAll('[data-reject-button]').forEach(function (button) {
        button.addEventListener('click', function (event) {
            const note = button.form.querySelector('[name="moderation_note"]');
            if (note && !note.value.trim()) {
                event.preventDefault();
                note.setCustomValidity(document.documentElement.lang === 'en'
                    ? 'Please explain why this restaurant is being declined.'
                    : 'Укажите причину отклонения ресторана.');
                note.reportValidity();
                note.addEventListener('input', function clearValidation() {
                    note.setCustomValidity('');
                    note.removeEventListener('input', clearValidation);
                });
            }
        });
    });

    const menuRestaurantFilter = document.querySelector('[data-menu-restaurant-filter]');
    const menuDishSearch = document.querySelector('[data-menu-dish-search]');
    if (menuRestaurantFilter && menuDishSearch) {
        const menuCategoryFilter = document.querySelector('[data-menu-category-filter]');
        const menuPriceFilter = document.querySelector('[data-menu-price-filter]');
        const vegetarianFilter = document.querySelector('[data-menu-vegetarian-filter]');
        const menuFilterReset = document.querySelector('[data-menu-filter-reset]');
        const menuResults = document.querySelector('[data-menu-results]');
        const menuNoResults = document.querySelector('[data-menu-no-results]');

        function filterMenus() {
            const selectedRestaurant = menuRestaurantFilter.value;
            const searchText = menuDishSearch.value.trim().toLocaleLowerCase();
            const selectedCategory = menuCategoryFilter ? menuCategoryFilter.value : '';
            const selectedPrice = menuPriceFilter ? menuPriceFilter.value : '';
            const vegetarianOnly = vegetarianFilter && vegetarianFilter.checked;
            const filterIsActive = Boolean(
                selectedRestaurant || searchText || selectedCategory || selectedPrice || vegetarianOnly,
            );
            let visibleDishCount = 0;

            document.querySelectorAll('[data-menu-restaurant]').forEach(function (restaurant) {
                const matchesRestaurant = !selectedRestaurant
                    || restaurant.dataset.menuRestaurant === selectedRestaurant;
                let restaurantHasMatch = false;

                restaurant.querySelectorAll('[data-menu-category]').forEach(function (category) {
                    const matchesCategory = !selectedCategory
                        || category.dataset.menuCategoryName === selectedCategory;
                    let categoryHasMatch = false;
                    category.querySelectorAll('[data-menu-item]').forEach(function (item) {
                        const price = Number(item.dataset.menuPrice);
                        const matchesPrice = !selectedPrice
                            || (selectedPrice === 'under-50' && price < 50)
                            || (selectedPrice === '50-100' && price >= 50 && price <= 100)
                            || (selectedPrice === 'over-100' && price > 100);
                        const matches = item.textContent.toLocaleLowerCase().includes(searchText)
                            && (!vegetarianOnly || item.dataset.menuVegetarian === 'true')
                            && matchesPrice
                            && matchesCategory;
                        item.hidden = !matches;
                        if (matches) {
                            categoryHasMatch = true;
                            restaurantHasMatch = true;
                            if (matchesRestaurant) {
                                visibleDishCount += 1;
                            }
                        }
                    });
                    category.hidden = !matchesCategory || (filterIsActive && !categoryHasMatch);
                });

                restaurant.hidden = !matchesRestaurant || (filterIsActive && !restaurantHasMatch);
                if (filterIsActive && matchesRestaurant && restaurantHasMatch) {
                    restaurant.open = true;
                }
            });

            if (menuResults) {
                const label = menuResults.dataset.resultLabel || '';
                menuResults.textContent = visibleDishCount + ' ' + label;
            }
            if (menuNoResults) {
                menuNoResults.hidden = visibleDishCount > 0;
            }
        }

        menuRestaurantFilter.addEventListener('change', filterMenus);
        menuDishSearch.addEventListener('input', filterMenus);
        [menuCategoryFilter, menuPriceFilter, vegetarianFilter].forEach(function (filter) {
            if (filter) {
                filter.addEventListener('change', filterMenus);
            }
        });
        if (menuFilterReset) {
            menuFilterReset.addEventListener('click', function () {
                menuRestaurantFilter.value = '';
                menuDishSearch.value = '';
                if (menuCategoryFilter) {
                    menuCategoryFilter.value = '';
                }
                if (menuPriceFilter) {
                    menuPriceFilter.value = '';
                }
                if (vegetarianFilter) {
                    vegetarianFilter.checked = false;
                }
                filterMenus();
                menuRestaurantFilter.focus();
            });
        }
    }
});
