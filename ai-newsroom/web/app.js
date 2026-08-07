/* AI Newsroom — ડેશબોર્ડ, અપ્રુવલ, ન્યુઝ, રિપોર્ટ, સેટિંગ */
const $ = (s) => document.querySelector(s);
const STATE_LABEL = {
  idle: "નિષ્ક્રિય", thinking: "વિચારે છે...", working: "કામ ચાલુ",
  waiting: "અપ્રુવલ રાહ", done: "પૂર્ણ ✓", error: "ભૂલ!",
};
const STATUS_LABEL = {
  pending_approval: "🟠 રાહમાં", approved: "✅ મંજૂર",
  published: "📤 પબ્લિશ", rejected: "❌ રદ", proofread: "લખાયો",
  draft: "ડ્રાફ્ટ",
};
const CAT_LABEL = { general: "સમાચાર", breaking: "બ્રેકિંગ",
  birthday: "જન્મદિવસ", tribute: "શ્રદ્ધાંજલિ" };
const AGENT_EMOJI = { ceo: "👑", scout: "🔍", editor: "✍️",
  proofreader: "🔤", designer: "🎨", photo: "📷", publisher: "📤",
  inbox: "💬", analyst: "📊", updater: "🔄" };

/* ── ટોસ્ટ ── */
function toast(msg, kind = "") {
  const t = document.createElement("div");
  t.className = "toast " + kind;
  t.textContent = msg;
  $("#toasts").appendChild(t);
  setTimeout(() => { t.style.opacity = 0; t.style.transition = "opacity .4s";
    setTimeout(() => t.remove(), 400); }, 3800);
}

/* ── થીમ (ડાર્ક/લાઈટ) ── */
(function initTheme() {
  const saved = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
})();
if ($("#theme-toggle")) $("#theme-toggle").onclick = () => {
  const cur = document.documentElement.getAttribute("data-theme");
  const next = cur === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
  $("#theme-toggle").textContent = next === "light" ? "🌞 થીમ બદલો" : "🌙 થીમ બદલો";
};

/* ── લોગિન (auth ચાલુ હોય તો) ── */
(async function checkAuth() {
  try {
    const me = await (await fetch("/api/me")).json();
    if (me.auth_enabled && !me.role) showLogin();
  } catch {}
})();
function showLogin() {
  $("#login-modal").classList.remove("hidden");
}
if ($("#btn-login")) $("#btn-login").onclick = async () => {
  const r = await (await fetch("/api/login", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: $("#login-user").value,
                           password: $("#login-pass").value }) })).json();
  if (r.ok) { $("#login-modal").classList.add("hidden"); location.reload(); }
  else $("#login-err").textContent = r.error || "લોગિન નિષ્ફળ";
};

/* ── ટેબ ── */
document.querySelectorAll(".nav-btn").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach((x) => x.classList.remove("active"));
    document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    $("#tab-" + b.dataset.tab).classList.add("active");
    if (b.dataset.tab === "approval") loadApproval();
    if (b.dataset.tab === "news") loadNews();
    if (b.dataset.tab === "reports") loadReports();
    if (b.dataset.tab === "settings") loadSettings();
    if (b.dataset.tab === "dashboard") requestAnimationFrame(drawEdges);
  }));

/* ── ઘડિયાળ ── */
setInterval(() => {
  $("#clock").textContent = new Date().toLocaleTimeString("gu-IN",
    { hour12: false });
}, 1000);

/* ── એજન્ટ ગ્રાફ ── */
const EDGE_PAIRS = [
  ["ceo", "scout"], ["ceo", "editor"], ["ceo", "proofreader"],
  ["ceo", "designer"], ["ceo", "photo"], ["editor", "proofreader"],
  ["proofreader", "designer"], ["designer", "publisher"],
  ["ceo", "inbox"], ["ceo", "analyst"],
];
function nodeCenter(name) {
  const el = $("#node-" + name), wrap = $(".graph-wrap");
  const r = el.getBoundingClientRect(), w = wrap.getBoundingClientRect();
  return { x: r.left + r.width / 2 - w.left, y: r.top + r.height / 2 - w.top };
}
function edgePath(a, b) {
  const p1 = nodeCenter(a), p2 = nodeCenter(b);
  const mx = (p1.x + p2.x) / 2, my = (p1.y + p2.y) / 2 - 26;
  return `M ${p1.x} ${p1.y} Q ${mx} ${my} ${p2.x} ${p2.y}`;
}
function drawEdges() {
  const svg = $("#edges");
  if (!svg || !$("#tab-dashboard").classList.contains("active")) return;
  svg.innerHTML = "";
  for (const [a, b] of EDGE_PAIRS) {
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", edgePath(a, b));
    path.setAttribute("class", "edge");
    path.id = `edge-${a}-${b}`;
    svg.appendChild(path);
  }
}
window.addEventListener("resize", drawEdges);
requestAnimationFrame(drawEdges);

/* CEO કામ વહેંચે — ટપકું દોડે */
function runDot(from, to) {
  const path = $(`#edge-${from}-${to}`) || $(`#edge-${to}-${from}`);
  if (!path) return;
  path.classList.add("active");
  setTimeout(() => path.classList.remove("active"), 2500);
  const svg = $("#edges");
  const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  dot.setAttribute("r", "7");
  dot.setAttribute("class", "dot-run");
  const anim = document.createElementNS("http://www.w3.org/2000/svg",
    "animateMotion");
  anim.setAttribute("dur", "1.2s");
  anim.setAttribute("path", path.getAttribute("d"));
  anim.setAttribute("fill", "freeze");
  dot.appendChild(anim);
  svg.appendChild(dot);
  anim.beginElement?.();
  setTimeout(() => dot.remove(), 1400);
}

function setAgentState(agent, status, message) {
  const node = $("#node-" + agent);
  if (!node) return;
  node.classList.remove("thinking", "working", "waiting", "done", "error");
  if (status && status !== "idle") node.classList.add(status);
  const st = $("#state-" + agent);
  st.textContent = STATE_LABEL[status] || STATE_LABEL.idle;
  if (message) st.title = message;
}

/* ── લાઈવ લોગ ── */
function addLog(ev) {
  if (!ev.message) return;
  const li = document.createElement("li");
  const time = (ev.ts || "").split("T")[1] || "";
  li.innerHTML = `<span class="t">${time}</span>` +
    `<span>${AGENT_EMOJI[ev.agent] || "•"} ${ev.message}</span>`;
  const log = $("#live-log");
  log.prepend(li);
  while (log.children.length > 80) log.lastChild.remove();
}

/* ── WebSocket ── */
let ws;
function connectWS() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (m) => {
    const ev = JSON.parse(m.data);
    if (ev.type === "job:progress") {
      const w = $("#progress-wrap");
      if (w) {
        w.style.display = ev.percent >= 100 ? "none" : "block";
        if (ev.percent >= 100) setTimeout(() => w.style.display = "none", 3000);
        w.style.display = "block";
        $("#progress-bar").style.width = ev.percent + "%";
        $("#progress-pct").textContent = ev.percent + "%";
        $("#progress-msg").textContent =
          (ev.stage ? ev.stage + " — " : "") + ev.message;
      }
      return;
    }
    if (ev.type !== "agent:event") return;
    if (ev.event === "dispatch" && ev.detail?.to) {
      runDot(ev.agent, ev.detail.to);
      return;
    }
    setAgentState(ev.agent, ev.status, ev.message);
    addLog(ev);
    if (ev.event === "completed" || ev.event === "failed" ||
        ev.status === "waiting") refreshStatus();
  };
  ws.onclose = () => setTimeout(connectWS, 2000);
}
connectWS();

/* ── સ્ટેટસ ── */
async function refreshStatus() {
  try {
    const s = await (await fetch("/api/status")).json();
    $("#ollama-dot").className = "dot" + (s.ollama ? " on" : "");
    $("#ollama-status").textContent =
      s.ollama ? "Ollama ચાલુ" : "Ollama બંધ — ડેમો મોડ";
    $("#version").textContent = "વર્ઝન: " + s.version;
    $("#pending-badge").textContent = s.pending_approval || "";
    const t = s.today || {};
    $("#st-collected").textContent = t.news_collected || 0;
    $("#st-selected").textContent = t.news_selected || 0;
    $("#st-written").textContent = t.news_written || 0;
    $("#st-posters").textContent = t.posters_created || 0;
    $("#st-approved").textContent = t.approved || 0;
  } catch {}
}
refreshStatus();
setInterval(refreshStatus, 10000);

// મલ્ટી-જિલ્લા ડ્રોપડાઉન ભરો
(async function loadDistricts() {
  try {
    const cfg = await (await fetch("/api/settings")).json();
    const ds = cfg.districts || [];
    const sel = $("#press-district");
    if (ds.length && sel) {
      ds.forEach(d => { const o = document.createElement("option");
        o.value = d.name; o.textContent = "📍 " + d.name; sel.appendChild(o); });
      sel.style.display = "block";
    }
  } catch {}
})();

// તહેવાર રિમાઈન્ડર + ટ્રેન્ડિંગ બેનર
(async function loadFestivals() {
  try {
    const f = await (await fetch("/api/festivals")).json();
    let html = "";
    if (f.length) html += f.map(x =>
      `<div class="card" style="padding:12px 18px;margin-bottom:12px;
       border-left:4px solid var(--gold)">🎉 <b>${x.when}</b>: ${x.name}
       — પોસ્ટર બનાવવાનું યાદ રાખો!</div>`).join("");
    const t = await (await fetch("/api/trending")).json();
    if (t.length) html += `<div class="card" style="padding:12px 18px;
      margin-bottom:12px;border-left:4px solid var(--blue)">📈 <b>ટ્રેન્ડિંગ:</b> ` +
      t.slice(0, 8).map(x => `${x.word} (${x.count})`).join(" • ") + "</div>";
    if ($("#fest-banner")) $("#fest-banner").innerHTML = html;
  } catch {}
})();

/* ── રન બટન — પહેલા પૂછે: કેટલા ન્યુઝ, કેટલી AI તસવીર ── */
const IMG_COST = { aiauto: 0, local: 0, pollinations: 0, gemini: 3, openai: 3.5 };
let imgProvider = "pollinations", imgEnabled = false;

async function openRunModal() {
  try {
    const cfg = await (await fetch("/api/settings")).json();
    $("#run-count").value = cfg.daily_news_count || 5;
    imgProvider = cfg.image_ai_provider || "pollinations";
    imgEnabled = !!cfg.image_ai_enabled;
    $("#run-ai").value = imgEnabled ? ($("#run-count").value) : 0;
  } catch {}
  updateRunCost();
  $("#run-modal").classList.remove("hidden");
}
function updateRunCost() {
  const n = +$("#run-ai").value || 0;
  const per = IMG_COST[imgProvider] ?? 0;
  const cost = n * per;
  $("#run-cost").textContent = !imgEnabled && n > 0
    ? "⚠️ સેટિંગમાં AI તસવીર બંધ છે — પહેલા ચાલુ કરો"
    : n === 0
      ? "AI તસવીર નહીં બને — ખર્ચ ₹0"
      : per === 0
        ? `${n} AI તસવીર (Pollinations — મફત) — ખર્ચ ₹0`
        : `અંદાજિત ખર્ચ: ${n} તસવીર × ₹${per} ≈ ₹${cost.toFixed(0)}`;
}
$("#run-ai").oninput = updateRunCost;
$("#btn-run").onclick = openRunModal;
$("#run-modal-close").onclick = () => $("#run-modal").classList.add("hidden");
$("#run-modal").addEventListener("click", (e) => {
  if (e.target === $("#run-modal")) $("#run-modal").classList.add("hidden");
});
$("#btn-run-go").onclick = async () => {
  $("#run-modal").classList.add("hidden");
  const r = await (await fetch("/api/run-day", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ count: +$("#run-count").value || 5,
                           ai_images: +$("#run-ai").value || 0 }),
  })).json();
  toast(r.message || r.error, r.error ? "bad" : "good");
};
$("#btn-press").onclick = async () => {
  const reporter = $("#press-reporter") ? $("#press-reporter").value.trim() : "";
  const pdf = $("#press-pdf") && $("#press-pdf").files[0];
  // PDF હોય તો એ રસ્તે
  if (pdf) {
    const fd = new FormData(); fd.append("pdf", pdf);
    if (reporter) fd.append("reporter", reporter);
    const r = await (await fetch("/api/press-pdf",
      { method: "POST", body: fd })).json();
    toast(r.message || r.error, r.error ? "bad" : "good");
    if (r.ok) $("#press-pdf").value = "";
    return;
  }
  const text = $("#press-text").value.trim();
  const files = [...$("#press-photo").files].slice(0, 3);
  if (!text && !files.length) return toast("પ્રેસ નોટનું લખાણ લખો", "bad");
  const fd = new FormData();
  fd.append("text", text);
  if (reporter) fd.append("reporter", reporter);
  const dsel = $("#press-district");
  if (dsel && dsel.value) fd.append("district", dsel.value);
  for (const f of files) fd.append("photos", f);
  const r = await (await fetch("/api/press-note",
    { method: "POST", body: fd })).json();
  toast(r.message || r.error, r.error ? "bad" : "good");
  if (r.ok) { $("#press-text").value = ""; $("#press-photo").value = ""; }
};

/* ── અપ્રુવલ ── */
async function loadApproval() {
  const list = await (await fetch("/api/news?status=pending_approval")).json();
  const wrap = $("#approval-list");
  wrap.innerHTML = list.length ? "" :
    '<p class="empty-note">કોઈ ન્યુઝ અપ્રુવલની રાહમાં નથી 🎉</p>';
  for (const n of list) {
    const div = document.createElement("div");
    div.className = "card a-card";
    const posters = n.posters || [];
    const sizeNames = { "1080x1080": "પોસ્ટ", "1080x1350": "પોર્ટ્રેટ",
      "1080x1920": "સ્ટોરી" };
    const tabs = posters.map((p, i) =>
      `<button class="${i === 0 ? "active" : ""}" data-url="${p.url}">` +
      `${sizeNames[p.size] || p.size}</button>`).join("");
    div.innerHTML = `
      <div class="poster-frame">
        ${posters[0]?.url ? `<img src="${posters[0].url}" loading="lazy">` : ""}
      </div>
      ${posters.length > 1 ? `<div class="size-tabs">${tabs}</div>` : ""}
      <div class="meta">
        <span class="cat-chip cat-${n.category}">${CAT_LABEL[n.category] || n.category}</span>
        <span>${(n.created_at || "").slice(0, 16)}</span>
      </div>
      <h4>${n.title}</h4>
      <p class="body-clip">${n.body}</p>
      <div class="row">
        <button class="approve">✅ મંજૂર + પબ્લિશ</button>
        <button class="reject">રદ કરો</button>
      </div>`;
    div.querySelectorAll(".size-tabs button").forEach((b) =>
      b.addEventListener("click", () => {
        div.querySelectorAll(".size-tabs button").forEach((x) =>
          x.classList.remove("active"));
        b.classList.add("active");
        div.querySelector("img").src = b.dataset.url;
      }));
    div.querySelector(".approve").onclick = async () => {
      div.style.opacity = .45;
      const r = await (await fetch(`/api/news/${n.id}/approve`,
        { method: "POST" })).json();
      toast(r.publish?.facebook === "simulated"
        ? "મંજૂર ✓ (ટોકન વગર — સિમ્યુલેશન પબ્લિશ)"
        : "મંજૂર + પબ્લિશ થઈ ગયું ✓", "good");
      loadApproval(); refreshStatus();
    };
    div.querySelector(".reject").onclick = async () => {
      await fetch(`/api/news/${n.id}/reject`, { method: "POST" });
      toast("ન્યુઝ રદ કર્યો");
      loadApproval(); refreshStatus();
    };
    wrap.appendChild(div);
  }
}

/* ── બધા ન્યુઝ ── */
let newsFilter = "";
document.querySelectorAll("#news-filters .chip").forEach((c) =>
  c.addEventListener("click", () => {
    document.querySelectorAll("#news-filters .chip").forEach((x) =>
      x.classList.remove("active"));
    c.classList.add("active");
    newsFilter = c.dataset.status;
    loadNews();
  }));

let newsSearchTimer;
if ($("#news-search")) $("#news-search").oninput = () => {
  clearTimeout(newsSearchTimer);
  newsSearchTimer = setTimeout(loadNews, 350);
};
async function loadNews() {
  const search = $("#news-search") ? $("#news-search").value.trim() : "";
  let q = "?limit=100";
  if (newsFilter) q += "&status=" + newsFilter;
  if (search) q += "&q=" + encodeURIComponent(search);
  const list = await (await fetch("/api/news" + q)).json();
  const wrap = $("#news-list");
  wrap.innerHTML = list.length ? "" :
    '<p class="empty-note">કોઈ ન્યુઝ નથી</p>';
  for (const n of list) {
    const div = document.createElement("div");
    div.className = "card n-row";
    div.innerHTML = `
      ${n.posters?.[0]?.url
        ? `<img class="n-thumb" src="${n.posters[0].url}" loading="lazy">`
        : '<div class="n-thumb"></div>'}
      <div class="n-info">
        <h4>${n.title}</h4>
        <p>${(n.created_at || "").slice(0, 16)} •
           ${CAT_LABEL[n.category] || n.category} • ${n.body}</p>
      </div>
      <span class="st-chip st-${n.status}">${STATUS_LABEL[n.status] || n.status}</span>`;
    div.onclick = () => openNewsModal(n);
    wrap.appendChild(div);
  }
}

function openNewsModal(n) {
  const posters = (n.posters || [])
    .map((p) => `<img src="${p.url}">`).join("");
  $("#modal-body").innerHTML = `
    <div class="meta" style="margin-bottom:8px">
      <span class="cat-chip cat-${n.category}">${CAT_LABEL[n.category] || ""}</span>
      <span class="st-chip st-${n.status}">${STATUS_LABEL[n.status] || ""}</span>
      ${n.tag ? `<span class="cat-chip" style="background:#23304f;color:#aabbdd">${n.tag}</span>` : ""}
    </div>
    <label style="font-size:12px;color:var(--muted)">હેડલાઈન</label>
    <input id="edit-title" value="${(n.title||'').replace(/"/g,'&quot;')}"
      style="width:100%;background:var(--bg-2);border:1px solid var(--line);
      color:var(--ink);border-radius:10px;padding:9px;margin:4px 0 10px">
    <label style="font-size:12px;color:var(--muted)">લખાણ</label>
    <textarea id="edit-body" rows="4">${n.body || ""}</textarea>
    <div class="row" style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap">
      <button class="primary small" id="btn-edit-save">💾 સેવ + પોસ્ટર ફરી બનાવો</button>
      <button class="ghost" id="btn-summarize">✨ સારાંશ</button>
      <button class="ghost" id="btn-video">🎬 વિડિયો (Reels)</button>
    </div>
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;
      flex-wrap:wrap">
      <span style="font-size:13px;color:var(--muted)">⏰ શેડ્યૂલ પબ્લિશ:</span>
      <input type="datetime-local" id="sched-at"
        style="background:var(--bg-2);border:1px solid var(--line);
        color:var(--ink);border-radius:8px;padding:7px">
      <button class="ghost" id="btn-schedule">સેટ કરો</button>
    </div>
    <div id="video-out"></div>
    ${n.source_url ? `<p style="margin-bottom:8px;font-size:12px">
      સોર્સ: <a href="${n.source_url}" target="_blank"
      style="color:var(--blue)">${n.source_title || n.source_url}</a></p>` : ""}
    <div class="modal-posters">${posters}</div>`;
  $("#btn-edit-save").onclick = async () => {
    $("#btn-edit-save").textContent = "બની રહ્યું છે...";
    await fetch(`/api/news/${n.id}/edit`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: $("#edit-title").value,
                             body: $("#edit-body").value }) });
    toast("પોસ્ટર ફરી બન્યું ✓", "good");
    $("#modal").classList.add("hidden");
    loadNews();
  };
  $("#btn-summarize").onclick = async () => {
    const r = await (await fetch("/api/summarize", { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: $("#edit-body").value }) })).json();
    if (r.summary) $("#edit-body").value = r.summary;
  };
  if (n.scheduled_at) $("#sched-at").value =
    n.scheduled_at.replace(" ", "T").slice(0, 16);
  $("#btn-schedule").onclick = async () => {
    const at = $("#sched-at").value;
    if (!at) return toast("પહેલા સમય પસંદ કરો", "bad");
    await fetch(`/api/news/${n.id}/schedule`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ at }) });
    toast("શેડ્યૂલ થઈ ગયું — સમય થાય એટલે આપોઆપ પબ્લિશ ⏰", "good");
    $("#modal").classList.add("hidden"); loadNews();
  };
  $("#btn-video").onclick = async () => {
    $("#video-out").textContent = "વિડિયો બની રહ્યો છે... (~10-20 સે)";
    const voice = confirm("વોઈસ-ઓવર (અવાજ) પણ ઉમેરવો? "
      + "(edge-tts ઈન્સ્ટોલ હોવું જોઈએ)");
    const r = await (await fetch(`/api/news/${n.id}/video`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ voice }) })).json();
    if (r.ok) $("#video-out").innerHTML =
      `<video src="${r.url}" controls style="width:100%;border-radius:10px;margin-top:8px"></video>`;
    else $("#video-out").textContent = r.error || "વિડિયો ભૂલ";
  };
  $("#modal").classList.remove("hidden");
}
$("#modal-close").onclick = () => $("#modal").classList.add("hidden");
$("#modal").addEventListener("click", (e) => {
  if (e.target === $("#modal")) $("#modal").classList.add("hidden");
});

/* ── રિપોર્ટ ── */
$("#report-month").value = new Date().toISOString().slice(0, 7);
$("#report-month").onchange = loadReports;
async function loadReports() {
  const month = $("#report-month").value;
  const r = await (await fetch("/api/reports?month=" + month)).json();
  const t = r.totals || {};
  $("#report-totals").innerHTML = `
    <div class="kpi"><span class="k-ic">✍️</span>
      <b>${t.news_written || 0}</b><small>ન્યુઝ</small></div>
    <div class="kpi"><span class="k-ic">🖼️</span>
      <b>${t.posters_created || 0}</b><small>પોસ્ટર</small></div>
    <div class="kpi"><span class="k-ic">✅</span>
      <b>${t.approved || 0}</b><small>મંજૂર</small></div>
    <div class="kpi"><span class="k-ic">📤</span>
      <b>${t.published_fb || 0}</b><small>FB પોસ્ટ</small></div>
    <div class="kpi"><span class="k-ic">⚠️</span>
      <b>${t.errors || 0}</b><small>ભૂલ</small></div>`;
  const days = (r.days || []).slice().reverse();
  const max = Math.max(1, ...days.map((d) => d.news_written || 0));
  $("#report-chart").innerHTML = days.map((d) =>
    `<div class="bar" style="height:${(d.news_written || 0) / max * 100}%"
       title="${d.date}: ${d.news_written || 0} ન્યુઝ">
       <small>${d.date.slice(8)}</small></div>`).join("") ||
    '<p class="empty-note">આ મહિને ડેટા નથી</p>';
  $("#report-days").innerHTML =
    "<tr><th>તારીખ</th><th>ભેગા</th><th>લખાયા</th><th>પોસ્ટર</th>" +
    "<th>મંજૂર</th><th>રદ</th><th>ભૂલ</th></tr>" +
    (r.days || []).map((d) =>
      `<tr><td>${d.date}</td><td>${d.news_collected}</td>
       <td>${d.news_written}</td><td>${d.posters_created}</td>
       <td>${d.approved}</td><td>${d.rejected}</td><td>${d.errors}</td></tr>`
    ).join("");
  $("#report-agents").innerHTML =
    "<tr><th>એજન્ટ</th><th>રન</th><th>ભૂલ</th><th>સરેરાશ સમય</th></tr>" +
    (r.agents || []).map((a) =>
      `<tr><td>${AGENT_EMOJI[a.agent] || ""} ${a.agent}</td><td>${a.runs}</td>
       <td>${a.errors}</td><td>${(a.avg_ms / 1000).toFixed(1)} સે</td></tr>`
    ).join("");
  try {
    const c = await (await fetch("/api/reports/cost?month=" + month)).json();
    $("#cost-line").textContent =
      `💰 આ મહિને AI તસવીર ખર્ચ (${c.provider}): ≈ ₹${(c.cost||0).toFixed(0)}`;
  } catch {}
  try {
    const a = await (await fetch("/api/accountant?month=" + month)).json();
    $("#acc-total").textContent = `કુલ ખર્ચ: ₹${(a.total||0).toFixed(2)}`;
    $("#acc-table").innerHTML =
      "<tr><th>પ્રકાર</th><th>સર્વિસ</th><th>સંખ્યા</th><th>ખર્ચ ₹</th></tr>" +
      (a.breakdown||[]).map(b =>
        `<tr><td>${b.kind==='image'?'🖼️ તસવીર':'✍️ લખાણ'}</td>
         <td>${b.provider}</td><td>${b.n}</td>
         <td>₹${(b.total||0).toFixed(2)}</td></tr>`).join("") ||
      "<tr><td colspan=4 style='color:var(--muted)'>આ મહિને ખર્ચ નથી</td></tr>";
  } catch {}
}
if ($("#btn-excel")) $("#btn-excel").onclick = () =>
  window.open("/api/reports/excel?month=" + $("#report-month").value, "_blank");
if ($("#btn-report-wa")) $("#btn-report-wa").onclick = async () => {
  const r = await (await fetch("/api/reports/whatsapp", {method:"POST"})).json();
  toast(r.error || "રિપોર્ટ WhatsApp પર મોકલ્યો ✓", r.error ? "bad" : "good");
};

/* ── સેટિંગ ── */
async function loadSettings() {
  const cfg = await (await fetch("/api/settings")).json();
  const form = $("#settings-form");
  for (const el of form.elements) {
    if (!el.name || !(el.name in cfg)) continue;
    if (el.type === "checkbox") el.checked = !!cfg[el.name];
    else el.value = cfg[el.name];
  }
  syncProviderBoxes();          // પસંદ કરેલા પ્રોવાઈડરના જ ખાના બતાવો
}
/* ── પ્રોવાઈડર પ્રમાણે જ ખાના બતાવો ── */
const IMG_LABEL = { aiauto: "AIAuto", local: "લોકલ SD",
  pollinations: "Pollinations", gemini: "Gemini", openai: "OpenAI" };
const KEY_HINT = {
  gemini: "aistudio.google.com/apikey પરથી key લો. ~₹3/તસવીર.",
  openai: "platform.openai.com → API keys. બિલિંગ અલગ છે.",
};
function syncProviderBoxes() {
  const p = $("[name=image_ai_provider]") ? $("[name=image_ai_provider]").value : "";
  document.querySelectorAll(".prov-box").forEach((b) =>
    b.classList.toggle("show", b.dataset.prov.split(" ").includes(p)));
  if ($("#img-key-label")) {
    $("#img-key-label").textContent =
      (p === "openai" ? "OpenAI" : "Gemini") + " API Key";
    $("#img-key").placeholder = p === "openai" ? "sk-..." : "AIza...";
    $("#img-key-hint").textContent = KEY_HINT[p] || "";
  }
  if ($("#btn-img-test"))
    $("#btn-img-test").textContent = `🧪 ${IMG_LABEL[p] || ""} થી ટેસ્ટ તસવીર બનાવો`;
  // ટેક્સ્ટ AI
  const t = $("[name=text_provider]") ? $("[name=text_provider]").value : "";
  document.querySelectorAll(".txt-box").forEach((b) =>
    b.classList.toggle("show", b.dataset.prov.split(" ").includes(t)));
  if ($("#txt-key-label")) {
    $("#txt-key-label").textContent =
      (t === "openai" ? "OpenAI" : "Gemini") + " API Key";
    $("#txt-key").placeholder = t === "openai" ? "sk-..." : "AIza...";
  }
  if ($("#btn-txt-test"))
    $("#btn-txt-test").textContent =
      `🧪 ${t === "ollama" ? "Ollama" : t === "openai" ? "OpenAI" : "Gemini"} થી લેખન ટેસ્ટ`;
}
if ($("[name=image_ai_provider]"))
  $("[name=image_ai_provider]").onchange = syncProviderBoxes;
if ($("[name=text_provider]"))
  $("[name=text_provider]").onchange = syncProviderBoxes;

$("#btn-txt-test").onclick = async () => {
  $("#txt-info").textContent = "લખાવી રહ્યો છું... (પહેલા સેવ કરો)";
  const r = await (await fetch("/api/text-test", { method: "POST" })).json();
  $("#txt-info").textContent = r.error
    ? "❌ " + r.error
    : "✅ " + (r.provider || "") + " ચાલે છે:\n" + (r.sample || "");
  toast(r.error || "લેખન ટેસ્ટ પાસ ✓", r.error ? "bad" : "good");
};

$("#settings-form").onsubmit = async (e) => {
  e.preventDefault();
  const form = e.target, payload = {};
  for (const el of form.elements) {
    if (!el.name) continue;
    if (el.type === "checkbox") payload[el.name] = el.checked;
    else if (el.type === "number") payload[el.name] = Number(el.value);
    else payload[el.name] = el.value;
  }
  await fetch("/api/settings", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload) });
  toast("સેટિંગ સેવ થઈ ગયું ✓", "good");
};
$("#btn-check-update").onclick = async () => {
  $("#update-info").textContent = "ચેક થઈ રહ્યું છે...";
  const r = await (await fetch("/api/update/check", { method: "POST" })).json();
  $("#update-info").textContent = r.error ? r.error :
    r.update_available
      ? `🎉 નવું અપડેટ છે!\nહાલનું: ${r.current} → નવું: ${r.latest}\n${r.message}`
      : `✅ લેટેસ્ટ વર્ઝન છે (${r.current})`;
};
$("#btn-apply-update").onclick = async () => {
  if (!confirm("અપડેટ શરૂ કરવું? બેકઅપ આપોઆપ લેવાશે.")) return;
  $("#update-info").textContent = "અપડેટ ચાલી રહ્યું છે...";
  const r = await (await fetch("/api/update/apply", { method: "POST" })).json();
  $("#update-info").textContent = r.error || r.message;
  toast(r.error || r.message, r.error ? "bad" : "good");
};
$("#btn-img-test").onclick = async () => {
  $("#img-info").textContent =
    "તસવીર બની રહી છે... (~30-60 સેકન્ડ, પહેલા સેવ કરો ભૂલતા નહીં)";
  const r = await (await fetch("/api/image-test", { method: "POST" })).json();
  if (r.ok) {
    $("#img-info").innerHTML =
      `✅ બની ગઈ!<br><img src="${r.url}" style="width:100%;border-radius:10px;margin-top:8px">`;
    toast("AI તસવીર બની ✓", "good");
  } else {
    $("#img-info").textContent = r.error;
    toast("AI તસવીર ભૂલ", "bad");
  }
};
$("#btn-logo-up").onclick = async () => {
  const f = $("#logo-file").files[0];
  if (!f) return toast("પહેલા લોગો ફાઈલ પસંદ કરો", "bad");
  const fd = new FormData(); fd.append("logo", f);
  const r = await (await fetch("/api/logo", { method: "POST", body: fd })).json();
  $("#logo-info").textContent = r.error || "લોગો સેવ થયો ✓ — હવે પોસ્ટરમાં આવશે";
  toast(r.error || "લોગો સેવ થયો ✓", r.error ? "bad" : "good");
};
$("#btn-logo-rm").onclick = async () => {
  await fetch("/api/logo/remove", { method: "POST" });
  $("#logo-info").textContent = "લોગો કઢાયો — ફરી PD બોક્સ આવશે";
  toast("લોગો કઢાયો");
};
$("#btn-tg-test").onclick = async () => {
  $("#tg-info").textContent = "મોકલી રહ્યો છું... (પહેલા સેવ કરો)";
  const r = await (await fetch("/api/telegram-test", { method: "POST" })).json();
  $("#tg-info").textContent = r.error ||
    (r.ok ? "✅ Telegram ચેનલ ચેક કરો!" : "❌ " + JSON.stringify(r.result || ""));
  toast(r.error || (r.ok ? "Telegram ટેસ્ટ ✓" : "Telegram ભૂલ"),
    r.ok ? "good" : "bad");
};
$("#btn-wa-test").onclick = async () => {
  $("#wa-info").textContent = "મોકલી રહ્યો છું... (પહેલા સેવ કરો ભૂલતા નહીં)";
  const r = await (await fetch("/api/whatsapp-test", { method: "POST" })).json();
  $("#wa-info").textContent = r.error ||
    (r.ok ? "✅ મોકલાઈ ગયું — તમારો WhatsApp ચેક કરો! " : "❌ ") +
    JSON.stringify(r.result || "");
  toast(r.error || (r.ok ? "WhatsApp ટેસ્ટ મોકલાયો ✓" : "WhatsApp ભૂલ"),
    r.ok ? "good" : "bad");
};
$("#btn-backup").onclick = async () => {
  const r = await (await fetch("/api/backup", { method: "POST" })).json();
  $("#update-info").textContent = "બેકઅપ: " + r.file;
  toast("બેકઅપ લેવાઈ ગયો ✓", "good");
};
$("#btn-restart").onclick = async () => {
  if (!confirm("સર્વર રીસ્ટાર્ટ કરવું? 5-10 સેકન્ડમાં ફરી ચાલુ થશે.")) return;
  try { await fetch("/api/restart", { method: "POST" }); } catch {}
  toast("સર્વર રીસ્ટાર્ટ થઈ રહ્યું છે... પેજ આપોઆપ ફરી લોડ થશે", "good");
  // ફરી ઉપલબ્ધ થાય ત્યાં સુધી રાહ જોઈ પેજ રીલોડ કરો
  let tries = 0;
  const check = setInterval(async () => {
    tries++;
    try {
      const r = await fetch("/api/status", { cache: "no-store" });
      if (r.ok) { clearInterval(check); location.reload(); }
    } catch {}
    if (tries > 30) { clearInterval(check); location.reload(); }
  }, 1500);
};
