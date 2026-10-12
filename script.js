const defaultListings = [
  {
    id: 1,
    seller: "Sundari Farms",
    district: "Thanjavur",
    residue: "Rice Straw",
    crop: "Rice",
    quantity: 6.2,
    unit: "t",
    quality: "Dry, clean",
    moisture: 12,
    price: 1450,
    distance: 32,
    availability: "2026-10-18",
    status: "Verified",
    image: "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=900&q=80"
  },
  {
    id: 2,
    seller: "GreenSpark Agro",
    district: "Coimbatore",
    residue: "Sugarcane Bagasse",
    crop: "Sugarcane",
    quantity: 9.8,
    unit: "t",
    quality: "Premium fibre",
    moisture: 18,
    price: 1800,
    distance: 48,
    availability: "2026-10-21",
    status: "Verified",
    image: "https://images.unsplash.com/photo-1471193945509-9ad0617afabf?auto=format&fit=crop&w=900&q=80"
  },
  {
    id: 3,
    seller: "Nadhamuni Bio",
    district: "Madurai",
    residue: "Coconut Husk",
    crop: "Coconut",
    quantity: 3.4,
    unit: "t",
    quality: "Medium grade",
    moisture: 25,
    price: 960,
    distance: 24,
    availability: "2026-10-19",
    status: "Needs review",
    image: "https://images.unsplash.com/photo-1523741543316-beb7fc7023d8?auto=format&fit=crop&w=900&q=80"
  },
  {
    id: 4,
    seller: "Veda Valley",
    district: "Tirupur",
    residue: "Cotton Stalk",
    crop: "Cotton",
    quantity: 4.1,
    unit: "t",
    quality: "Clean and baled",
    moisture: 14,
    price: 1200,
    distance: 39,
    availability: "2026-10-25",
    status: "Verified",
    image: "https://images.unsplash.com/photo-1492496913980-501348b61469?auto=format&fit=crop&w=900&q=80"
  }
];

const roleMetrics = {
  farmer: [
    { label: "Active listings", value: 18, delta: "+6% this month" },
    { label: "Buyer enquiries", value: 42, delta: "+12 new" },
    { label: "Sales value", value: "₹4.8L", delta: "+₹85k" },
    { label: "Avg. fulfillment", value: "96%", delta: "On-time" }
  ],
  buyer: [
    { label: "Open requests", value: 9, delta: "3 priority" },
    { label: "Matches found", value: 26, delta: "+7 today" },
    { label: "Procurement spend", value: "₹6.2L", delta: "+₹1.1L" },
    { label: "On-time delivery", value: "94%", delta: "Strong" }
  ],
  admin: [
    { label: "Registered users", value: 1132, delta: "+86 this week" },
    { label: "Active listings", value: 436, delta: "12 under review" },
    { label: "Orders tracked", value: 289, delta: "34 pending" },
    { label: "Transaction value", value: "₹24.7L", delta: "+8.3%" }
  ],
  researcher: [
    { label: "Farmers engaged", value: 624, delta: "+34 this month" },
    { label: "Residue records", value: 1084, delta: "81% complete" },
    { label: "Model accuracy", value: "R² 0.82", delta: "Baseline validated" },
    { label: "Export ready", value: 7, delta: "Data packs" }
  ]
};

const researchRows = [
  { category: "Farmer", district: "Trichy", crop: "Rice", residue: "Rice straw", quantity: "5.4t", value: "₹9,800", consent: "Yes" },
  { category: "Processor", district: "Madurai", crop: "Sugarcane", residue: "Bagasse", quantity: "7.1t", value: "₹15,200", consent: "Yes" },
  { category: "Entrepreneur", district: "Coimbatore", crop: "Maize", residue: "Stalks", quantity: "3.3t", value: "₹7,100", consent: "Yes" },
  { category: "Farmer", district: "Salem", crop: "Coconut", residue: "Husk", quantity: "2.7t", value: "₹5,600", consent: "Pending" }
];

const state = {
  role: "farmer",
  search: "",
  residueFilter: "All",
  districtFilter: "All",
  priceCap: 2500,
  listings: defaultListings,
  researchResponses: researchRows,
  apiToken: localStorage.getItem("agriwaste_token") || "",
  authMode: "login"
};

const API_BASE_URL = window.location.protocol === "file:" ? "http://localhost:8000" : window.location.origin;

async function apiFetch(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(state.apiToken ? { Authorization: `Bearer ${state.apiToken}` } : {}),
    ...(options.headers || {})
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    const errorBody = contentType.includes("application/json")
      ? await response.json()
      : { detail: await response.text() };
    throw new Error(errorBody.detail || "Request failed");
  }

  return response.headers.get("content-type")?.includes("application/json") ? response.json() : response.text();
}

async function ensureAuthenticated() {
  if (state.apiToken) return state.apiToken;
  const bootstrapResponse = await fetch(`${API_BASE_URL}/api/public/bootstrap`);
  if (!bootstrapResponse.ok) {
    throw new Error("Cannot connect to the application API.");
  }
  const bootstrap = await bootstrapResponse.json();
  if (!bootstrap.synthetic_data) {
    throw new Error("Sign in to use this feature.");
  }
  const demoCredentials = {
    email: "farmer@agriwaste2wealth.example.com",
    password: "FarmerPass123!"
  };
  const loginResponse = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(demoCredentials)
  });
  if (!loginResponse.ok) {
    throw new Error("Unable to authenticate demo user");
  }
  const payload = await loginResponse.json();
  state.apiToken = payload.access_token;
  localStorage.setItem("agriwaste_token", state.apiToken);
  return state.apiToken;
}

async function loadBackendData() {
  const statusEl = document.getElementById("systemStatus");
  const backendChip = document.getElementById("backendChip");
  try {
    await ensureAuthenticated();
    const [summary, listings, user] = await Promise.all([
      apiFetch("/api/dashboard/summary"),
      apiFetch("/api/listings"),
      apiFetch("/api/me")
    ]);
    state.role = user.role;
    document.getElementById("authAction").textContent = "Sign out";

    if (statusEl) {
      statusEl.innerHTML = '<span class="status-dot"></span> Backend live';
    }
    if (backendChip) {
      backendChip.innerHTML = '<span class="chip-dot"></span> Backend live';
    }

    state.listings = Array.isArray(listings) ? listings.map((item) => ({
      id: item.id,
      seller: item.seller_name || "Farmer",
      district: item.district,
      residue: item.residue_type,
      crop: item.source_crop,
      quantity: Number(item.quantity_available || 0),
      unit: item.unit || "t",
      quality: item.quality || "Standard",
      moisture: item.moisture_content || 0,
      price: Number(item.price_per_unit || 0),
      distance: 30,
      availability: item.availability_date || "2026-10-30",
      status: item.status || "Verified",
      image: item.photo_url || "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=900&q=80"
    })) : defaultListings;

    try {
      const research = await apiFetch("/api/research");
      state.researchResponses = Array.isArray(research) ? research.map((row) => ({
        category: row.respondent_category || "Farmer",
        district: row.district,
        crop: row.main_crop,
        residue: row.residue_type,
        quantity: `${row.quantity_generated || 0}t`,
        value: `₹${Number(row.sale_price || 0).toLocaleString("en-IN")}`,
        consent: row.consent_given ? "Yes" : "Pending"
      })) : researchRows;
    } catch (researchError) {
      console.info("Research endpoint unavailable for this role; keeping demo snapshot.");
    }

    document.getElementById("dashboardGrid").innerHTML = "";
    renderDashboard();
    renderMarketplace();
    renderResearchTable();
    if (summary && typeof summary.total_value !== "undefined") {
      roleMetrics.farmer[2].value = `₹${Math.round(summary.total_value / 1000)}k`;
      roleMetrics.buyer[2].value = `₹${Math.round(summary.total_value / 1000)}k`;
      roleMetrics.admin[3].value = `₹${Math.round(summary.total_value / 1000)}k`;
    }
  } catch (error) {
    if (statusEl) {
      statusEl.innerHTML = '<span class="status-dot"></span> Demo fallback';
    }
    if (backendChip) {
      backendChip.innerHTML = '<span class="chip-dot"></span> Demo fallback';
    }
    console.warn("Backend unavailable, using default demo data", error);
    setNotice(error.message || "Backend unavailable. Showing synthetic demonstration data.", "error");
    renderDashboard();
    renderMarketplace();
    renderResearchTable();
  }
}

function setNotice(message, kind = "info") {
    const notice = document.getElementById("actionNotice");
    if (!notice) return;
    notice.textContent = message;
    notice.dataset.kind = kind;
    notice.hidden = false;
    window.clearTimeout(setNotice.timeout);
    setNotice.timeout = window.setTimeout(() => {
      notice.hidden = true;
    }, 5000);
  }

function setAuthMode(mode) {
    state.authMode = mode;
    const registering = mode === "register";
    document.getElementById("authTitle").textContent = registering ? "Create your account" : "Sign in";
    document.getElementById("authDescription").textContent = registering
      ? "Register as a farmer, buyer, or researcher."
      : "Sign in to use live marketplace and research features.";
    document.getElementById("authNameField").hidden = !registering;
    document.getElementById("authRoleField").hidden = !registering;
    document.getElementById("authName").required = registering;
    document.getElementById("authSubmit").textContent = registering ? "Create account" : "Sign in";
    document.getElementById("authPassword").autocomplete = registering ? "new-password" : "current-password";
    document.getElementById("authSwitch").textContent = registering ? "Already have an account? Sign in" : "Create an account";
    document.getElementById("authError").hidden = true;
  }

async function handleAuthSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const errorEl = document.getElementById("authError");
    const registering = state.authMode === "register";
    const body = {
      email: formData.get("email"),
      password: formData.get("password")
    };

    try {
      if (registering) {
        const registration = await fetch(`${API_BASE_URL}/api/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...body, name: formData.get("name"), role: formData.get("role") })
        });
        if (!registration.ok) {
          const message = await registration.json();
          throw new Error(message.detail || "Account registration failed.");
        }
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!response.ok) {
        const message = await response.json();
        throw new Error(message.detail || "Sign in failed.");
      }
      const result = await response.json();
      state.apiToken = result.access_token;
      localStorage.setItem("agriwaste_token", state.apiToken);
      const user = await apiFetch("/api/me");
      state.role = user.role;
      document.getElementById("authAction").textContent = "Sign out";
      document.getElementById("authDialog").close();
      renderDashboard();
      await loadBackendData();
      setNotice(`Signed in as ${user.name} (${user.role}).`);
    } catch (error) {
      errorEl.textContent = error.message || "Authentication failed.";
      errorEl.hidden = false;
    }
  }

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(value);
}

function renderDashboard() {
  const dashboardGrid = document.getElementById("dashboardGrid");
  const metrics = roleMetrics[state.role];
  dashboardGrid.innerHTML = metrics
    .map((item) => `
      <div class="metric">
        <span class="kicker">${item.label}</span>
        <strong>${item.value}</strong>
        <small>${item.delta}</small>
      </div>
    `)
    .join("");

  document.querySelectorAll(".role-toggle").forEach((button) => {
    button.classList.toggle("active", button.dataset.role === state.role);
  });
}

function renderMarketplace() {
  const cards = document.getElementById("listingGrid");
  const filtered = [...state.listings].filter((item) => {
    const matchesText = !state.search || [item.seller, item.residue, item.district, item.crop].some((field) =>
      field.toLowerCase().includes(state.search.toLowerCase())
    );
    const matchesResidue = state.residueFilter === "All" || item.residue === state.residueFilter;
    const matchesDistrict = state.districtFilter === "All" || item.district === state.districtFilter;
    const matchesPrice = item.price <= state.priceCap;
    return matchesText && matchesResidue && matchesDistrict && matchesPrice;
  });

  cards.innerHTML = filtered.length
    ? filtered
        .map(
          (item) => `
            <article class="listing-card">
              <div class="listing-image" style="background-image:url('${item.image}')"></div>
              <div class="content">
                <div class="tags">
                  <span class="tag">${item.residue}</span>
                  <span class="status-badge">${item.status}</span>
                </div>
                <h4>${item.seller}</h4>
                <p class="muted">${item.crop} • ${item.district}</p>
                <ul class="listing-meta">
                  <li>Available: ${item.quantity} ${item.unit}</li>
                  <li>Quality: ${item.quality}</li>
                  <li>Range: ${item.distance} km pickup</li>
                </ul>
                <div class="price-row">
                  <div>
                    <div class="muted">Expected price</div>
                    <div class="price-value">₹${item.price}/t</div>
                  </div>
                  <button class="btn btn-primary">Request</button>
                </div>
              </div>
            </article>
          `
        )
        .join("")
    : '<div class="panel" style="grid-column:1/-1;"><p class="muted">No listings match the current filter selection. Adjust criteria to expand the search.</p></div>';

  const residueSelect = document.getElementById("residueFilter");
  const districtSelect = document.getElementById("districtFilter");
  if (!residueSelect.dataset.filled) {
    const residueOptions = [...new Set(state.listings.map((item) => item.residue))];
    residueSelect.innerHTML = ['<option value="All">All residues</option>']
      .concat(residueOptions.map((value) => `<option value="${value}">${value}</option>`))
      .join("");
    residueSelect.dataset.filled = "true";
  }

  if (!districtSelect.dataset.filled) {
    const districtOptions = [...new Set(state.listings.map((item) => item.district))];
    districtSelect.innerHTML = ['<option value="All">All districts</option>']
      .concat(districtOptions.map((value) => `<option value="${value}">${value}</option>`))
      .join("");
    districtSelect.dataset.filled = "true";
  }
}

function buildAIEstimateSummary(payload) {
  const area = Number(payload.area_acres ?? payload.area ?? 0) || 0;
  const production = Number(payload.yield_per_acre_t ?? payload.production ?? 0) || 0;
  const season = payload.season || "Rabi";
  const residueFactor = Number(payload.residue_factor ?? payload.residueFactor ?? 0.22) || 0.22;
  const recovery = Number(payload.recovery_ratio ?? payload.recovery ?? 0.66) || 0.66;
  const priceKg = Number(payload.expected_price_per_kg ?? payload.priceKg ?? 1.8) || 1.8;

  const residueGeneration = area * production * residueFactor;
  const recoverable = residueGeneration * recovery;
  const marketable = recoverable * 0.74;
  const value = marketable * 1000 * priceKg;
  const collectionCost = recoverable * 140;
  const transportCost = area * 260;
  const netIncome = value - collectionCost - transportCost;
  const confidence = Math.min(92, Math.max(58, 78 + (recovery * 18) - (season === "Kharif" ? 5 : 0)));

  return {
    residueGeneration,
    recoverable,
    marketable,
    netIncome,
    confidence,
    season,
    label: payload.label || "Preliminary valuation"
  };
}

function renderAIResult() {
  const form = document.getElementById("aiEstimatorForm");
  const resultWrap = document.getElementById("aiResultWrap");
  const formData = new FormData(form);
  const payload = {
    area: Number(formData.get("area")) || 0,
    production: Number(formData.get("production")) || 0,
    season: formData.get("season") || "Rabi",
    residueFactor: Number(formData.get("residueFactor")) || 0.22,
    recovery: Number(formData.get("recovery")) || 0.66,
    priceKg: Number(formData.get("priceKg")) || 1.8
  };
  const summary = buildAIEstimateSummary(payload);

  resultWrap.innerHTML = `
    <div class="result-box">
      <h4>${summary.label}</h4>
      <div class="main-value">${formatCurrency(summary.netIncome)}</div>
      <div class="muted" style="margin-top:0.4rem;">Estimated net income • model version v1.4 • ${summary.season} season</div>
      <div class="breakdown">
        <div>
          <span>Residue generated</span>
          <strong>${summary.residueGeneration.toFixed(1)} t</strong>
        </div>
        <div>
          <span>Recoverable</span>
          <strong>${summary.recoverable.toFixed(1)} t</strong>
        </div>
        <div>
          <span>Marketable</span>
          <strong>${summary.marketable.toFixed(1)} t</strong>
        </div>
        <div>
          <span>Confidence</span>
          <strong>${summary.confidence.toFixed(0)}%</strong>
        </div>
      </div>
    </div>
  `;
}

function renderMatchesFromResults(matches = []) {
  const matchList = document.getElementById("matchList");
  if (!Array.isArray(matches) || !matches.length) {
    matchList.innerHTML = '<div class="muted">No matches available for the selected specification.</div>';
    return;
  }

  matchList.innerHTML = matches
    .map((match) => {
      const reasons = Array.isArray(match.reasons) ? match.reasons : ["Weighted match based on crop, price, and logistics fit."];
      return `
        <article class="match-card">
          <header>
            <div>
              <strong>${match.seller_name || "Seller"}</strong>
              <div class="muted">${match.residue_type || "Residue"} • ${match.district || "Local"}</div>
            </div>
            <span class="score-pill">${Math.round(match.score || 0)}%</span>
          </header>
          <div class="muted">${match.quantity_available || 0} t available • ${formatCurrency(match.price_per_unit || 0)}/t</div>
          <ul>
            ${reasons.map((reason) => `<li>${reason}</li>`).join("")}
          </ul>
        </article>
      `;
    })
    .join("");
}

function renderMatches() {
  const requirements = {
    residue: document.getElementById("buyerResidue").value,
    quantity: Number(document.getElementById("buyerQty").value) || 3,
    district: document.getElementById("buyerDistrict").value,
    maxPrice: Number(document.getElementById("buyerPrice").value) || 1800
  };

  const matches = state.listings
    .filter((item) => item.residue === requirements.residue || requirements.residue === "All")
    .map((item) => {
      const quantityScore = 100 - Math.max(0, ((requirements.quantity - item.quantity) / requirements.quantity) * 90);
      const priceScore = item.price <= requirements.maxPrice ? 100 : Math.max(35, 100 - ((item.price - requirements.maxPrice) / 1200) * 100);
      const distanceScore = Math.max(40, 100 - (item.distance / 90) * 100);
      const qualityScore = item.quality.includes("clean") || item.quality.includes("Premium") ? 100 : 82;
      const score = Math.round((quantityScore + priceScore + distanceScore + qualityScore) / 4);
      const reasons = [
        `${item.quantity} t available against ${requirements.quantity} t need`,
        `Price ${formatCurrency(item.price)}/t is within target`,
        `Seller in ${item.district} with ${item.distance} km logistics footprint`,
        `${item.status} status and ${item.quality} quality`
      ];
      return { item, score, reasons };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  document.getElementById("matchList").innerHTML = matches
    .map(
      ({ item, score, reasons }) => `
        <article class="match-card">
          <header>
            <div>
              <strong>${item.seller}</strong>
              <div class="muted">${item.residue} • ${item.district}</div>
            </div>
            <span class="score-pill">${score}%</span>
          </header>
          <div class="muted">${item.quantity} t available • ${item.quality}</div>
          <ul>
            ${reasons.map((reason) => `<li>${reason}</li>`).join("")}
          </ul>
        </article>
      `
    )
    .join("");
}

async function requestAIEstimate(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = {
    area_acres: Number(formData.get("area")) || 0,
    yield_per_acre_t: Number(formData.get("production")) || 0,
    residue_factor: Number(formData.get("residueFactor")) || 0.22,
    recovery_ratio: Number(formData.get("recovery")) || 0.66,
    expected_price_per_kg: Number(formData.get("priceKg")) || 1.8,
    season: formData.get("season") || "rabi",
    residue_type: "rice_straw"
  };

  try {
    await ensureAuthenticated();
    const response = await apiFetch("/api/ai/estimate", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    const summary = buildAIEstimateSummary({
      ...payload,
      label: response?.label || "AI estimate",
      area_acres: payload.area_acres,
      yield_per_acre_t: payload.yield_per_acre_t,
      residue_factor: payload.residue_factor,
      recovery_ratio: payload.recovery_ratio,
      expected_price_per_kg: payload.expected_price_per_kg,
      season: payload.season
    });
    const resultWrap = document.getElementById("aiResultWrap");
    resultWrap.innerHTML = `
      <div class="result-box">
        <h4>${summary.label}</h4>
        <div class="main-value">${formatCurrency(summary.netIncome)}</div>
        <div class="muted" style="margin-top:0.4rem;">Estimated net income • ${payload.season} season • label: ${response?.label || "preliminary"}</div>
        <div class="breakdown">
          <div><span>Residue generated</span><strong>${summary.residueGeneration.toFixed(1)} t</strong></div>
          <div><span>Recoverable</span><strong>${summary.recoverable.toFixed(1)} t</strong></div>
          <div><span>Marketable</span><strong>${summary.marketable.toFixed(1)} t</strong></div>
          <div><span>Confidence</span><strong>${summary.confidence.toFixed(0)}%</strong></div>
        </div>
      </div>
    `;
  } catch (error) {
    console.warn("AI estimate API unavailable, using local estimator", error);
    setNotice(error.message || "The estimate could not be saved by the API.", "error");
  }
}

async function requestMatches(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = {
    residue_type: formData.get("buyerResidue") || "Rice Straw",
    quantity_required: Number(formData.get("buyerQty")) || 0,
    unit: "t",
    acceptable_price: Number(formData.get("buyerPrice")) || 0,
    district: formData.get("buyerDistrict") || "Thanjavur"
  };

  try {
    await ensureAuthenticated();
    const response = await apiFetch("/api/matches", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    renderMatchesFromResults(response?.matches || []);
  } catch (error) {
    console.warn("Matching API unavailable, using local match logic", error);
    setNotice(error.message || "Matching could not be completed by the API.", "error");
  }
}

function renderResearchTable() {
  const tableBody = document.getElementById("researchTableBody");
  tableBody.innerHTML = state.researchResponses
    .map(
      (row) => `
        <tr>
          <td>${row.category}</td>
          <td>${row.district}</td>
          <td>${row.crop}</td>
          <td>${row.residue}</td>
          <td>${row.quantity}</td>
          <td>${row.value}</td>
          <td>${row.consent}</td>
        </tr>
      `
    )
    .join("");
}

function updateSearchFilters() {
  state.search = document.getElementById("marketSearch").value.trim();
  state.residueFilter = document.getElementById("residueFilter").value;
  state.districtFilter = document.getElementById("districtFilter").value;
  state.priceCap = Number(document.getElementById("priceCap").value) || 2500;
  renderMarketplace();
}

async function handleListingSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);

  const payload = {
    title: `${data.get("residue") || "Residue"} listing`,
    residue_type: data.get("residue") || "Rice Straw",
    source_crop: data.get("cropType") || "Rice",
    quantity_available: Number(data.get("quantity")) || 1,
    unit: data.get("unit") || "t",
    quality: data.get("quality") || "Fresh",
    moisture_content: Number(data.get("moisture")) || 14,
    district: data.get("district") || "Local",
    village: "Local village",
    location: `${data.get("district") || "Local"} district`,
    availability_date: data.get("availability") || "2026-10-30",
    price_per_unit: Number(data.get("price")) || 1500,
    status: "active",
    photo_url: "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=900&q=80",
    pickup_or_delivery: "pickup"
  };

  try {
    await ensureAuthenticated();
    const listing = await apiFetch("/api/listings", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    const mappedListing = {
      id: listing.id,
      seller: listing.seller_name || data.get("sellerName") || "New Seller",
      district: listing.district || payload.district,
      residue: listing.residue_type || payload.residue_type,
      crop: listing.source_crop || payload.source_crop,
      quantity: Number(listing.quantity_available || payload.quantity_available),
      unit: listing.unit || payload.unit,
      quality: listing.quality || payload.quality,
      moisture: Number(listing.moisture_content || payload.moisture_content),
      price: Number(listing.price_per_unit || payload.price_per_unit),
      distance: Number(data.get("distance")) || 30,
      availability: listing.availability_date || payload.availability_date,
      status: listing.status || "active",
      image: listing.photo_url || payload.photo_url
    };
    state.listings = [mappedListing, ...state.listings].slice(0, 12);
    form.reset();
    renderMarketplace();
    return;
  } catch (error) {
    console.warn("Listing API request failed", error);
    setNotice(error.message || "Listing could not be saved.", "error");
    return;
  }
}

async function handleResearchSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const payload = {
    respondent_category: data.get("respondent") || "Farmer",
    district: data.get("district") || "Local",
    locality: "Field survey",
    main_crop: data.get("crop") || "Rice",
    residue_type: data.get("residue") || "Rice straw",
    quantity_generated: Number(data.get("quantity")) || 0,
    quantity_reused: 0,
    quantity_sold: 0,
    quantity_burned: 0,
    disposal_cost: 0,
    sale_price: Number(data.get("value")) || 0,
    awareness_level: "moderate",
    consent_given: data.get("consent") === "yes"
  };

  try {
    await ensureAuthenticated();
    const savedRow = await apiFetch("/api/research", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    const row = {
      category: savedRow.respondent_category || payload.respondent_category,
      district: savedRow.district || payload.district,
      crop: savedRow.main_crop || payload.main_crop,
      residue: savedRow.residue_type || payload.residue_type,
      quantity: `${savedRow.quantity_generated || payload.quantity_generated}t`,
      value: `₹${Number(savedRow.sale_price || payload.sale_price).toLocaleString("en-IN")}`,
      consent: savedRow.consent_given ? "Yes" : "Pending"
    };
    state.researchResponses = [row, ...state.researchResponses].slice(0, 6);
    form.reset();
    renderResearchTable();
    return;
  } catch (error) {
    console.warn("Research API request failed", error);
    setNotice(error.message || "Research response could not be saved.", "error");
  }
}

function init() {
  document.querySelectorAll(".role-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      state.role = button.dataset.role;
      renderDashboard();
    });
  });

  document.getElementById("marketSearch").addEventListener("input", updateSearchFilters);
  document.getElementById("residueFilter").addEventListener("change", updateSearchFilters);
  document.getElementById("districtFilter").addEventListener("change", updateSearchFilters);
  document.getElementById("priceCap").addEventListener("input", updateSearchFilters);

  document.getElementById("listingForm").addEventListener("submit", handleListingSubmit);
  document.getElementById("aiEstimatorForm").addEventListener("submit", requestAIEstimate);
  document.getElementById("buyerRequirementForm").addEventListener("submit", requestMatches);
  document.getElementById("researchForm").addEventListener("submit", handleResearchSubmit);
  document.getElementById("authAction").addEventListener("click", () => {
    if (state.apiToken) {
      state.apiToken = "";
      localStorage.removeItem("agriwaste_token");
      state.role = "farmer";
      document.getElementById("authAction").textContent = "Sign in";
      renderDashboard();
      setNotice("You have signed out.");
      return;
    }
    setAuthMode("login");
    document.getElementById("authDialog").showModal();
  });
  document.getElementById("authClose").addEventListener("click", () => document.getElementById("authDialog").close());
  document.getElementById("authSwitch").addEventListener("click", () => {
    setAuthMode(state.authMode === "login" ? "register" : "login");
  });
  document.getElementById("authForm").addEventListener("submit", handleAuthSubmit);

  document.getElementById("buyerResidue").value = "Rice Straw";
  document.getElementById("buyerDistrict").value = "Thanjavur";
  document.getElementById("buyerQty").value = "4";
  document.getElementById("buyerPrice").value = "1700";

  renderDashboard();
  renderMarketplace();
  renderAIResult();
  renderMatches();
  renderResearchTable();
  loadBackendData();
}

init();
