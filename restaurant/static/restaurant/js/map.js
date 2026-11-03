document.addEventListener('DOMContentLoaded', function () {
    const restaurantMap = document.querySelector('[data-restaurant-map]');
    const contactMap = document.querySelector('[data-contact-map]');
    const locationPicker = document.querySelector('[data-location-picker]');
    const mapElement = restaurantMap || contactMap || locationPicker;
    const locationButton = document.querySelector('[data-find-location]');
    const searchInput = document.querySelector('[data-restaurant-search]');
    const cuisineSelect = document.querySelector('[data-cuisine-filter]');
    const mapStatus = document.querySelector('[data-map-status], [data-location-status]');
    const cards = document.querySelectorAll('[data-restaurant-card]');
    const noResults = document.querySelector('[data-no-results]');
    const resultCount = document.querySelector('[data-results-count]');
    const markers = [];
    const isEnglish = document.documentElement.lang === 'en';
    let map = null;

    function setStatus(message) {
        if (mapStatus) {
            mapStatus.textContent = message;
        }
    }

    function filterRestaurants() {
        const searchText = searchInput
            ? searchInput.value.trim().toLocaleLowerCase()
            : '';
        const selectedCuisine = cuisineSelect ? cuisineSelect.value : '';
        let visibleCount = 0;

        cards.forEach(function (card) {
            const cardText = (card.dataset.searchText || '').toLocaleLowerCase();
            const matchesSearch = cardText.includes(searchText);
            const matchesCuisine = !selectedCuisine
                || card.dataset.cuisine === selectedCuisine;
            const isVisible = matchesSearch && matchesCuisine;

            card.hidden = !isVisible;
            if (isVisible) {
                visibleCount += 1;
            }
        });

        if (noResults) {
            noResults.hidden = visibleCount > 0;
        }
        if (resultCount) {
            const label = resultCount.dataset.resultLabel || '';
            resultCount.textContent = visibleCount + ' ' + label;
        }

        markers.forEach(function (entry) {
            if (!map) {
                return;
            }
            const card = document.querySelector(
                '[data-restaurant-card][data-restaurant-id="' + entry.id + '"]',
            );
            const isVisible = card && !card.hidden;
            if (isVisible && !map.hasLayer(entry.marker)) {
                entry.marker.addTo(map);
            } else if (!isVisible && map.hasLayer(entry.marker)) {
                map.removeLayer(entry.marker);
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', filterRestaurants);
    }
    if (cuisineSelect) {
        cuisineSelect.addEventListener('change', filterRestaurants);
    }

    const resetFilters = document.querySelector('[data-filter-reset]');
    if (resetFilters) {
        resetFilters.addEventListener('click', function () {
            searchInput.value = '';
            cuisineSelect.value = '';
            filterRestaurants();
            searchInput.focus();
        });
    }

    if (!mapElement) {
        return;
    }
    if (typeof L === 'undefined') {
        mapElement.textContent = isEnglish
            ? 'The map did not load. Check your internet connection and refresh.'
            : 'Карта не загрузилась. Проверьте подключение к интернету и обновите страницу.';
        return;
    }

    const latitudeInput = locationPicker
        ? locationPicker.closest('form').querySelector('[name="latitude"]')
        : null;
    const longitudeInput = locationPicker
        ? locationPicker.closest('form').querySelector('[name="longitude"]')
        : null;
    const mapOptions = {
        scrollWheelZoom: false,
    };
    if (locationPicker) {
        mapOptions.maxBounds = [[38.46, 68.68], [38.71, 68.89]];
        mapOptions.maxBoundsViscosity = 0.8;
    }
    map = L.map(mapElement, mapOptions)
        .setView([38.568658, 68.785062], locationPicker ? 15 : 14);
    const tileLayer = L.tileLayer('https://tile.openstreetmap.de/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
    }).addTo(map);
    let tileErrors = 0;
    let usedFallback = false;
    let selectedMarker = null;
    let userMarker = null;

    tileLayer.on('load', function () {
        if (!usedFallback && !locationPicker) {
            setStatus('');
        }
    });
    tileLayer.on('tileerror', function () {
        if (usedFallback) {
            return;
        }
        tileErrors += 1;
        if (tileErrors >= 3) {
            usedFallback = true;
            map.removeLayer(tileLayer);
            const fallbackLayer = L.tileLayer(
                'https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
                {
                    maxZoom: 19,
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
                },
            );
            fallbackLayer.on('load', function () {
                setStatus('');
            });
            fallbackLayer.on('tileerror', function () {
                setStatus(isEnglish
                    ? 'The map could not load. Check your internet connection and refresh.'
                    : 'Не удалось загрузить карту. Проверьте интернет и обновите страницу.');
            });
            fallbackLayer.addTo(map);
            setStatus(isEnglish
                ? 'Connecting to the backup map server…'
                : 'Подключаем резервный сервер карты…');
        }
    });

    const dataElement = document.getElementById(
        restaurantMap ? 'restaurant-map-data' : 'contact-map-data',
    );
    const places = dataElement ? JSON.parse(dataElement.textContent) : [];
    const points = [];

    places.forEach(function (place) {
        const point = [place.latitude, place.longitude];
        points.push(point);

        const popup = document.createElement('div');
        const name = document.createElement('strong');
        const address = document.createElement('p');
        name.textContent = place.name;
        address.textContent = place.address || '';
        popup.append(name, address);

        if (place.url) {
            const link = document.createElement('a');
            link.textContent = isEnglish ? 'Open place' : 'Открыть место';
            link.href = place.url;
            if (place.url.startsWith('https://www.openstreetmap.org/')) {
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
            }
            popup.append(link);
        }

        const markerKind = ['terra', 'reference'].includes(place.kind)
            ? place.kind
            : 'restaurant';
        const marker = L.marker(point, {
            icon: L.divIcon({
                className: 'map-pin-wrap',
                html: '<span class="map-pin map-pin-' + markerKind + '"></span>',
                iconSize: [22, 22],
                iconAnchor: [11, 11],
            }),
        }).bindPopup(popup);
        marker.addTo(map);
        if (place.id !== undefined) {
            markers.push({ id: String(place.id), marker: marker });
        }
    });

    if (points.length > 0) {
        map.fitBounds(points, {
            padding: [32, 32],
            maxZoom: contactMap ? 15 : 13,
            animate: false
        });
    }

    if (restaurantMap) {
        const selectedPlaceId = new URLSearchParams(window.location.search).get('place');
        const selectedPlace = markers.find(function (entry) {
            return entry.id === selectedPlaceId;
        });
        if (selectedPlace) {
            map.setView(selectedPlace.marker.getLatLng(), 16, { animate: false });
            selectedPlace.marker.openPopup();
        }
    }

    if (locationPicker) {
        function setSelectedLocation(latitude, longitude) {
            latitudeInput.value = latitude.toFixed(6);
            longitudeInput.value = longitude.toFixed(6);
            if (!selectedMarker) {
                selectedMarker = L.marker([latitude, longitude], {
                    draggable: true,
                }).addTo(map);
                selectedMarker.on('dragend', function (event) {
                    const position = event.target.getLatLng();
                    setSelectedLocation(position.lat, position.lng);
                });
            } else {
                selectedMarker.setLatLng([latitude, longitude]);
            }
            setStatus(isEnglish
                ? 'Location selected. Drag the marker to adjust it.'
                : 'Место выбрано. Перетащите метку, если нужно её уточнить.');
        }

        map.on('click', function (event) {
            setSelectedLocation(event.latlng.lat, event.latlng.lng);
        });

        const savedLatitude = Number(latitudeInput.value);
        const savedLongitude = Number(longitudeInput.value);
        if (savedLatitude && savedLongitude) {
            setSelectedLocation(savedLatitude, savedLongitude);
        }
    }

    window.setTimeout(function () {
        map.invalidateSize();
    }, 100);

    if (locationButton) {
        locationButton.addEventListener('click', function () {
            if (!navigator.geolocation) {
                setStatus(isEnglish
                    ? 'This browser does not support location.'
                    : 'Этот браузер не поддерживает определение местоположения.');
                return;
            }

            locationButton.disabled = true;
            setStatus(isEnglish ? 'Finding your location…' : 'Определяем ваше местоположение…');
            navigator.geolocation.getCurrentPosition(
                function (position) {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
                        setStatus(isEnglish
                            ? 'The browser returned an invalid location.'
                            : 'Браузер вернул некорректное местоположение.');
                        locationButton.disabled = false;
                        return;
                    }
                    const point = [latitude, longitude];
                    if (userMarker) {
                        userMarker.setLatLng(point);
                    } else {
                        userMarker = L.circleMarker(point, {
                            radius: 9,
                            color: '#ffffff',
                            weight: 3,
                            fillColor: '#3578d4',
                            fillOpacity: 1,
                        }).addTo(map);
                    }
                    userMarker.bindPopup(
                        isEnglish ? 'Your current location' : 'Ваше местоположение',
                    ).openPopup();
                    map.setView(point, 16);
                    setStatus(isEnglish
                        ? 'Your location is shown on the map only for this visit.'
                        : 'Ваше местоположение показано на карте только сейчас.');
                    locationButton.disabled = false;
                },
                function (error) {
                    const messages = {
                        1: isEnglish
                            ? 'Location access was denied. Allow it in your browser settings.'
                            : 'Доступ к местоположению запрещён. Разрешите его в настройках браузера.',
                        2: isEnglish
                            ? 'Your location is unavailable. Check GPS or network and try again.'
                            : 'Местоположение недоступно. Проверьте GPS или сеть и попробуйте снова.',
                        3: isEnglish
                            ? 'Location request timed out. Please try again.'
                            : 'Время ожидания местоположения истекло. Попробуйте ещё раз.',
                    };
                    setStatus(messages[error.code] || (
                        isEnglish
                            ? 'Could not find your location. Please try again.'
                            : 'Не удалось определить местоположение. Попробуйте ещё раз.'
                    ));
                    locationButton.disabled = false;
                },
                { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 },
            );
        });
    }

    if (searchInput || cuisineSelect) {
        filterRestaurants();
    }
});
