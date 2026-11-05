// Status page: cache summary, cache table, and the clear-cache action.
(() => {
  const root = document.getElementById("status");
  if (!root) return;

  const ttl = Number(root.dataset.ttl);
  const rows = document.getElementById("cache-rows");
  const table = document.getElementById("cache-table");
  const empty = document.getElementById("cache-empty");
  const error = document.getElementById("cache-error");
  const msg = document.getElementById("cache-msg");
  const button = document.getElementById("clear-cache");
  const dayTime = new Intl.DateTimeFormat(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  const timeOnly = new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" });
  const full = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "medium" });

  function duration(seconds) {
    const s = Math.max(0, Math.round(seconds));
    if (s < 60) return `${s} s`;
    const m = Math.floor(s / 60);
    if (m < 60) return `${m} min`;
    const h = Math.floor(m / 60);
    if (h < 48) return m % 60 ? `${h} h ${m % 60} min` : `${h} h`;
    return `${Math.floor(h / 24)} days`;
  }
  function bytes(n) {
    if (n < 1024) return `${n} B`;
    if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / 1024 ** 2).toFixed(1)} MB`;
  }
  function cell(text, cls) {
    const td = document.createElement("td");
    if (cls) td.className = cls;
    td.textContent = text;
    return td;
  }
  function window_(start, end) {
    const a = new Date(start * 1000);
    const b = new Date(end * 1000);
    const sameDay = a.toDateString() === b.toDateString();
    return `${dayTime.format(a)} – ${sameDay ? timeOnly.format(b) : dayTime.format(b)}`;
  }

  document.getElementById("ttl-note").textContent = `Each chunk is fetched again once it is older than ${duration(ttl)}.`;

  function show(part) {
    table.hidden = part !== "table";
    empty.hidden = part !== "empty";
    error.hidden = part !== "error";
  }

  function render(chunks) {
    const now = Date.now() / 1000;
    document.getElementById("stat-chunks").textContent = String(chunks.length);
    document.getElementById("stat-size").textContent = bytes(chunks.reduce((sum, c) => sum + c.size_bytes, 0));
    const until = chunks.reduce((max, c) => Math.max(max, c.end_time), 0);
    document.getElementById("stat-until").textContent = until ? dayTime.format(until * 1000) : "–";
    if (!chunks.length) return show("empty");

    rows.replaceChildren(...chunks.map((c) => {
      const tr = document.createElement("tr");
      const age = now - c.fetched_at;
      const fetched = cell(`${duration(age)} ago`);
      fetched.title = full.format(c.fetched_at * 1000);
      const status = document.createElement("td");
      const badge = document.createElement("span");
      badge.className = `badge ${age < ttl ? "fresh" : "stale"}`;
      badge.textContent = age < ttl ? "Fresh" : "Stale";
      status.append(badge);
      tr.append(cell(window_(c.start_time, c.end_time), "num"), cell(bytes(c.size_bytes), "num"), fetched, status);
      return tr;
    }));
    show("table");
  }

  async function load() {
    try {
      const res = await fetch("/cache");
      if (!res.ok) throw new Error(`The service answered HTTP ${res.status}.`);
      const data = await res.json();
      if (!Array.isArray(data)) throw new Error(data.error || "Unexpected response from /cache.");
      render(data);
    } catch (e) {
      document.getElementById("cache-error-text").textContent = e.message;
      show("error");
    }
  }

  button.addEventListener("click", async () => {
    if (!confirm("Delete all cached guide data? The next request fetches everything from HDHomeRun again.")) return;
    button.disabled = true;
    msg.className = "msg";
    msg.textContent = "Clearing…";
    try {
      const res = await fetch("/cache", { method: "DELETE" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      msg.className = "msg ok";
      msg.textContent = "Cache cleared.";
      await load();
    } catch (e) {
      msg.className = "msg bad";
      msg.textContent = `Couldn't clear the cache (${e.message}). Check the service logs.`;
    } finally {
      button.disabled = false;
    }
  });

  load();
})();
