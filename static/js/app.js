const stateSelect = document.getElementById("state-select");
const citySelect = document.getElementById("city-select");
const photoForm = document.getElementById("photo-form");
const uploadStatus = document.getElementById("upload-status");
const gallery = document.getElementById("photo-gallery");
const filterButtons = document.querySelectorAll("button[data-filter]");
const slideshow = document.getElementById("slideshow");
const slideImage = document.getElementById("slide-image");
const slideInfo = document.getElementById("slide-info");
const prevSlide = document.getElementById("prev-slide");
const nextSlide = document.getElementById("next-slide");

let allPhotos = [];
let currentFilter = "all";
let currentSlideIndex = 0;
let slideItems = [];

let geoLayers = {};      // stateName → Leaflet layer
let selectedState = null;

let startDateInput = null;
let endDateInput = null;
let periodControls = null;
let tripControls = null;
let applyPeriodButton = null;

function updateCityOptions() {
  const selectedState = stateSelect?.value;
  if (!selectedState) {
    if (citySelect) citySelect.innerHTML = '<option value="">Selecione a cidade</option>';
    return;
  }

  if (!STATES_CITIES[selectedState]) {
    if (citySelect) citySelect.innerHTML = '<option value="">Selecione a cidade</option>';
    return;
  }

  if (!citySelect) return;
  citySelect.innerHTML = '<option value="">Selecione a cidade</option>';
  STATES_CITIES[selectedState].forEach((city) => {
    const option = document.createElement("option");
    option.value = city;
    option.textContent = city;
    citySelect.appendChild(option);
  });
}

function showPhotosForState(state) {
  const panel = document.getElementById("state-photo-gallery");
  const info = document.getElementById("state-photos-info");
  if (!panel || !info) return;

  const list = allPhotos
    .filter((p) => p.state === state)
    .sort((a, b) => a.date.localeCompare(b.date));

  panel.innerHTML = "";
  if (!list.length) {
    info.textContent = `Nenhuma foto encontrada para ${state}.`;
    return;
  }

  info.textContent = `Fotos cadastradas em ${state}:`;

  const fragment = document.createDocumentFragment();
  list.forEach((item) => {
    const card = document.createElement("div");
    card.className = "photo-card";
    card.style.cursor = "pointer";

    card.innerHTML = `
      <img src="/uploads/${item.filename}" alt="Foto de viagem" />
      <div class="meta">
        <p><strong>${item.city}</strong></p>
        <p>${item.date}</p>
        <p>${item.caption || "Sem descrição"}</p>
      </div>
    `;

    card.addEventListener("click", () => openStatePhotoInSlide(item));
    fragment.appendChild(card);
  });

  panel.appendChild(fragment);

  document.getElementById("state-photos-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openStatePhotoInSlide(photo) {
  const idx = slideItems.findIndex((p) => p.filename === photo.filename);
  if (idx >= 0) {
    currentSlideIndex = idx;
    updateSlide();
    document.getElementById("slideshow")?.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

function parseDateToMs(isoDate) {
  if (!isoDate) return NaN;
  const [y, m, d] = isoDate.split("-").map((x) => parseInt(x, 10));
  if (!y || !m || !d) return NaN;
  return Date.UTC(y, m - 1, d);
}

function getFilteredPhotos() {
  if (currentFilter === "period") {
    const startMs = startDateInput?.value ? parseDateToMs(startDateInput.value) : NaN;
    const endMs = endDateInput?.value ? parseDateToMs(endDateInput.value) : NaN;

    if (Number.isNaN(startMs) && Number.isNaN(endMs)) {
      return [...allPhotos].sort((a, b) => a.date.localeCompare(b.date));
    }

    return allPhotos
      .filter((p) => {
        const t = parseDateToMs(p.date);
        if (Number.isNaN(t)) return false;
        if (!Number.isNaN(startMs) && t < startMs) return false;
        if (!Number.isNaN(endMs) && t > endMs) return false;
        return true;
      })
      .sort((a, b) => a.date.localeCompare(b.date));
  }

  if (currentFilter === "trip") {
    const X_DAYS = 2;
    const MAX_GAP_MS = X_DAYS * 24 * 60 * 60 * 1000;

    const byKey = {};
    allPhotos.forEach((photo) => {
      const key = `${photo.state} - ${photo.city}`;
      if (!byKey[key]) byKey[key] = [];
      byKey[key].push(photo);
    });

    const trips = [];
    Object.entries(byKey).forEach(([key, items]) => {
      const sorted = items.sort((a, b) => a.date.localeCompare(b.date));
      let currentSegment = [];
      let segmentStartMs = NaN;
      let segmentEndMs = NaN;

      for (const p of sorted) {
        const t = parseDateToMs(p.date);
        if (Number.isNaN(t)) continue;

        if (currentSegment.length === 0) {
          currentSegment.push(p);
          segmentStartMs = t;
          segmentEndMs = t;
          continue;
        }

        const prev = currentSegment[currentSegment.length - 1];
        const prevMs = parseDateToMs(prev.date);

        if (!Number.isNaN(prevMs) && t - prevMs <= MAX_GAP_MS) {
          currentSegment.push(p);
          segmentEndMs = t;
        } else {
          trips.push({ key, items: currentSegment, startMs: segmentStartMs, endMs: segmentEndMs });
          currentSegment = [p];
          segmentStartMs = t;
          segmentEndMs = t;
        }
      }

      if (currentSegment.length) {
        trips.push({ key, items: currentSegment, startMs: segmentStartMs, endMs: segmentEndMs });
      }
    });

    if (!trips.length) return [];
    trips.sort((a, b) => b.endMs - a.endMs);
    return trips[0].items.sort((a, b) => a.date.localeCompare(b.date));
  }

  return [...allPhotos].sort((a, b) => a.date.localeCompare(b.date));
}

function renderGallery() {
  gallery.innerHTML = "";
  const list = getFilteredPhotos();
  if (list.length === 0) {
    gallery.innerHTML = "<p>Nenhuma foto cadastrada ainda.</p>";
    slideshow?.classList.add("hidden");
    return;
  }

  list.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "photo-card";
    card.innerHTML = `
      <img src="/uploads/${item.filename}" alt="Foto de viagem" />
      <div class="meta">
        <p><strong>${item.city}, ${item.state}</strong></p>
        <p>${item.date}</p>
        <p>${item.caption || "Sem descrição"}</p>
      </div>
    `;

    card.addEventListener("click", () => openSlide(index));
    gallery.appendChild(card);
  });

  slideItems = list;
  currentSlideIndex = 0;
  updateSlide();
}

function updateSlide() {
  if (!slideItems.length) {
    slideshow.classList.add("hidden");
    return;
  }

  slideshow.classList.remove("hidden");
  const item = slideItems[currentSlideIndex];
  slideImage.src = `/uploads/${item.filename}`;
  slideInfo.textContent = `${item.date} — ${item.city}, ${item.state} — ${item.caption || "Sem descrição"}`;
}

function openSlide(index) {
  currentSlideIndex = index;
  updateSlide();
}

async function loadPhotos() {
  try {
    const response = await fetch("/photos");
    allPhotos = await response.json();
    renderGallery();
    refreshMapStyles();
  } catch (error) {
    gallery.innerHTML = "<p>Não foi possível carregar as fotos.</p>";
  }
}

function getStateStyle(stateName, isSelected) {
  const hasPhotos = allPhotos.some((p) => p.state === stateName);
  if (isSelected) {
    return { color: "#1565c0", weight: 2.5, fillColor: "#1976d2", fillOpacity: 0.55 };
  }
  if (hasPhotos) {
    return { color: "#2e7d32", weight: 1.5, fillColor: "#43a047", fillOpacity: 0.35 };
  }
  return { color: "#1976d2", weight: 1, fillColor: "#1976d2", fillOpacity: 0.0 };
}

function refreshMapStyles() {
  Object.entries(geoLayers).forEach(([name, layer]) => {
    layer.setStyle(getStateStyle(name, name === selectedState));
  });
}

function initMap() {
  const map = L.map("map", {
    center: [-14.5, -51.5],
    zoom: 4,
    zoomControl: true,
    attributionControl: true,
    scrollWheelZoom: false,
    dragging: true,
    doubleClickZoom: true,
    touchZoom: true,
  });

  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 10,
    minZoom: 3,
  }).addTo(map);

  fetch("/static/geo/uf-br.geojson")
    .then((r) => r.json())
    .then((geo) => {
      L.geoJSON(geo, {
        style: (feature) => {
          const name = (feature?.properties?.name || "").toString();
          return getStateStyle(name, false);
        },
        onEachFeature: (feature, fLayer) => {
          const props = feature?.properties || {};
          const stateName = (
            props.name ||
            props.NOME ||
            props.UF ||
            props.uf ||
            props.sigla ||
            props.SIGLA ||
            ""
          ).toString();

          if (!stateName) return;

          geoLayers[stateName] = fLayer;

          fLayer.bindTooltip(stateName, { sticky: true });

          fLayer.on({
            click: () => {
              selectedState = stateName;
              refreshMapStyles();
              showPhotosForState(stateName);

              if (stateSelect) {
                stateSelect.value = stateName;
                updateCityOptions();
                const cities = STATES_CITIES[stateName] || [];
                if (cities[0]) citySelect.value = cities[0];
              }

              document.getElementById("state-photos-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
            },
            mouseover: () => {
              if (stateName !== selectedState) {
                fLayer.setStyle({ fillOpacity: 0.3, weight: 2 });
              }
            },
            mouseout: () => {
              if (stateName !== selectedState) {
                fLayer.setStyle(getStateStyle(stateName, false));
              }
            },
          });
        },
      }).addTo(map);
    })
    .catch(() => {});
}

// bindings de UI
stateSelect?.addEventListener("change", updateCityOptions);

periodControls = document.getElementById("period-controls");
tripControls = document.getElementById("trip-controls");
startDateInput = document.getElementById("start-date");
endDateInput = document.getElementById("end-date");
applyPeriodButton = document.getElementById("apply-period");

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filterButtons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");
    currentFilter = button.dataset.filter;

    if (currentFilter === "period") {
      periodControls.classList.remove("hidden");
      tripControls.classList.add("hidden");
    } else if (currentFilter === "trip") {
      tripControls.classList.remove("hidden");
      periodControls.classList.add("hidden");
    } else {
      periodControls?.classList.add("hidden");
      tripControls?.classList.add("hidden");
    }

    renderGallery();
  });
});

applyPeriodButton?.addEventListener("click", () => {
  currentFilter = "period";
  filterButtons.forEach((btn) => btn.classList.remove("active"));
  const periodBtn = document.querySelector('button[data-filter="period"]');
  if (periodBtn) periodBtn.classList.add("active");
  renderGallery();
});

photoForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(photoForm);
  uploadStatus.textContent = "Enviando foto...";

  try {
    const response = await fetch("/upload", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok || !data.success) {
      uploadStatus.textContent = data.message || "Erro ao enviar foto.";
      uploadStatus.style.color = "#c62828";
      return;
    }

    uploadStatus.textContent = "Foto enviada com sucesso!";
    uploadStatus.style.color = "#2e7d32";
    photoForm.reset();
    citySelect.innerHTML = '<option value="">Selecione a cidade</option>';

    await loadPhotos();
  } catch (error) {
    uploadStatus.textContent = "Erro ao conectar com o servidor.";
    uploadStatus.style.color = "#c62828";
  }
});

prevSlide?.addEventListener("click", () => {
  if (!slideItems.length) return;
  currentSlideIndex = (currentSlideIndex - 1 + slideItems.length) % slideItems.length;
  updateSlide();
});

nextSlide?.addEventListener("click", () => {
  if (!slideItems.length) return;
  currentSlideIndex = (currentSlideIndex + 1) % slideItems.length;
  updateSlide();
});

initMap();
loadPhotos();

