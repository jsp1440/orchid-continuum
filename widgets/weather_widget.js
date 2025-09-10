/**
 * Orchid Continuum Weather Badge
 * Given timestamp (ISO 8601) and lat/lon, fetch historical weather & render a small badge.
 * Uses Open-Meteo archive (no API key). https://open-meteo.com/
 */
async function orchidWeatherBadge({container, lat, lon, isoTime}) {
  if (!container) return;
  try {
    const dt = new Date(isoTime);
    const date = dt.toISOString().slice(0,10);
    const hour = dt.getUTCHours();
    const url = new URL('https://archive-api.open-meteo.com/v1/archive');
    url.searchParams.set('latitude', lat);
    url.searchParams.set('longitude', lon);
    url.searchParams.set('start_date', date);
    url.searchParams.set('end_date', date);
    url.searchParams.set('hourly', 'temperature_2m,relative_humidity_2m,dew_point_2m,pressure_msl,wind_speed_10m');
    url.searchParams.set('timezone', 'UTC');
    const resp = await fetch(url.toString());
    const data = await resp.json();
    const idx = hour; // hour-of-day in UTC
    const T = data.hourly?.temperature_2m?.[idx];
    const RH = data.hourly?.relative_humidity_2m?.[idx];
    const DP = data.hourly?.dew_point_2m?.[idx];
    const P  = data.hourly?.pressure_msl?.[idx];
    const W  = data.hourly?.wind_speed_10m?.[idx];

    function vpd_kpa_c(Tc, RHp) {
      const es = 0.6108 * Math.exp((17.27*Tc)/(Tc+237.3)); // kPa
      return es * (1 - (RHp/100));
    }
    const vpd = (T!=null && RH!=null) ? vpd_kpa_c(T, RH).toFixed(2) : '—';

    const badge = document.createElement('div');
    badge.style.fontFamily = 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif';
    badge.style.fontSize = '12px';
    badge.style.border = '1px solid #ddd';
    badge.style.borderRadius = '8px';
    badge.style.padding = '8px 10px';
    badge.style.display = 'inline-flex';
    badge.style.gap = '10px';
    badge.style.alignItems = 'center';
    badge.style.background = '#fafafa';

    badge.innerHTML = `
      <strong>Weather @ capture</strong>
      <span>Temp: ${T!=null?T.toFixed(1)+'°C':'—'}</span>
      <span>RH: ${RH!=null?RH+'%':'—'}</span>
      <span>VPD: ${vpd} kPa</span>
      <span>Pressure: ${P!=null?P.toFixed(0)+' hPa':'—'}</span>
      <span>Wind: ${W!=null?W.toFixed(1)+' m/s':'—'}</span>
    `;
    container.replaceChildren(badge);
  } catch (e) {
    container.textContent = 'Weather unavailable';
    console.error('Weather badge error', e);
  }
}
window.orchidWeatherBadge = orchidWeatherBadge;