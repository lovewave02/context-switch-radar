const map = L.map('map').setView([36.35, 127.8], 7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const markers = L.layerGroup().addTo(map);

const form = document.getElementById('memoryForm');
const listEl = document.getElementById('memoryList');
const statsEl = document.getElementById('stats');
const filterBtn = document.getElementById('filterBtn');
const resetBtn = document.getElementById('resetBtn');
const seedBtn = document.getElementById('seedBtn');

map.on('click', (e) => {
  document.getElementById('lat').value = e.latlng.lat.toFixed(6);
  document.getElementById('lon').value = e.latlng.lng.toFixed(6);
});

async function fetchJson(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `request failed: ${res.status}`);
  }
  return res.json();
}

function itemHtml(item) {
  return `
    <strong>${item.title}</strong>
    <div class="meta">${item.memory_date} | ${item.city || '-'} | ${item.climate_tag || '-'} | ${item.temp_c ?? '-'}°C</div>
    <div>${item.note}</div>
    <button class="del" data-id="${item.id}">삭제</button>
  `;
}

function renderList(items) {
  listEl.innerHTML = '';
  for (const it of items) {
    const li = document.createElement('li');
    li.innerHTML = itemHtml(it);
    listEl.appendChild(li);
  }

  listEl.querySelectorAll('.del').forEach((btn) => {
    btn.addEventListener('click', async () => {
      await fetchJson(`/api/climate-memories/${btn.dataset.id}`, { method: 'DELETE' });
      await refresh();
    });
  });
}

function renderMap(items) {
  markers.clearLayers();
  const bounds = [];
  items.forEach((it) => {
    const m = L.marker([it.lat, it.lon]).addTo(markers);
    m.bindPopup(`<strong>${it.title}</strong><br/>${it.memory_date}<br/>${it.city || ''}<br/>${it.note}`);
    bounds.push([it.lat, it.lon]);
  });
  if (bounds.length > 0) map.fitBounds(bounds, { padding: [24, 24] });
}

function renderStats(stats) {
  const topTagText = (stats.top_tags || []).map((x) => `${x.tag}(${x.count})`).join(', ') || '-';
  const yearsText = (stats.yearly_counts || []).map((x) => `${x.year}:${x.count}`).join(' | ') || '-';
  statsEl.innerHTML = `
    <span>총 기록: <strong>${stats.total_count}</strong></span>
    <span>평균 기온: <strong>${stats.avg_temp_c ?? '-'}</strong>°C</span>
    <span>상위 태그: <strong>${topTagText}</strong></span>
    <span>연도별: <strong>${yearsText}</strong></span>
  `;
}

async function refresh() {
  const year = document.getElementById('yearFilter').value.trim();
  const tag = document.getElementById('tagFilter').value.trim();
  const params = new URLSearchParams();
  if (year) params.set('year', year);
  if (tag) params.set('tag', tag);

  const list = await fetchJson(`/api/climate-memories?${params.toString()}`);
  const stats = await fetchJson('/api/climate-stats');

  renderList(list);
  renderMap(list);
  renderStats(stats);
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    title: document.getElementById('title').value,
    city: document.getElementById('city').value,
    memory_date: document.getElementById('memoryDate').value,
    climate_tag: document.getElementById('climateTag').value,
    feeling: document.getElementById('feeling').value,
    temp_c: document.getElementById('tempC').value ? Number(document.getElementById('tempC').value) : null,
    lat: Number(document.getElementById('lat').value),
    lon: Number(document.getElementById('lon').value),
    note: document.getElementById('note').value
  };

  await fetchJson('/api/climate-memories', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload)
  });

  form.reset();
  await refresh();
});

filterBtn.addEventListener('click', refresh);
resetBtn.addEventListener('click', async () => {
  document.getElementById('yearFilter').value = '';
  document.getElementById('tagFilter').value = '';
  await refresh();
});

seedBtn.addEventListener('click', async () => {
  await fetchJson('/api/climate-seed', { method: 'POST' });
  await refresh();
});

refresh().catch((err) => {
  console.error(err);
  alert('기후 메모리 지도 로딩 중 오류가 발생했습니다.');
});
