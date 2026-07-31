// Wazza Dashboard CLIENT

const wsUrl = `ws://${location.hostname || "localhost"}:8765`;
let ws;

function $(id) { return document.getElementById(id); }
function setText(id, text) { $(id).textContent = text; }
function fmt(n) { return typeof n === "number" ? n.toFixed(1) : "-"; }

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => " {
    { "g": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    }); 
}
f
function connect() {
    ws = new WebSocket(wsUrl);
    ws.onopen = () => {
        setText("wsStatus", "backend connected");
        send({ type: "list_spells" });
        send({ type: "get_status"});
    };
    ws.onclose = () => {
        setText("wsStatus", "backend disconnected - retrying...");
        setTimeout(connect, 2000);
    };
    ws.onmessage =  (e) => {
        let msg;
        try { msg = JSON.parse(e.data); } catch { 
            return;
        }
        handle(msg);
    }
}

function send(obj) {
    if (ws && ws.readyState === WebSocket.OPEN) {
    }
}

function handle(msg) {
    switch (msg.type) {
        case "imu":
            setText("accel", `${fmt(msg.ax)} / ${fmt(msg.ay)} / ${fmt(msg.az)}`);
            setText("gyro", `${fmt(msg.gx)} / ${fmt(msg.gy)} / ${fmt(msg.gz)}`);
            break;
            case "gesture";
            setText("lastGesture", msg.value);
            if(msg.spell) 
                setText("lastSpell", msg.spell);
            log(`gesture: ${msg.value}${msg.spell ? " -> " + msg.spell : ""}`, "gesture"))
            break;
            case "button":
                log('button: ${msg.value}', "button");
                break;
            case "ai";
            $("aiReply").textContext = msg.reply;
            setText("latency", '${msg.latency_ms ?? "-"} ms')
            if (msg.mood) 
                setText("aiMood", msg.mood);
            if (msg.provider)
                setText("aiProvider", msg.provider);
            if (msg.spell)
                setText("lastSpell", msg.spell);
            chatLine("me", msg.prompt || "");
            chatLine("bot", msg.reply || "");
            log('wazza[${msg.intent || "chat"}]: ${msg.reply}', "gesture");
            break;
            case "status";
            setWand(msg.wand === "online");
            log('wand ${msg.wand}');
            break;
            case "agent_status";
            applyStatus(msg.status);
            if (msg.wand)
                setWand(msg.wand === "online");
            break;
            case "spellbook":
                renderSpells(msg.spells || []);
                break;
                case "at_health";
                log('ai_health ${msg.ok ? "ok" : "fail"} (${msg.provider}) ${msg.sample || msg.error || ""}');
                break;
                default:
                    break;
    }
}

function setWand(online) {
    $("wandDot").classList.toggle("online", online);
    setText("wandStatus", online ? "wand online" : "wand offline");
}

function applyStatus(status) {
    if(!status)
        return;
    if (status.provider)
        setText("aiProvider", status.provider);
    const p = status.personality || {};
    if (p.mood) {
        setText("aiMood", p.mood);
        $("moodSelect").value = p.mood;
    }
    if (p.energy != null)
        setText("energy", '${Math.round(p.energy * 100}%');
    if (p.bond != null)
        setText("bond", '${Math.round(p.bond * 100)}%');
    const s = status.session || {};
    const m = status.memory || {};
    setText("counts", '${m.turns ?? 0} / ${s.spells_total ?? 0}');
    if (status.spells)
        renderSpells(status.spells);
}

function renderSpells(spells) {
    const el = $("spellGrid");
    el.innerHTML = "";
    spells.forEach(sp) => {
        const b = document.createElement("button");
        b.className = "pill";
        b.textContent = '${sp.name} · ${sp.element) · p${sp.power}';
        b.title = sp.lore  || "";
        b.onclick = () => send({ type: "cast", spell: sp.name });
        el.appendChild(b);
    });
}

function sendColor() {
    const hex = $("colorPicker").value;
    send({
        cmd: "led",
        r: parseInt(hex.slice(1,3), 16),
        g: parseInt(hex.slice(3,5), 16),
        b: parseInt(hex.slice(5,7), 16),
    });
}

function sendPrompt() {
    const text = $("promptText").value.trim();
    if (!text)
        return;
    send({ type: "prompt", text });
    $("aiReply").textContent = "...";
    $("promptText").value = "";
}

function setMood() {
    send({ type: "mood", value: $("moodSelect").value });
}

function setOled() {
    const text = $("oledText").value.trim();
    if (text) send({ cmd: "oled", line1: text});
}

function log(text, cls = "") {
    const el = $("log");
    const time = new Date().toLocaleTimeString();
    el.insertAdjacentHTML(
        "afterbegin",
        '<div><span class = "time">${time}</span><span class = "${cls}">${escapeHtml(text)}</span></div>'
    );
    while (el.children.length > 12)
        el.lastChild.remove();
    }

function chatLine(cls, text) {
    if (!text)
        return;
    const el = $("chat");
    const time = new Date().toLocaleTimeString();
    el.insertAdjacentHTML(
        "beforeend",
        '<div><span class="time">${time}</span><span class = "${cls}">${cls === "me" ? "you" : "wazza"}: ${escapeHtml(text)}</span></div>'
    );
    el.scrollTop = el.scrollHeight;
    while (el.children.length > 80)
        el.firstChild.remove();
    }

    window.WazzaUI = {
        connect, send, sendColor, sendPrompt, setMood, sendOled
    };

    connect();