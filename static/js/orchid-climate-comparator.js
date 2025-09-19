/* ======================================================================
   Orchid Continuum — Parallel Photoperiod & Habitat Comparator (All-in-One)
   - Modes: "seasonal" (default), "photoperiod", "calendar", "parallel35"
   - Elevation temp adjustment, solar-time alignment, hemisphere offset
   - Confidence scoring + badges + plain-English insights
   - Strict Orchid-of-the-Day filter (complete species/hybrid rules)
   ====================================================================== */

// ─────────────────────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────────────────────
const toRad = (d) => d * Math.PI / 180;
const mean = (arr) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
const round = (x, d = 0) => Math.round(x * 10 ** d) / 10 ** d;

// Daylength approximation (horticultural-grade). Swap w/ NOAA calc if desired.
function approximateDaylengthHours(lat, date) {
  const start = new Date(Date.UTC(date.getUTCFullYear(), 0, 0));
  const N = Math.floor((+date - +start) / 86400000);
  const decl = 23.44 * Math.PI / 180 * Math.sin(2 * Math.PI * (N - 80) / 365);
  const phi = toRad(lat);
  const cosH = -Math.tan(phi) * Math.tan(decl);
  if (cosH <= -1) return 24;
  if (cosH >= 1) return 0;
  const H = Math.acos(cosH);
  return 2 * H * 180 / Math.PI / 15;
}

// Align "solar noon" by longitude (~15° = 1 hour)
function solarHourOffsetHours(userLon, habitatLon) {
  return (habitatLon - userLon) / 15;
}

// Opposite hemispheres? (coarse 6-month hint)
function hemisphereOffsetMonths(userLat, habitatLat) {
  if (userLat === 0 || habitatLat === 0) return 0;
  const opposite = (userLat > 0 && habitatLat < 0) || (userLat < 0 && habitatLat > 0);
  return opposite ? 6 : 0;
}

// Environmental distance over monthly normals (weighted Euclidean)
function monthDistance(a, b) {
  const dtmin = a.tmin - b.tmin;
  const dtmax = a.tmax - b.tmax;
  const drh = a.rh - b.rh;
  const dpp = a.precip - b.precip;
  return Math.sqrt((dtmin * dtmin) * 0.5 + (dtmax * dtmax) * 0.5 + (drh * drh) * 0.2 + (dpp * dpp) * 0.1);
}

// Dry adiabatic lapse temp adjustment (approx). Positive = LOCAL raised to compare to habitat.
function elevationAdjustC(localElev, habitatElev) {
  if (localElev == null || habitatElev == null) return 0;
  const deltaKm = (habitatElev - localElev) / 1000;
  const lapseCperKm = 9.8;
  return deltaKm * lapseCperKm;
}

// Circular shift of hourly habitat series
function shiftSeries(arr, hours) {
  const n = arr.length || 24;
  const out = new Array(n);
  for (let i = 0; i < n; i++) out[(i + hours + n) % n] = arr[i];
  return out;
}

// ─────────────────────────────────────────────────────────────
// MOCK CLIMATE API (Replace with real weather service)
// ─────────────────────────────────────────────────────────────
class MockClimateAPI {
  async getHourly(latlon, isoDate) {
    // Mock hourly data - replace with real weather API
    const baseTemp = 20 + (latlon.lat / 10) + Math.sin(Date.parse(isoDate) / 86400000) * 5;
    const baseRH = 60 + (latlon.lat / 5);
    
    return Array.from({ length: 24 }, (_, hour) => ({
      t: baseTemp + Math.sin(hour * Math.PI / 12) * 8,
      rh: Math.max(30, Math.min(95, baseRH + Math.cos(hour * Math.PI / 12) * 20))
    }));
  }

  async getMonthlyNormals(latlon) {
    // Mock monthly normals - replace with real climate data
    const baseTempMin = 10 + (latlon.lat / 5);
    const baseTempMax = 25 + (latlon.lat / 5);
    const baseRH = 65 + (latlon.lat / 8);
    
    return Array.from({ length: 12 }, (_, i) => ({
      month: i + 1,
      tmin: baseTempMin + Math.sin((i + 1) * Math.PI / 6) * 10,
      tmax: baseTempMax + Math.sin((i + 1) * Math.PI / 6) * 10,
      rh: Math.max(40, Math.min(90, baseRH + Math.cos((i + 1) * Math.PI / 6) * 15)),
      precip: 50 + Math.sin((i + 1) * Math.PI / 6) * 30
    }));
  }

  async nearestStationMeta(latlon) {
    // Mock station metadata - replace with real station data
    return {
      distanceKm: Math.random() * 200,
      elev: 100 + Math.random() * 1000
    };
  }
}

// ─────────────────────────────────────────────────────────────
// MODES — main orchestration
// ─────────────────────────────────────────────────────────────
export async function compareHabitat(
  climate,
  user,
  habitat,
  dateISO,
  mode = "seasonal"
) {
  const date = new Date(dateISO);
  const badges = [];
  const details = {};
  let confidence = "High";
  const insights = [];

  // Confidence inputs
  const userStation = await climate.nearestStationMeta(user);
  const habStation = await climate.nearestStationMeta(habitat);
  const elevAdjC = elevationAdjustC(user.elev, habitat.elev);
  details.stationDistanceKm = habStation.distanceKm;
  details.elevationAdjustmentC = elevAdjC;

  // Heuristic confidence
  const distPenalty = habStation.distanceKm > 150 ? 1 : 0;
  const elevPenalty = Math.abs(elevAdjC) > 4 ? 1 : 0;
  const penalties = distPenalty + elevPenalty;
  confidence = penalties === 0 ? "High" : penalties === 1 ? "Medium" : "Low";

  if (mode === "calendar") {
    badges.push("Calendar mode");
    return runCalendarMode(climate, user, habitat, date, badges, confidence, details, insights, elevAdjC);
  }
  if (mode === "photoperiod") {
    badges.push("Photoperiod aligned");
    return runPhotoperiodMode(climate, user, habitat, date, badges, confidence, details, insights, elevAdjC);
  }
  if (mode === "parallel35") {
    badges.push("35th Parallel comparator");
    return runParallel35Mode(climate, user, habitat, date, badges, confidence, details, insights, elevAdjC);
  }
  if (mode === "orbit") {
    badges.push("Orbit & Rays visualization");
    return runOrbitMode(climate, user, habitat, date, badges, confidence, details, insights, elevAdjC);
  }
  // default
  badges.push("Seasonal aligned");
  return runSeasonalMode(climate, user, habitat, date, badges, confidence, details, insights, elevAdjC);
}

// ── Calendar (raw today-vs-today)
async function runCalendarMode(
  climate, user, habitat, date, badges, confidence, details, insights, elevAdjC
) {
  const userHourly = await climate.getHourly(user, date.toISOString());
  const habHourly = await climate.getHourly(habitat, date.toISOString());

  const hourly = userHourly.map((pt, i) => ({
    hour: `${i}:00`,
    local: { t: pt.t + elevAdjC, rh: pt.rh },
    habitat: habHourly[i] ?? habHourly[habHourly.length - 1]
  }));

  const dailyLocalMeanT = mean(hourly.map(h => h.local.t));
  const dailyLocalMeanRH = mean(hourly.map(h => h.local.rh));
  const dailyHabMeanT = mean(hourly.map(h => h.habitat.t));
  const dailyHabMeanRH = mean(hourly.map(h => h.habitat.rh));

  const deltas = {
    tC: round(dailyLocalMeanT - dailyHabMeanT, 1),
    rhPct: round(dailyLocalMeanRH - dailyHabMeanRH, 1)
  };

  insights.push(`Today vs. today: ΔT=${deltas.tC}°C, ΔRH=${deltas.rhPct}%.`);
  return { mode: "calendar", badges, confidence, hourly, deltas, insights, details };
}

// ── Seasonal (recommended default)
async function runSeasonalMode(
  climate, user, habitat, date, badges, confidence, details, insights, elevAdjC
) {
  const userNormals = await climate.getMonthlyNormals(user);
  const habNormals = await climate.getMonthlyNormals(habitat);

  const m = date.getMonth() + 1;
  const uM = userNormals.find(n => n.month === m);

  // Best habitat month analog
  let best = { month: 1, dist: Number.POSITIVE_INFINITY };
  for (const h of habNormals) {
    const d = monthDistance(uM, h);
    if (d < best.dist) best = { month: h.month, dist: d };
  }

  const hemisOffset = hemisphereOffsetMonths(user.lat, habitat.lat);
  if (hemisOffset) badges.push(`Hemisphere offset ~${hemisOffset} months`);
  details.hemisphereOffsetMonths = hemisOffset;

  // Hourly (today) for visual overlay
  const userHourly = await climate.getHourly(user, date.toISOString());
  const habHourly = await climate.getHourly(habitat, date.toISOString());
  const hourly = userHourly.map((pt, i) => ({
    hour: `${i}:00`,
    local: { t: pt.t + elevAdjC, rh: pt.rh },
    habitat: habHourly[i] ?? habHourly[habHourly.length - 1]
  }));

  const seasonal = habNormals.map(h => {
    const mid = (h.tmin + h.tmax) / 2;
    return { month: h.month, min: h.tmin, max: h.tmax, mean: mid };
  });

  const uMean = (uM.tmin + uM.tmax) / 2 + elevAdjC;
  const hBest = habNormals.find(h => h.month === best.month);
  const hMean = (hBest.tmin + hBest.tmax) / 2;

  const deltas = { tC: round(uMean - hMean, 1), rhPct: round(uM.rh - hBest.rh, 1) };
  insights.push(`Seasonal analog (your M${m} vs habitat M${best.month}): ΔT=${deltas.tC}°C, ΔRH=${deltas.rhPct}%.`);
  return { mode: "seasonal", badges, confidence, hourly, seasonal, deltas, insights, details };
}

// ── Photoperiod (precise circadian alignment)
async function runPhotoperiodMode(
  climate, user, habitat, date, badges, confidence, details, insights, elevAdjC
) {
  const userDL = approximateDaylengthHours(user.lat, date);
  // Find habitat date with closest daylength
  let bestDate = new Date(date);
  let bestDelta = Number.POSITIVE_INFINITY;
  for (let k = -183; k <= 183; k++) {
    const d = new Date(date);
    d.setUTCDate(d.getUTCDate() + k);
    const dl = approximateDaylengthHours(habitat.lat, d);
    const delta = Math.abs(dl - userDL);
    if (delta < bestDelta) { bestDelta = delta; bestDate = d; }
  }

  const userHourly = await climate.getHourly(user, date.toISOString());
  const habHourlyRaw = await climate.getHourly(habitat, bestDate.toISOString());

  const shiftH = solarHourOffsetHours(user.lon, habitat.lon);
  details.habitatDateUsed = bestDate.toISOString().slice(0, 10);
  details.solarAligned = true;
  badges.push("Solar time aligned");

  const habHourly = shiftSeries(habHourlyRaw, Math.round(shiftH));

  const hourly = userHourly.map((pt, i) => ({
    hour: `${i}:00`,
    local: { t: pt.t + elevAdjC, rh: pt.rh },
    habitat: habHourly[i] ?? habHourly[habHourly.length - 1]
  }));

  const uMeanT = mean(hourly.map(h => h.local.t));
  const hMeanT = mean(hourly.map(h => h.habitat.t));
  const uMeanRH = mean(hourly.map(h => h.local.rh));
  const hMeanRH = mean(hourly.map(h => h.habitat.rh));
  const deltas = { tC: round(uMeanT - hMeanT, 1), rhPct: round(uMeanRH - hMeanRH, 1) };

  insights.push(`Photoperiod match (equal daylength & solar hour). Habitat date: ${details.habitatDateUsed}. ΔT=${deltas.tC}°C, ΔRH=${deltas.rhPct}%.`);
  return { mode: "photoperiod", badges, confidence, hourly, deltas, insights, details };
}

// ── 35th-Parallel special (decorated seasonal with parallel insights)
async function runParallel35Mode(
  climate, user, habitat, date, badges, confidence, details, insights, elevAdjC
) {
  details.latBandUsed = 35;

  const orchidNear35 = Math.abs(habitat.lat) >= 32 && Math.abs(habitat.lat) <= 38;
  const growerNear35 = Math.abs(user.lat) >= 32 && Math.abs(user.lat) <= 38;
  if (orchidNear35) badges.push("Native to ~35° latitude");
  if (growerNear35) badges.push("You grow at ~35° latitude");

  // Use seasonal logic as base
  const result = await runSeasonalMode(climate, user, habitat, date, badges, confidence, details, insights, elevAdjC);
  result.mode = "parallel35";

  // Add 35th parallel specific insights
  if (orchidNear35 && growerNear35) {
    insights.push("🌍 Both you and this orchid are near the 35th parallel - a global crossroad of temperate orchid diversity!");
  } else if (orchidNear35) {
    insights.push("🌍 This orchid is from the 35th parallel region - known for Mediterranean and temperate climates.");
  } else if (growerNear35) {
    insights.push("🌍 You're growing at the 35th parallel - perfect for many temperate orchid species!");
  }

  return result;
}

// ─────────────────────────────────────────────────────────────
// CHART RENDERING
// ─────────────────────────────────────────────────────────────
export function renderClimateChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;

  // Clear canvas
  ctx.clearRect(0, 0, width, height);

  if (data.hourly) {
    renderHourlyChart(ctx, width, height, data.hourly);
  } else if (data.seasonal) {
    renderSeasonalChart(ctx, width, height, data.seasonal);
  }
}

function renderHourlyChart(ctx, width, height, hourly) {
  const margin = 40;
  const chartWidth = width - 2 * margin;
  const chartHeight = height - 2 * margin;

  // Find temperature range
  const allTemps = hourly.flatMap(h => [h.local.t, h.habitat.t]);
  const minTemp = Math.min(...allTemps) - 2;
  const maxTemp = Math.max(...allTemps) + 2;

  // Draw axes
  ctx.strokeStyle = '#666';
  ctx.beginPath();
  ctx.moveTo(margin, margin);
  ctx.lineTo(margin, height - margin);
  ctx.lineTo(width - margin, height - margin);
  ctx.stroke();

  // Draw temperature lines
  ctx.lineWidth = 2;

  // Local temperature (blue)
  ctx.strokeStyle = '#3498db';
  ctx.beginPath();
  hourly.forEach((h, i) => {
    const x = margin + (i / (hourly.length - 1)) * chartWidth;
    const y = height - margin - ((h.local.t - minTemp) / (maxTemp - minTemp)) * chartHeight;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Habitat temperature (red)
  ctx.strokeStyle = '#e74c3c';
  ctx.beginPath();
  hourly.forEach((h, i) => {
    const x = margin + (i / (hourly.length - 1)) * chartWidth;
    const y = height - margin - ((h.habitat.t - minTemp) / (maxTemp - minTemp)) * chartHeight;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Add legend
  ctx.fillStyle = '#3498db';
  ctx.fillRect(margin, 10, 15, 15);
  ctx.fillStyle = '#333';
  ctx.font = '12px Arial';
  ctx.fillText('Your Location', margin + 20, 22);

  ctx.fillStyle = '#e74c3c';
  ctx.fillRect(margin + 120, 10, 15, 15);
  ctx.fillStyle = '#333';
  ctx.fillText('Orchid Habitat', margin + 140, 22);
}

function renderSeasonalChart(ctx, width, height, seasonal) {
  const margin = 40;
  const chartWidth = width - 2 * margin;
  const chartHeight = height - 2 * margin;

  // Find temperature range
  const allTemps = seasonal.flatMap(s => [s.min, s.max]);
  const minTemp = Math.min(...allTemps) - 2;
  const maxTemp = Math.max(...allTemps) + 2;

  // Draw axes
  ctx.strokeStyle = '#666';
  ctx.beginPath();
  ctx.moveTo(margin, margin);
  ctx.lineTo(margin, height - margin);
  ctx.lineTo(width - margin, height - margin);
  ctx.stroke();

  // Draw seasonal bands
  ctx.fillStyle = 'rgba(231, 76, 60, 0.3)';
  seasonal.forEach((s, i) => {
    const x = margin + (i / (seasonal.length - 1)) * chartWidth;
    const yMin = height - margin - ((s.min - minTemp) / (maxTemp - minTemp)) * chartHeight;
    const yMax = height - margin - ((s.max - minTemp) / (maxTemp - minTemp)) * chartHeight;
    const barWidth = chartWidth / seasonal.length * 0.8;
    ctx.fillRect(x - barWidth / 2, yMax, barWidth, yMin - yMax);
  });

  // Draw mean line
  ctx.strokeStyle = '#e74c3c';
  ctx.lineWidth = 2;
  ctx.beginPath();
  seasonal.forEach((s, i) => {
    const x = margin + (i / (seasonal.length - 1)) * chartWidth;
    const y = height - margin - ((s.mean - minTemp) / (maxTemp - minTemp)) * chartHeight;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

// ── Orbit Mode (Orbital visualization)
async function runOrbitMode(
  climate, user, habitat, date, badges, confidence, details, insights, elevAdjC
) {
  // For orbit mode, we return basic comparison data but the main visualization is handled separately
  const userHourly = await climate.getHourly(user, date.toISOString());
  const habHourly = await climate.getHourly(habitat, date.toISOString());

  const hourly = userHourly.map((pt, i) => ({
    hour: `${i}:00`,
    local: { t: pt.t + elevAdjC, rh: pt.rh },
    habitat: habHourly[i] ?? habHourly[habHourly.length - 1]
  }));

  insights.push("Orbital visualization shows Earth's seasonal positions and solar ray dynamics.");
  insights.push("Use latitude lines to compare photoperiods at different latitudes.");
  insights.push("The 35° parallel is highlighted for its seasonal richness and orchid diversity.");
  
  return { 
    mode: "orbit", 
    badges, 
    confidence, 
    hourly, 
    insights, 
    details,
    orbitData: {
      userLat: user.lat,
      habitatLat: habitat.lat,
      date: date
    }
  };
}

// ─────────────────────────────────────────────────────────────
// ORBITAL VISUALIZATION SYSTEM
// ─────────────────────────────────────────────────────────────

// Global state for orbit animation
let orbitAnimationId = null;
let orbitAnimationRunning = false;
let currentDayOfYear = 0;
let focusLatitude = 35; // Default focus on 35th parallel
let enabledLatLines = new Set([35]); // Default to 35° enabled

// Solar declination calculation
function solarDeclination(dayOfYear) {
  return 23.44 * Math.sin(toRad((360 * (dayOfYear - 81)) / 365));
}

// Day of year to month/day string
function dayOfYearToDate(dayOfYear) {
  const date = new Date(2024, 0, 1 + dayOfYear);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Earth position on elliptical orbit
function earthPosition(dayOfYear) {
  // Approximate elliptical orbit (perihelion ≈ DOY 3, aphelion ≈ DOY 185)
  const angle = toRad((dayOfYear / 365) * 360);
  const a = 1.0; // Semi-major axis (normalized)
  const e = 0.0167; // Earth's orbital eccentricity
  const r = a * (1 - e * e) / (1 + e * Math.cos(angle));
  
  return {
    x: r * Math.cos(angle),
    y: r * Math.sin(angle),
    angle: angle
  };
}

// Render orbital visualization
function renderOrbit(canvas, dayOfYear) {
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  const centerX = width / 2;
  const centerY = height / 2;
  const scale = Math.min(width, height) / 3;
  
  // Clear canvas
  ctx.fillStyle = '#1a1a1a';
  ctx.fillRect(0, 0, width, height);
  
  // Draw orbital ellipse
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.ellipse(centerX, centerY, scale, scale * 0.95, 0, 0, 2 * Math.PI);
  ctx.stroke();
  
  // Draw sun at center
  ctx.fillStyle = '#ffd700';
  ctx.beginPath();
  ctx.arc(centerX, centerY, 8, 0, 2 * Math.PI);
  ctx.fill();
  
  // Draw sun rays
  ctx.strokeStyle = 'rgba(255, 215, 0, 0.6)';
  ctx.lineWidth = 2;
  for (let i = 0; i < 12; i++) {
    const angle = (i / 12) * 2 * Math.PI;
    const x1 = centerX + Math.cos(angle) * 15;
    const y1 = centerY + Math.sin(angle) * 15;
    const x2 = centerX + Math.cos(angle) * 25;
    const y2 = centerY + Math.sin(angle) * 25;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }
  
  // Get Earth position
  const earthPos = earthPosition(dayOfYear);
  const earthX = centerX + earthPos.x * scale;
  const earthY = centerY + earthPos.y * scale;
  
  // Draw Earth
  ctx.save();
  ctx.translate(earthX, earthY);
  
  // Earth rotation for axial tilt
  const tilt = toRad(23.44);
  ctx.rotate(earthPos.angle + tilt);
  
  // Draw Earth sphere
  ctx.fillStyle = '#4a90e2';
  ctx.beginPath();
  ctx.arc(0, 0, 12, 0, 2 * Math.PI);
  ctx.fill();
  
  // Draw latitude lines if enabled
  const declination = solarDeclination(dayOfYear);
  
  enabledLatLines.forEach(lat => {
    ctx.strokeStyle = lat === 35 ? '#ff6b6b' : 'rgba(255, 255, 255, 0.8)';
    ctx.lineWidth = lat === focusLatitude ? 2 : 1;
    
    // Draw latitude line
    const latRad = toRad(lat);
    const y = -12 * Math.sin(latRad);
    
    ctx.beginPath();
    ctx.moveTo(-12, y);
    ctx.lineTo(12, y);
    ctx.stroke();
    
    // Label latitude
    ctx.fillStyle = lat === 35 ? '#ff6b6b' : '#fff';
    ctx.font = '10px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(`${lat}°`, 14, y + 3);
  });
  
  // Draw sun rays hitting Earth
  const rayCount = 8;
  for (let i = 0; i < rayCount; i++) {
    const angle = (i / rayCount) * 2 * Math.PI;
    const rayX = Math.cos(angle) * 30;
    const rayY = Math.sin(angle) * 30;
    
    ctx.strokeStyle = 'rgba(255, 215, 0, 0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(-rayX, -rayY);
    ctx.lineTo(rayX, rayY);
    ctx.stroke();
  }
  
  ctx.restore();
  
  // Draw orbital markers for key dates
  const keyDates = [
    { day: 0, label: 'Jan 1', color: '#fff' },
    { day: 3, label: 'Perihelion', color: '#ff6b6b' },
    { day: 80, label: 'Equinox', color: '#4ecdc4' },
    { day: 185, label: 'Aphelion', color: '#ff6b6b' },
    { day: 265, label: 'Equinox', color: '#4ecdc4' }
  ];
  
  keyDates.forEach(marker => {
    const pos = earthPosition(marker.day);
    const x = centerX + pos.x * scale;
    const y = centerY + pos.y * scale;
    
    ctx.fillStyle = marker.color;
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, 2 * Math.PI);
    ctx.fill();
    
    // Label
    ctx.fillStyle = marker.color;
    ctx.font = '9px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(marker.label, x, y - 8);
  });
}

// Update caption with declination and daylength
function updateOrbitCaption(dayOfYear) {
  const declination = solarDeclination(dayOfYear);
  const daylength = approximateDaylengthHours(focusLatitude, new Date(2024, 0, 1 + dayOfYear));
  
  const caption = document.getElementById('orbitCaption');
  if (caption) {
    caption.textContent = `Solar declination: ${declination.toFixed(1)}°, Daylength at ${focusLatitude}°: ${daylength.toFixed(1)} hours`;
  }
}

// ─────────────────────────────────────────────────────────────
// GLOBAL EXPORTS
// ─────────────────────────────────────────────────────────────
window.OrchidClimateComparator = {
  MockClimateAPI,
  compareHabitat,
  renderClimateChart,
  renderOrbit,
  updateOrbitCaption
};