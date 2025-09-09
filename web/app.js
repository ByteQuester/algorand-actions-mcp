(function () {
  const qs = new URLSearchParams(location.search);
  const INDEXER_URL = qs.get('indexer') || 'https://mainnet-idx.algonode.cloud';
  const NFD_URL = qs.get('nfd') || 'https://api.nf.domains';

  const $ = (id) => document.getElementById(id);
  const addrInput = $('addrInput');
  const addrBtn = $('addrBtn');
  const addrOut = $('addrOut');
  const nfdInput = $('nfdInput');
  const nfdBtn = $('nfdBtn');
  const nfdOut = $('nfdOut');
  const endpoints = $('endpoints');
  endpoints.textContent = `indexer=${INDEXER_URL} | nfd=${NFD_URL}`;

  async function jsonFetch(url, init) {
    const res = await fetch(url, init);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return await res.json();
  }

  async function resolveNfd(name) {
    const data = await jsonFetch(`${NFD_URL}/nfd/${encodeURIComponent(name)}?view=basic`);
    if (!data || !data.owner) throw new Error('NFD not found or missing owner');
    return data.owner;
  }

  function pretty(obj) {
    try { return JSON.stringify(obj, null, 2); } catch { return String(obj); }
  }

  addrBtn.addEventListener('click', async () => {
    addrOut.textContent = 'Loading...';
    let query = addrInput.value.trim();
    if (!query) { addrOut.textContent = 'Enter an address or NFD.'; return; }
    try {
      if (query.endsWith('.algo')) {
        const resolved = await resolveNfd(query);
        query = resolved;
      }
      const data = await jsonFetch(`${INDEXER_URL}/v2/accounts/${encodeURIComponent(query)}`);
      addrOut.textContent = pretty(data);
    } catch (e) {
      addrOut.textContent = `Error: ${e.message}`;
    }
  });

  nfdBtn.addEventListener('click', async () => {
    nfdOut.textContent = 'Loading...';
    const name = nfdInput.value.trim();
    if (!name) { nfdOut.textContent = 'Enter an NFD name.'; return; }
    try {
      const data = await jsonFetch(`${NFD_URL}/nfd/${encodeURIComponent(name)}?view=full`);
      nfdOut.textContent = pretty(data);
    } catch (e) {
      nfdOut.textContent = `Error: ${e.message}`;
    }
  });

  // Node Health (from local ETL JSON)
  async function loadNodeHealth() {
    const container = document.getElementById('nodeHealth');
    if (!container) return;
    try {
      const data = await jsonFetch('data/node_status.json');
      renderNodeHealth(container, data);
    } catch (e) {
      container.innerHTML = '<div class="muted">No node_status.json found yet. Generate it with your local script.</div>';
    }
  }

  function renderNodeHealth(container, data) {
    const entries = [];
    if (typeof data.last_committed_block === 'number') entries.push(['Last Round', String(data.last_committed_block)]);
    if (typeof data.sync_time_seconds === 'number') entries.push(['Sync Time', `${data.sync_time_seconds.toFixed(1)} s`]);
    if (data.catchpoint) entries.push(['Catchpoint', String(data.catchpoint)]);

    const accTot = Number(data.catchpoint_accounts_total || 0);
    const accProc = Number(data.catchpoint_accounts_processed || 0);
    if (accTot > 0) {
      const pct = Math.floor((accProc / accTot) * 100);
      entries.push(['Accounts Progress', `${accProc.toLocaleString()} / ${accTot.toLocaleString()} (${pct}%)`]);
    }

    const kvTot = Number(data.catchpoint_kv_total || 0);
    const kvProc = Number(data.catchpoint_kv_processed || 0);
    if (kvTot > 0) {
      const pct = Math.floor((kvProc / kvTot) * 100);
      entries.push(['KV Progress', `${kvProc.toLocaleString()} / ${kvTot.toLocaleString()} (${pct}%)`]);
    }

    if (data.genesis_id) entries.push(['Genesis', String(data.genesis_id)]);
    if (typeof data.generated_at === 'number') entries.push(['Generated', new Date(data.generated_at * 1000).toISOString()]);

    const dl = document.createElement('dl');
    dl.className = 'kv';
    for (const [k, v] of entries) {
      const dt = document.createElement('dt');
      dt.textContent = k;
      const dd = document.createElement('dd');
      dd.textContent = v;
      dl.appendChild(dt);
      dl.appendChild(dd);
    }
    container.innerHTML = '';
    container.appendChild(dl);
  }

  // Recent Blocks chart (from local ETL JSON)
  async function loadRecentBlocksChart() {
    const canvas = document.getElementById('blocksChart');
    if (!canvas) return;
    const hintEl = document.querySelector('#recentBlocksCard .hint');
    try {
      const data = await jsonFetch('data/recent_blocks.json');
      const blocks = Array.isArray(data.blocks) ? data.blocks : [];
      if (!blocks.length) {
        if (hintEl) hintEl.textContent = 'No blocks found in snapshot.';
        return;
      }
      drawTxCountChart(canvas, blocks);
      if (hintEl) hintEl.textContent = `Showing ${blocks.length} rounds ending at ${data.last_round}.`;
    } catch (e) {
      if (hintEl) hintEl.textContent = 'No recent_blocks.json found yet.';
    }
  }

  function drawTxCountChart(canvas, blocks) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    const padding = 18;
    const plotW = width - padding * 2;
    const plotH = height - padding * 2;

    const counts = blocks.map(b => Number(b.tx_count || 0));
    const maxCount = Math.max(1, ...counts);

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding + (plotH * i) / 4;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    // Polyline
    ctx.strokeStyle = '#2a6df0';
    ctx.lineWidth = 2;
    ctx.beginPath();
    counts.forEach((c, i) => {
      const x = padding + (plotW * i) / (counts.length - 1 || 1);
      const y = padding + plotH - (plotH * c) / maxCount;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dots
    ctx.fillStyle = 'rgba(42, 109, 240, 0.85)';
    counts.forEach((c, i) => {
      const x = padding + (plotW * i) / (counts.length - 1 || 1);
      const y = padding + plotH - (plotH * c) / maxCount;
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  // Load ETL snapshot if present
  (async function loadEtl() {
    const el = document.createElement('section');
    el.className = 'card';
    el.innerHTML = '<h2>Recent Blocks (ETL Snapshot)</h2><pre class="out" id="etlOut">Loading...</pre>';
    document.querySelector('.container').appendChild(el);
    const etlOut = document.getElementById('etlOut');
    try {
      const data = await jsonFetch('data/recent_blocks.json');
      etlOut.textContent = pretty(data);
    } catch (e) {
      etlOut.textContent = 'No ETL snapshot found yet. Run etl/run.py to generate one.';
    }
  })();

  // Kick off local JSON-driven UI pieces
  loadNodeHealth();
  loadRecentBlocksChart();
})();


