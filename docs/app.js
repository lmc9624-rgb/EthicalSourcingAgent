const DATA_URL = "./data.json";
const TIER_COLORS = { Low: "#65C29A", Watch: "#E2C66F", Elevated: "#F0A15D", High: "#F07878" };
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHTML = value => String(value ?? "").replace(/[&<>\"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char]));
const money = value => `USD ${Number(value).toLocaleString("en-US")}`;
const state = { data: null, profileId: null, map: null, mapLayer: null, markerLayer: null };
const current = () => state.data.profiles.find(profile => profile.id === state.profileId);

function showTab(name) {
  for (const button of $$('[data-tab]')) button.setAttribute("aria-selected", String(button.dataset.tab === name));
  for (const panel of $$('[data-panel]')) panel.classList.toggle("active", panel.dataset.panel === name);
  if (name === "map" && state.map) setTimeout(() => state.map.invalidateSize(), 100);
}

function renderProfile() {
  const profile = current();
  $("#profile-title").textContent = `${profile.name} | ${profile.product}`;
  $("#profile-location").textContent = `${profile.facility_context}, Taiwan · ${profile.interviews} workers interviewed`;
  $("#metric-tier").textContent = profile.tier;
  $("#metric-score").textContent = `${profile.score.toFixed(1)} / 100`;
  $("#metric-confidence").textContent = `${profile.confidence} (${profile.confidence_score.toFixed(2)})`;
  $("#metric-sample").textContent = String(profile.interviews);
  $("#profile-summary").textContent = `${profile.interviews} interviewed workers (${profile.workers}); fees ${profile.fees}. ${profile.debt_evidence}`;
  $("#profile-response").textContent = profile.response;
  $("#profile-indicators").innerHTML = profile.ilo_indicators.map(item => `<span class="pill">${escapeHTML(item.replaceAll("_", " "))}</span>`).join("");
  $("#profile-tier-reason").textContent = profile.tier_reason;
  renderSignals(profile);
  renderConnections(profile);
  renderDebtComparison();
  if (state.map) renderMap(profile);
}

function renderSignals(profile) {
  $("#signals").innerHTML = profile.signals.map((signal, index) => `
    <details class="evidence" ${index === 0 ? "open" : ""}>
      <summary>${escapeHTML(signal.claim)} · ${escapeHTML(signal.title)}</summary>
      <div class="pill-row"><span class="pill">${escapeHTML(signal.pillar)}</span><span class="pill">Strength ${Number(signal.strength).toFixed(2)}</span></div>
      <p>${escapeHTML(signal.detail).replaceAll("$", "USD ")}</p>
      <p class="small-note">Source IDs: ${escapeHTML(signal.source_ids.join(", "))}</p>
      ${signal.next_step ? `<p><strong>Verification step:</strong> ${escapeHTML(signal.next_step)}</p>` : ""}
    </details>`).join("") || '<p class="empty">No report-tagged evidence for this entity.</p>';
}

function renderConnections(profile) {
  const affiliations = profile.affiliations || [];
  $("#affiliations").innerHTML = affiliations.map(item => `<tr>
    <td>${escapeHTML(item.name)}</td><td>${escapeHTML(item.relationship)}</td>
    <td>${escapeHTML(item.locality)}, ${escapeHTML(item.country)}</td><td>${escapeHTML(item.basis)}</td>
      <td>${item.own_score != null ? `Own evidence ${Number(item.own_score).toFixed(1)}/100 · ${escapeHTML(item.tier)}` : `Linked exposure ${Number(item.linked_score).toFixed(1)}/100; not an independent finding`}</td>
  </tr>`).join("") || '<tr><td colspan="5">No report-named recruiter or corporate affiliate for this profile.</td></tr>';
  $("#buyers").innerHTML = (profile.buyers || []).map(item => `<tr>
    <td>${escapeHTML(item.company)}</td><td>${escapeHTML(item.country || "Not supplied")}</td>
    <td>${escapeHTML(item.status)}</td><td>Potential Tier 1 downstream only if verified</td>
  </tr>`).join("") || '<tr><td colspan="4">No contacted buyers named in the supplied brief.</td></tr>';
}

function renderDebtComparison() {
  const profiles = [...state.data.debt_comparison].sort((a, b) => a.fee_low_usd - b.fee_low_usd);
  const maxFee = 7000;
  $("#fee-chart").innerHTML = profiles.map(item => {
    const left = item.fee_low_usd / maxFee * 100;
    const width = Math.max((item.fee_high_usd - item.fee_low_usd) / maxFee * 100, 1);
    return `<div class="fee-row"><div class="fee-name">${escapeHTML(item.company)}</div>
      <div class="fee-track" title="${escapeHTML(item.debt_evidence)}"><span class="fee-range" style="left:${left}%;width:${width}%"></span></div>
      <div class="fee-label">${money(item.fee_low_usd)}–${money(item.fee_high_usd)}</div></div>`;
  }).join("");
  $("#debt-rows").innerHTML = profiles.map(item => `<tr>
    <td>${escapeHTML(item.company)}</td><td>${escapeHTML(item.worker_origin_country)}</td>
    <td>${item.workers_with_reported_fees} of ${item.workers_interviewed}</td>
    <td>${money(item.fee_low_usd)}–${money(item.fee_high_usd)}</td><td>${escapeHTML(item.debt_evidence)}</td>
    <td>${item.monthly_broker_fee_usd ? `${money(item.monthly_broker_fee_usd[0])}–${money(item.monthly_broker_fee_usd[1])}` : "Not quantified in company summary"}</td>
  </tr>`).join("");
}

function makeIcon(type, label) {
  const symbol = type === "buyer" ? "◆" : type === "port" ? "⚓" : type === "worker" ? "↗" : type === "factory" ? "F" : "A";
  return L.divIcon({ className: "", html: `<span class="map-marker ${type}" title="${escapeHTML(label)}">${symbol}</span>`, iconSize: [30, 30], iconAnchor: [15, 15] });
}

function selectMapEntity(info) {
  $("#selected-name").textContent = info.name;
  $("#selected-type").textContent = info.type;
  $("#selected-location").textContent = info.location;
  $("#selected-score").textContent = info.score || "Not scored";
  $("#selected-detail").textContent = info.detail;
  $("#selected-source").textContent = info.source;
}

function renderMap(profile) {
  if (!state.map) return;
  state.mapLayer.clearLayers();
  state.markerLayer.clearLayers();
  function marker(lat, lon, type, label, info) {
    L.marker([lat, lon], { icon: makeIcon(type, label), title: label })
      .on("click", () => selectMapEntity(info)).addTo(state.markerLayer);
  }
  function route(start, end, color, label) {
    L.polyline([start, end], { color, weight: 2, opacity: .78, dashArray: "7 6" }).bindTooltip(label).addTo(state.mapLayer);
  }

  for (const item of state.data.profiles) {
    const [lat, lon] = item.position;
    marker(lat, lon, "factory", item.name, {
      name: item.name, type: `Investigated manufacturer · ${item.tier} · score ${item.score.toFixed(1)}/100`,
      location: `${item.facility_context}, Taiwan · ${item.location_precision}`,
      score: `${item.score.toFixed(1)}/100`,
      detail: `${item.interviews} interviewees; reported fees ${item.fees}. ${item.debt_evidence}`,
      source: "User-supplied summary attributed to the Transparentem brief; not independently verified."
    });
  }

  const originCode = profile.worker_origin_country;
  const originPosition = state.data.country_centroids[originCode];
  if (originPosition) {
    marker(originPosition[0], originPosition[1], "worker", `${originCode} worker-origin context`, {
      name: `Worker-origin context · ${originCode}`, type: "Reported worker-origin country; context only",
      location: `Country centroid ${originCode}; no individual home locations are mapped`,
      score: "Not scored",
      detail: "Worker-origin context is not a goods supplier, shipment origin, or country implicated in the reported conduct.",
      source: "Origin country is taken from the user-supplied case summary."
    });
    route(originPosition, profile.position, "#72afd1", `Reported worker-origin context (${originCode}); not a goods route.`);
  }

  for (const affiliate of profile.affiliations || []) {
    const position = state.data.country_centroids[affiliate.country];
    if (!position) continue;
      marker(position[0], position[1], "affiliate", affiliate.name, {
        name: affiliate.name, type: affiliate.relationship,
        location: `${affiliate.locality}, ${affiliate.country}`,
        score: affiliate.own_score != null ? `${Number(affiliate.own_score).toFixed(1)}/100 · ${affiliate.tier}` : `Association-weighted exposure ${Number(affiliate.linked_score).toFixed(1)}/100`,
        detail: affiliate.basis,
        source: "Report-attributed relationship; independently verify. Not a confirmed supply edge."
      });
    route(profile.position, position, "#e2c66f", affiliate.relationship);
  }

  const markets = new Map();
  for (const buyer of profile.buyers || []) {
    if (!buyer.country || !state.data.country_centroids[buyer.country]) continue;
    if (!markets.has(buyer.country)) markets.set(buyer.country, []);
    markets.get(buyer.country).push(buyer);
  }
  for (const [country, buyers] of markets) {
    const position = state.data.country_centroids[country];
    const names = buyers.map(item => item.company).join(", ");
    marker(position[0], position[1], "buyer", `Possible buyers · ${country}`, {
      name: `Possible buyer market · ${country}`, type: "Contacted buyer market; unconfirmed",
      location: `Country centroid ${country}; not corporate headquarters or shipment destination`,
      score: "Not scored; buyer links are unconfirmed", detail: names,
      source: "The report names these companies as possible/former connections; no sale or shipment is confirmed here."
    });
    route(profile.position, position, "#607a96", `Possible buyer link: ${names} · unconfirmed`);
  }

  for (const port of state.data.ports) {
    marker(port.lat, port.lon, "port", port.name, {
      name: port.name, type: "Taiwan commercial port · context only", location: port.location,
      score: "Not scored", detail: "General port location; no company-specific shipping record is linked.",
      source: "Context point only, not an inferred shipment route."
    });
  }
}

function renderOverview() {
  const p = current();
  $("#overview-panel").innerHTML = `<div class="two-col">
    <section class="card"><h2>Worker evidence</h2><p>${p.interviews} interviews · ${escapeHTML(p.workers)} · reported fees ${escapeHTML(p.fees)}</p>
    <p>${escapeHTML(p.debt_evidence)}</p><h3>Reported ILO indicators</h3><div class="pill-row">${p.ilo_indicators.map(x => `<span class="pill">${escapeHTML(x.replaceAll("_", " "))}</span>`).join("")}</div></section>
    <section class="card"><h2>Company response, per report</h2><p>${escapeHTML(p.response)}</p><h3>Assessment rationale</h3><p>${escapeHTML(p.tier_reason)}</p>
    <p class="small-note">Illustrative score. Report allegations have not been independently verified by SourceSight.</p></section></div>`;
}

function renderEvidence() {
  const p = current();
  $("#evidence-list").innerHTML = (p.signals || []).map((signal, index) => `<details class="evidence" ${index === 0 ? "open" : ""}>
    <summary>${escapeHTML(signal.claim)} · ${escapeHTML(signal.title)}</summary>
    <div class="evidence-meta"><span class="pill">${escapeHTML(signal.pillar)}</span><span class="pill">Strength ${Number(signal.strength).toFixed(2)}</span></div>
    <p>${escapeHTML(signal.detail).replaceAll("$", "USD ")}</p><p class="small-note">Source IDs: ${escapeHTML(signal.source_ids.join(", "))}</p>
    ${signal.next_step ? `<p><strong>Verification:</strong> ${escapeHTML(signal.next_step)}</p>` : ""}</details>`).join("") || '<p class="empty">No report-tagged evidence for this profile.</p>';
}

function renderConnections() {
  const p = current();
  $("#affiliation-rows").innerHTML = (p.affiliations || []).map(item => `<tr><td>${escapeHTML(item.name)}</td><td>${escapeHTML(item.relationship)}</td><td>${escapeHTML(item.country)}</td><td>${escapeHTML(item.basis)}</td><td>${item.own_score != null ? `Own evidence ${Number(item.own_score).toFixed(1)}/100 · ${escapeHTML(item.tier)}` : `Linked exposure ${Number(item.linked_score).toFixed(1)}/100; not an independent finding`}</td></tr>`).join("") || '<tr><td colspan="5">No corporate affiliation named in this brief.</td></tr>';
  $("#buyer-rows").innerHTML = (p.buyers || []).map(item => `<tr><td>${escapeHTML(item.company)}</td><td>${escapeHTML(item.country || "Not supplied")}</td><td>${escapeHTML(item.status)}</td><td>Possible connection; not a confirmed supply edge</td></tr>`).join("") || '<tr><td colspan="4">No contacted buyers named in the supplied brief.</td></tr>';
}

function renderDebt() {
  const profiles = [...state.data.debt_comparison].sort((a,b) => a.fee_low_usd - b.fee_low_usd);
  const max = 7000;
  $("#fee-ranges").innerHTML = profiles.map(item => `<div class="fee-row"><div class="fee-name">${escapeHTML(item.company)}</div><div class="fee-track" title="${escapeHTML(item.debt_evidence)}"><span class="fee-range" style="left:${item.fee_low_usd/max*100}%;width:${Math.max((item.fee_high_usd-item.fee_low_usd)/max*100,1)}%"></span></div><div class="fee-label">${money(item.fee_low_usd)}–${money(item.fee_high_usd)}</div></div>`).join("");
  $("#debt-rows").innerHTML = profiles.map(item => `<tr><td>${escapeHTML(item.company)}</td><td>${escapeHTML(item.worker_origin_country)}</td><td>${item.workers_with_reported_fees} of ${item.workers_interviewed}</td><td>${money(item.fee_low_usd)}–${money(item.fee_high_usd)}</td><td>${escapeHTML(item.debt_evidence)}</td><td>${item.monthly_broker_fee_usd ? `${money(item.monthly_broker_fee_usd[0])}–${money(item.monthly_broker_fee_usd[1])}` : "Not quantified"}</td></tr>`).join("");
}

function render() {
  const profile = current();
  $("#profile-select").value = profile.id;
  $("#profile-title").textContent = `${profile.name} | ${profile.product}`;
  $("#profile-location").textContent = `${profile.facility_context}, Taiwan · ${profile.interviews} interviews`;
  $("#metric-tier").textContent = profile.tier;
  $("#metric-score").textContent = `${profile.score.toFixed(1)} / 100`;
  $("#metric-confidence").textContent = `${profile.confidence} (${profile.confidence_score.toFixed(2)})`;
  $("#metric-sample").textContent = String(profile.interviews);
  $("#report-summary").textContent = `${profile.fees}: ${profile.debt_evidence}`.replaceAll("$", "USD ");
  $("#profile-response").textContent = profile.response;
  $("#profile-indicators").innerHTML = profile.ilo_indicators.map(item => `<span class="pill">${escapeHTML(item.replaceAll("_", " "))}</span>`).join("");
  $("#profile-reason").textContent = profile.tier_reason;
  renderOverview(); renderEvidence(); renderConnections(); renderDebt();
  if (state.map) renderMap(profile);
}

function initMap() {
  if (!window.L) { $("#map").innerHTML = '<p class="empty">Map library unavailable. Use the entity tables below.</p>'; return; }
  state.map = L.map("map", { scrollWheelZoom: false }).setView([24.5, 121], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: '&copy; OpenStreetMap contributors' }).addTo(state.map);
  state.mapLayer = L.layerGroup().addTo(state.map);
  state.markerLayer = L.markerClusterGroup({
    showCoverageOnHover: false,
    spiderfyOnMaxZoom: true,
    zoomToBoundsOnClick: true,
    maxClusterRadius: 34,
    iconCreateFunction(cluster) {
      const count = cluster.getChildCount();
      return L.divIcon({ html: `<span>${count}</span>`, className: "cluster-bubble", iconSize: [36, 36] });
    }
  }).addTo(state.map);
  renderMap(current());
}

async function start() {
  try { const response=await fetch("./data.json"); if(!response.ok) throw new Error(`Report data unavailable (${response.status})`); state.data=await response.json(); }
  catch (error) { $("#app").innerHTML=`<p class="empty">Could not load SourceSight data: ${escapeHTML(error.message)}</p>`; return; }
  for (const profile of state.data.profiles) { const option=document.createElement("option"); option.value=profile.id; option.textContent=`${profile.name} | ${profile.product}`; $("#profile-select").append(option); }
  state.profileId=state.data.profiles[0].id;
  $("#profile-select").addEventListener("change", event => { state.profileId=event.target.value; render(); });
  $$('[data-tab]').forEach(button => button.addEventListener("click", () => {
    $$('[data-tab]').forEach(item => item.setAttribute("aria-selected", String(item === button)));
    $$('[data-panel]').forEach(panel => panel.classList.toggle("active", panel.dataset.panel === button.dataset.tab));
    if (button.dataset.tab === "map" && state.map) setTimeout(() => state.map.invalidateSize(), 100);
  }));
  render(); initMap();
}
start();
