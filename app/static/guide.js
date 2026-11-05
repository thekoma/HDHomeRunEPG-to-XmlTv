// TV guide: local times, ruler, now-line, genre filter, title search, detail pane, arrow-key navigation.
(() => {
  const sheet = document.getElementById("sheet");
  if (!sheet) return;

  const details = JSON.parse(document.getElementById("guide-data").textContent);
  const origin = Number(sheet.dataset.origin);
  const span = Number(sheet.dataset.span);
  const rows = [...sheet.querySelectorAll(".row")];
  const slots = [...sheet.querySelectorAll(".slot")];
  const pane = document.getElementById("pane");
  const paneBody = document.getElementById("pane-body");
  const narrow = window.matchMedia("(max-width: 1279px)");
  const time = new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" });
  const day = new Intl.DateTimeFormat(undefined, { weekday: "short", day: "numeric", month: "short" });
  const shortDay = new Intl.DateTimeFormat(undefined, { weekday: "short", day: "numeric" });
  const today = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" }).format(0, "day");
  const at = (minutes) => new Date((origin + minutes * 60) * 1000);
  const nowMinutes = () => (Date.now() / 1000 - origin) / 60;
  const pxPerMinute = () => document.getElementById("ticks").getBoundingClientRect().width / span;
  const slotOf = (i) => sheet.querySelector(`.slot[data-i="${i}"]`);

  // Times are formatted in the viewer's own time zone.
  for (const t of sheet.querySelectorAll("time[data-ts]")) t.textContent = time.format(t.dataset.ts * 1000);

  // Ruler: half-hour ticks, midnight rules, and one tab per day.
  const ticks = document.getElementById("ticks");
  const midnights = [];
  for (let m = 0; m <= span; m += 30) {
    const d = at(m);
    const tick = document.createElement("span");
    tick.className = "tick";
    tick.style.setProperty("--m", m);
    if (d.getHours() === 0 && d.getMinutes() === 0) {
      tick.classList.add("midnight");
      tick.textContent = shortDay.format(d);
      midnights.push(m);
    } else {
      tick.textContent = time.format(d);
    }
    ticks.append(tick);
  }
  for (const lane of sheet.querySelectorAll(".lane")) {
    for (const m of midnights) {
      const rule = document.createElement("span");
      rule.className = "midnight-rule";
      rule.style.setProperty("--m", m);
      lane.append(rule);
    }
  }

  const tabs = document.getElementById("day-tabs");
  const dayStarts = [0, ...midnights];
  dayStarts.forEach((m, n) => {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "btn";
    tab.textContent = n === 0 ? today[0].toUpperCase() + today.slice(1) : day.format(at(m));
    if (n === 0) tab.title = "Back to now";
    tab.addEventListener("click", () => (n === 0 ? scrollToNow() : scrollToMinute(m)));
    tabs.append(tab);
  });
  const rulerDay = document.getElementById("ruler-day");
  function syncDay() {
    const left = sheet.scrollLeft / pxPerMinute();
    let current = 0;
    dayStarts.forEach((m, n) => { if (left >= m - 1) current = n; });
    [...tabs.children].forEach((tab, n) => tab.setAttribute("aria-pressed", String(n === current)));
    rulerDay.textContent = day.format(at(Math.max(left, dayStarts[current])));
  }
  sheet.addEventListener("scroll", syncDay, { passive: true });

  // Now-line: moves every 30 seconds; programmes that ended are dimmed.
  const nowTag = document.getElementById("now-tag");
  function placeNow() {
    const now = nowMinutes();
    sheet.style.setProperty("--now", now.toFixed(2));
    nowTag.textContent = time.format(Date.now());
    // The now tag hides the tick labels it overlaps, on either side of it.
    const tag = nowTag.getBoundingClientRect();
    for (const tick of ticks.querySelectorAll(".tick")) {
      const label = tick.getBoundingClientRect();
      tick.classList.toggle("covered", label.left < tag.right && label.right > tag.left);
    }
    for (const s of slots) {
      const start = Number(s.dataset.s);
      const end = Number(s.dataset.e);
      const airing = start <= now && now < end;
      s.classList.toggle("ended", end <= now);
      s.classList.toggle("airing", airing);
      if (airing) s.style.setProperty("--lead", (now - start).toFixed(2));
      // On air, what fits is the width left after the rule, not the whole programme.
      s.classList.toggle("tight", airing && end - now < 10);
      s.classList.toggle("snug", airing && end - now < 15);
    }
  }
  function scrollToMinute(m) {
    sheet.scrollTo({ left: Math.max(0, m * pxPerMinute()), behavior: "smooth" });
  }
  function scrollToNow() {
    scrollToMinute(nowMinutes() - 20);
  }

  // Genre filter: dims every other genre across the whole sheet.
  const chips = [...document.querySelectorAll(".chip[data-genre]")];
  for (const chip of chips) {
    chip.addEventListener("click", () => {
      chip.setAttribute("aria-pressed", String(chip.getAttribute("aria-pressed") !== "true"));
      const on = chips.filter((c) => c.getAttribute("aria-pressed") === "true").map((c) => c.dataset.genre);
      sheet.classList.toggle("is-filtering", on.length > 0);
      for (const c of chips) sheet.classList.toggle(`show-${c.dataset.genre}`, on.includes(c.dataset.genre));
    });
  }

  // Detail pane, filled with textContent only.
  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }
  function fillPane(i) {
    const d = details[i];
    const minutes = Math.round((d.end - d.start) / 60);
    const parts = [];
    if (d.image) {
      const fig = el("figure");
      const img = el("img");
      img.src = d.image;
      img.alt = "";
      img.addEventListener("error", () => fig.remove());
      fig.append(img);
      parts.push(fig);
    }
    const title = el("h2", null, d.title);
    title.id = "pane-title";
    parts.push(title);
    if (d.episodeTitle) parts.push(el("p", "sub", d.episodeTitle));
    const when = el("p", "when", `${day.format(d.start * 1000)} · ${time.format(d.start * 1000)}–${time.format(d.end * 1000)} · ${minutes} min`);
    parts.push(when, el("p", "channel", d.channel));
    const tags = el("div", "tags");
    const genre = el("span", `tag fill g-${d.genre}`, d.categories[0] || "Other");
    tags.append(genre);
    for (const c of d.categories.slice(1)) tags.append(el("span", "tag", c));
    if (d.episodeNumber) tags.append(el("span", "tag", d.episodeNumber));
    if (d.first) tags.append(el("span", "tag", "First airing"));
    else if (d.airdate) tags.append(el("span", "tag", `First aired ${new Date(d.airdate * 1000).getFullYear()}`));
    parts.push(tags);
    parts.push(d.synopsis ? el("p", "desc", d.synopsis) : el("p", "desc missing", "The guide data has no description for this programme."));
    const next = details[i + 1];
    if (next && next.row === d.row) parts.push(el("p", "next", `Next on ${d.channel}: ${next.title} · ${time.format(next.start * 1000)}`));
    paneBody.replaceChildren(...parts);
  }

  let current = null;
  function select(slot, { focus = false } = {}) {
    if (current) {
      current.removeAttribute("aria-current");
      current.tabIndex = -1;
    }
    current = slot;
    slot.setAttribute("aria-current", "true");
    slot.tabIndex = 0;
    fillPane(Number(slot.dataset.i));
    if (focus) slot.focus();
  }
  function openPane() {
    if (!narrow.matches) return;
    pane.classList.add("open");
    document.getElementById("pane-close").focus();
  }
  function closePane() {
    if (!pane.classList.contains("open")) return;
    pane.classList.remove("open");
    current?.focus();
  }
  document.getElementById("pane-close").addEventListener("click", closePane);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closePane(); });

  sheet.addEventListener("click", (e) => {
    const slot = e.target.closest(".slot");
    if (!slot) return;
    select(slot);
    openPane();
  });
  sheet.addEventListener("focusin", (e) => {
    if (e.target.classList.contains("slot") && e.target !== current) select(e.target);
  });

  // Arrow keys move across the sheet like a remote: left and right along a channel, up and down at the same time.
  sheet.addEventListener("keydown", (e) => {
    const slot = e.target.closest(".slot");
    if (!slot) return;
    const lane = slot.parentElement;
    const inLane = [...lane.querySelectorAll(".slot")];
    const r = rows.indexOf(lane.parentElement);
    let target = null;
    if (e.key === "ArrowRight") target = inLane[inLane.indexOf(slot) + 1];
    else if (e.key === "ArrowLeft") target = inLane[inLane.indexOf(slot) - 1];
    else if (e.key === "Home") target = inLane[0];
    else if (e.key === "End") target = inLane[inLane.length - 1];
    else if (["ArrowDown", "ArrowUp", "PageDown", "PageUp"].includes(e.key)) {
      const step = { ArrowDown: 1, ArrowUp: -1, PageDown: 5, PageUp: -5 }[e.key];
      // Stay at the same moment: "now" while on an airing programme, otherwise its start.
      const s = Number(slot.dataset.s);
      const now = nowMinutes();
      const moment = s <= now && now < Number(slot.dataset.e) ? now : s;
      const first = Math.min(Math.max(r + step, 0), rows.length - 1);
      // Rows without programmes are skipped in the direction of travel.
      for (let n = first; n >= 0 && n < rows.length && n !== r && !target; n += Math.sign(step)) {
        const candidates = [...rows[n].querySelectorAll(".slot")];
        target = candidates.find((c) => Number(c.dataset.s) <= moment && Number(c.dataset.e) > moment)
          || candidates.find((c) => Number(c.dataset.s) >= moment)
          || candidates[candidates.length - 1];
      }
    } else return;
    e.preventDefault();
    if (target) select(target, { focus: true });
  });

  // Title search: lists upcoming matches and jumps the sheet to the slot.
  const q = document.getElementById("q");
  const results = document.getElementById("results");
  let timer;
  q.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(renderResults, 120);
  });
  q.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" && !results.hidden) {
      e.preventDefault();
      results.querySelector(".result")?.focus();
    } else if (e.key === "Escape") {
      q.value = "";
      results.hidden = true;
    }
  });
  results.addEventListener("keydown", (e) => {
    const items = [...results.querySelectorAll(".result")];
    const n = items.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); items[n + 1]?.focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); (items[n - 1] || q).focus(); }
    else if (e.key === "Escape") { results.hidden = true; q.focus(); }
  });
  document.addEventListener("click", (e) => { if (!e.target.closest(".search")) results.hidden = true; });

  function renderResults() {
    const term = q.value.trim().toLowerCase();
    if (term.length < 2) {
      results.hidden = true;
      return;
    }
    const nowSec = Date.now() / 1000;
    const hits = details
      .map((d, i) => ({ d, i }))
      .filter(({ d }) => d.end > nowSec && `${d.title} ${d.episodeTitle || ""}`.toLowerCase().includes(term))
      .sort((a, b) => a.d.start - b.d.start)
      .slice(0, 12);
    if (!hits.length) {
      results.replaceChildren(el("p", null, `No upcoming programme matches “${q.value.trim()}”.`));
    } else {
      results.replaceChildren(...hits.map(({ d, i }) => {
        const item = el("button", "result");
        item.type = "button";
        const name = el("b", null, d.title);
        const meta = el("span", null, `${d.channel} · ${shortDay.format(d.start * 1000)} ${time.format(d.start * 1000)}`);
        const swatch = el("i", `g-${d.genre}`);
        swatch.setAttribute("aria-hidden", "true");
        meta.prepend(swatch);
        item.append(name, meta);
        item.addEventListener("click", () => {
          results.hidden = true;
          select(slotOf(i), { focus: true });
          openPane();
        });
        return item;
      }));
    }
    results.hidden = false;
  }

  // Dark logos on a transparent ground get a light tile. A separate CORS copy is probed,
  // so the visible logo never breaks if the image host stops sending CORS headers.
  const probe = document.createElement("canvas");
  probe.width = 24;
  probe.height = 18;
  const pctx = probe.getContext("2d", { willReadFrequently: true });
  function classifyLogo(visible) {
    const copy = new Image();
    copy.crossOrigin = "anonymous";
    copy.addEventListener("load", () => {
      try {
        pctx.clearRect(0, 0, 24, 18);
        pctx.drawImage(copy, 0, 0, 24, 18);
        const px = pctx.getImageData(0, 0, 24, 18).data;
        let sum = 0;
        let opaque = 0;
        for (let k = 0; k < px.length; k += 4) {
          if (px[k + 3] < 128) continue;
          sum += 0.2126 * px[k] + 0.7152 * px[k + 1] + 0.0722 * px[k + 2];
          opaque += 1;
        }
        if (opaque && sum / opaque / 255 < 0.35 && opaque / (24 * 18) < 0.5) visible.parentElement.classList.add("on-light");
      } catch {
        // Tainted canvas: keep the dark tile.
      }
    }, { once: true });
    copy.src = visible.currentSrc || visible.src;
  }
  for (const img of sheet.querySelectorAll(".plate .logo img")) {
    if (img.complete) classifyLogo(img);
    else img.addEventListener("load", () => classifyLogo(img), { once: true });
  }

  // Start on the programme airing now on the first channel.
  placeNow();
  setInterval(placeNow, 30000);
  syncDay();
  const firstAiring = rows[0] && [...rows[0].querySelectorAll(".slot")].find((s) => !s.classList.contains("ended"));
  // The wide layout shows the first programme on air in the pane. On narrow
  // screens the pane is closed, so that programme is only where the keyboard
  // starts, without a selection ring.
  const start = firstAiring || slots[0];
  if (start && narrow.matches) {
    current = start;
    start.tabIndex = 0;
  } else if (start) {
    select(start);
  }
})();
