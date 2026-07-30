/* AI Newsroom ડેશબોર્ડ — WebSocket લાઈવ એનિમેશન + અપ્રુવલ + રિપોર્ટ + સેટિંગ */
const $ = (s) => document.querySelector(s);
const AGENTS = ["ceo", "scout", "editor", "proofreader", "designer",
                "photo", "publisher", "inbox", "analyst"];
const STATE_LABEL = {
  idle: "⚪ નિષ્ક્રિય", thinking: "🔵 વિચારે", working: "🟢 ચાલુ",
  waiting: "🟠 રાહ", done: "✅ પૂર્ણ", error: "🔴 ભૂલ",
};

/* ── ટેબ ── */
document.querySelectorAll(".nav-btn").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach((x) => x.classList.remove("active"));
    document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    $("#tab-" + b.dataset.tab).classList.add("active");
    if (b.dataset.tab === "approval") loadApproval();
    if (b.dataset.tab === "reports") loadReports();
    if (b.dataset.tab === "settings") loadSettings();
  }));

/* ── ઘડિયાળ ── */
setInterval(() => {
  $("#clock").textContent = new Date().toLocaleTimeString("gu-IN", { hour12: false });
}, 1000);

/* ── એજન્ટ ગ્રાફ: SVG લાઈન દોરો ── */
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
function drawEdges() {
  const svg = $("#edges");
  svg.innerHTML = "";
  for (const [a, b] of EDGE_PAIRS) {
    const p1 = nodeCenter(a), p2 = nodeCenter(b);
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", `M ${p1.x} ${p1.y} L ${p2.x} ${p2.y}`);
    path.setAttribute("class", "edge");
    path.id = `edge-${a}-${b}`;
    svg.appendChild(path);
  }
}
window.addEventListener("resize", drawEdges);
drawEdges();

/* ⭐ CEO કામ વહેંચે — લાઈન પર ટપકું દોડે */
function runDot(from, to) {
  const path = $(`#edge-${from}-${to}`) || $(`#edge-${to}-${from}`);
  if (!path) return;
  path.classList.add("active");
  setTimeout(() => path.classList.remove("active"), 2500);
  const svg = $("#edges");
  const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  dot.setAttribute("r", "6");
  dot.setAttribute("class", "dot");
  const anim = document.createElementNS("http://www.w3.org/2000/svg", "animateMotion");
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
  li.innerHTML = `<span class="t">${time}</span>${emoji(ev.agent)} ${ev.message}`;
  const log = $("#live-log");
  log.prepend(li);
  while (log.children.length > 80) log.lastChild.remove();
}
function emoji(agent) {
  return { ceo: "👑", scout: "🔍", editor: "✍️", proofreader: "🔤",
           designer: "🎨", photo: "📷", publisher: "📤", inbox: "💬",
           analyst: "📊", updater: "🔄" }[agent] || "•";
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
    $("#ollama-status").textContent =
      "Ollama: " + (s.ollama ? "✅ ચાલુ" : "❌ બંધ (ડેમો મોડ)");
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

/* ── બટન: દિવસ શરૂ / પ્રેસ નોટ ── */
$("#btn-run").onclick = async () => {
  const r = await (await fetch("/api/run-day", { method: "POST" })).json();
  alert(r.message || r.error);
};
$("#btn-press").onclick = async () => {
  const text = $("#press-text").value.trim();
  if (!text) return alert("પ્રેસ નોટનું લખાણ લખો");
  const fd = new FormData();
  fd.append("text", text);
  const r = await (await fetch("/api/press-note", { method: "POST", body: fd })).json();
  alert(r.message || r.error);
  if (r.ok) $("#press-text").value = "";
};

/* ── અપ્રુવલ ── */
async function loadApproval() {
  const list = await (await fetch("/api/news?status=pending_approval")).json();
  const wrap = $("#approval-list");
  wrap.innerHTML = list.length ? "" :
    "<p>કોઈ ન્યુઝ અપ્રુવલની રાહમાં નથી 🎉</p>";
  for (const n of list) {
    const img = n.posters?.[0]?.url
      ? `<img src="${n.posters[0].url}" loading="lazy">` : "";
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `${img}<h4>${n.title}</h4><p>${n.body}</p>
      <div class="row">
        <button class="approve">✅ મંજૂર + પબ્લિશ</button>
        <button class="reject">❌ રદ</button>
      </div>`;
    div.querySelector(".approve").onclick = async () => {
      div.style.opacity = .5;
      await fetch(`/api/news/${n.id}/approve`, { method: "POST" });
      loadApproval(); refreshStatus();
    };
    div.querySelector(".reject").onclick = async () => {
      await fetch(`/api/news/${n.id}/reject`, { method: "POST" });
      loadApproval(); refreshStatus();
    };
    wrap.appendChild(div);
  }
}

/* ── રિપોર્ટ ── */
$("#report-month").value = new Date().toISOString().slice(0, 7);
$("#report-month").onchange = loadReports;
async function loadReports() {
  const month = $("#report-month").value;
  const r = await (await fetch("/api/reports?month=" + month)).json();
  const t = r.totals || {};
  $("#report-totals").innerHTML = `
    <div class="tile"><b>${t.news_written || 0}</b>ન્યુઝ</div>
    <div class="tile"><b>${t.posters_created || 0}</b>પોસ્ટર</div>
    <div class="tile"><b>${t.approved || 0}</b>મંજૂર</div>
    <div class="tile"><b>${t.rejected || 0}</b>રદ</div>
    <div class="tile"><b>${t.published_fb || 0}</b>FB પોસ્ટ</div>
    <div class="tile"><b>${t.errors || 0}</b>ભૂલ</div>`;
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
      `<tr><td>${emoji(a.agent)} ${a.agent}</td><td>${a.runs}</td>
       <td>${a.errors}</td><td>${Math.round(a.avg_ms || 0)} ms</td></tr>`
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
  alert("સેવ થઈ ગયું ✅");
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
};
$("#btn-backup").onclick = async () => {
  const r = await (await fetch("/api/backup", { method: "POST" })).json();
  $("#update-info").textContent = "બેકઅપ: " + r.file;
};
