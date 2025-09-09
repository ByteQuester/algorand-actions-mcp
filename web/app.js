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
})();


