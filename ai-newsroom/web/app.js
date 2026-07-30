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
  birthday: "જન્મદિવસ" };
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

/* ── રન બટન — પહેલા પૂછે: કેટલા ન્યુઝ, કેટલી AI તસવીર ── */
const IMG_COST = { pollinations: 0, gemini: 3, openai: 3.5 };
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
  const text = $("#press-text").value.trim();
  const files = [...$("#press-photo").files].slice(0, 3);
  if (!text && !files.length) return toast("પ્રેસ નોટનું લખાણ લખો", "bad");
  const fd = new FormData();
  fd.append("text", text);
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
        ${posters.length > 1 ? `<div class="size-tabs">${tabs}</div>` : ""}
      </div>
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

async function loadNews() {
  const q = newsFilter ? `?status=${newsFilter}&limit=100` : "?limit=100";
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
    </div>
    <h3 style="margin-bottom:10px">${n.title}</h3>
    <p style="color:var(--ink-2);font-size:14px">${n.body}</p>
    ${n.source_url ? `<p style="margin-top:10px;font-size:12px">
      સોર્સ: <a href="${n.source_url}" target="_blank"
      style="color:var(--blue)">${n.source_title || n.source_url}</a></p>` : ""}
    <div class="modal-posters">${posters}</div>`;
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
}

/* ── સેટિંગ ── */
async function loadSettings() {
  const cfg = await (await fetch("/api/settings")).json();
  const form = $("#settings-form");
  for (const el of form.elements) {
    if (!el.name || !(el.name in cfg)) continue;
    if (el.type === "checkbox") el.checked = !!cfg[el.name];
    else el.value = cfg[el.name];
  }
}
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
