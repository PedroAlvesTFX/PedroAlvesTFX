const SLIDER_SCHEMA = {
    line: [
        { key: "roi_y_start", label: "ROI inicio (%)", min: 0, max: 1, step: 0.01 },
        { key: "black_v_max", label: "Preto V max", min: 0, max: 255, step: 1 },
        { key: "black_s_max", label: "Preto S max", min: 0, max: 255, step: 1 },
        { key: "min_area", label: "Area minima", min: 0, max: 5000, step: 50 },
    ],
    red: [
        { key: "h1_min", label: "H1 min", min: 0, max: 179, step: 1 },
        { key: "h1_max", label: "H1 max", min: 0, max: 179, step: 1 },
        { key: "h2_min", label: "H2 min", min: 0, max: 179, step: 1 },
        { key: "h2_max", label: "H2 max", min: 0, max: 179, step: 1 },
        { key: "s_min", label: "S min", min: 0, max: 255, step: 1 },
        { key: "v_min", label: "V min", min: 0, max: 255, step: 1 },
        { key: "roi_y_start", label: "ROI inicio (%)", min: 0, max: 1, step: 0.01 },
        { key: "min_area", label: "Area minima", min: 0, max: 5000, step: 50 },
    ],
    green: [
        { key: "h_min", label: "H min", min: 0, max: 179, step: 1 },
        { key: "h_max", label: "H max", min: 0, max: 179, step: 1 },
        { key: "s_min", label: "S min", min: 0, max: 255, step: 1 },
        { key: "v_min", label: "V min", min: 0, max: 255, step: 1 },
        { key: "min_area", label: "Area minima", min: 0, max: 5000, step: 50 },
        { key: "merge_gap_px", label: "Gap de merge (px)", min: 0, max: 100, step: 1 },
    ],
    obstacle: [
        { key: "v_max", label: "V max", min: 0, max: 255, step: 1 },
        { key: "s_max", label: "S max", min: 0, max: 255, step: 1 },
        { key: "min_area", label: "Area minima", min: 0, max: 20000, step: 100 },
        { key: "roi_y_start", label: "ROI inicio (%)", min: 0, max: 1, step: 0.01 },
        { key: "roi_y_end", label: "ROI fim (%)", min: 0, max: 1, step: 0.01 },
        { key: "line_exclusion_margin_px", label: "Margem exclusao linha (px)", min: 0, max: 150, step: 1 },
    ],
};

const SECTION_LABELS = { line: "Linha (Preto)", red: "Vermelho", green: "Verde", obstacle: "Obstaculo" };

let currentConfig = null;
let updateTimer = null;

// ===================== Sliders =====================
function renderSliders(config) {
    const container = document.getElementById("sliderGroups");
    container.innerHTML = "";

    for (const section of Object.keys(SLIDER_SCHEMA)) {
        const block = document.createElement("div");
        block.className = "controlBlock";

        const title = document.createElement("h3");
        title.textContent = SECTION_LABELS[section] || section;
        block.appendChild(title);

        for (const field of SLIDER_SCHEMA[section]) {
            const value = config[section]?.[field.key] ?? field.min;

            const row = document.createElement("div");
            row.className = "sliderRow";

            const label = document.createElement("label");
            label.innerHTML = `<span>${field.label}</span><span class="val" id="val-${section}-${field.key}">${value}</span>`;
            row.appendChild(label);

            const input = document.createElement("input");
            input.type = "range";
            input.min = field.min;
            input.max = field.max;
            input.step = field.step;
            input.value = value;
            input.dataset.section = section;
            input.dataset.key = field.key;
            input.id = `slider-${section}-${field.key}`;

            input.addEventListener("input", onSliderChange);

            row.appendChild(input);
            block.appendChild(row);
        }

        container.appendChild(block);
    }
}

function updateSliderValues(config) {
    for (const section of Object.keys(SLIDER_SCHEMA)) {
        for (const field of SLIDER_SCHEMA[section]) {
            const value = config[section]?.[field.key];
            if (value === undefined) continue;

            const slider = document.getElementById(`slider-${section}-${field.key}`);
            const label = document.getElementById(`val-${section}-${field.key}`);
            if (slider) slider.value = value;
            if (label) label.textContent = value;
        }
    }
}

function onSliderChange(e) {
    const section = e.target.dataset.section;
    const key = e.target.dataset.key;
    const value = parseFloat(e.target.value);

    document.getElementById(`val-${section}-${key}`).textContent = value;

    clearTimeout(updateTimer);
    updateTimer = setTimeout(() => sendConfigUpdate(section, key, value), 120);
}

async function sendConfigUpdate(section, key, value) {
    try {
        await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ [section]: { [key]: value } }),
        });
    } catch (e) { /* proxima tentativa de slider corrige sozinha */ }
}

// ===================== Config: carregar / salvar / descartar =====================
async function loadConfig() {
    const r = await fetch("/api/config");
    currentConfig = await r.json();
    renderSliders(currentConfig);

    const stateSelect = document.getElementById("stateSelect");
    if (currentConfig.state) stateSelect.value = currentConfig.state;
}

document.getElementById("saveBtn").addEventListener("click", async () => {
    const statusEl = document.getElementById("configStatus");
    try {
        await fetch("/api/config/save", { method: "POST" });
        statusEl.textContent = "Salvo em config/hsv.json.";
        statusEl.className = "ok";
    } catch (e) {
        statusEl.textContent = "Erro ao salvar.";
        statusEl.className = "error";
    }
});

document.getElementById("loadBtn").addEventListener("click", async () => {
    const statusEl = document.getElementById("configStatus");
    try {
        const r = await fetch("/api/config/load", { method: "POST" });
        const data = await r.json();
        updateSliderValues(data.config);
        statusEl.textContent = "Recarregado do disco (mudancas nao salvas foram descartadas).";
        statusEl.className = "ok";
    } catch (e) {
        statusEl.textContent = "Erro ao recarregar.";
        statusEl.className = "error";
    }
});

// ===================== Estado da missao =====================
document.getElementById("stateSelect").addEventListener("change", async (e) => {
    await fetch("/api/state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: e.target.value }),
    });
});

// ===================== Abas de imagem =====================
document.querySelectorAll(".imgTabButton").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".imgTabButton").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById("streamImg").src = "/video_feed/" + btn.dataset.stream + "?t=" + Date.now();
    });
});

// ===================== Status (polling) =====================
function fmtGreen(g) {
    const map = { none: "nenhum", left: "esquerda", right: "direita", both: "ambos" };
    return map[g] || g;
}

async function pollStatus() {
    try {
        const r = await fetch("/api/status");
        if (!r.ok) return;
        const s = await r.json();

        document.getElementById("fpsBadge").textContent = "FPS: " + s.objects.fps;
        document.getElementById("cpuBadge").textContent = "CPU: " + (s.cpu_percent ?? "--") + "%";

        const timing = s.objects.timing_ms || {};
        const timingStr = Object.entries(timing).map(([k, v]) => `${k}:${v}ms`).join(" ");
        document.getElementById("timingBadge").textContent = "Proc: " + (timingStr || s.objects.total_ms + "ms total");

        const uartBadge = document.getElementById("uartBadge");
        uartBadge.textContent = "UART: " + (s.uart_connected ? "conectado" : "desconectado");
        uartBadge.className = "badge " + (s.uart_connected ? "ok" : "error");

        document.getElementById("stateBadge").textContent = "Estado: " + s.state;

        const line = s.objects.line;
        document.getElementById("roLine").textContent = line.present
            ? `erro ${line.error} / angulo ${line.angle}°`
            : "sem linha";

        const green = s.objects.green;
        document.getElementById("roGreen").textContent = fmtGreen(green.side) + ` (${green.count})`;

        const red = s.objects.red;
        document.getElementById("roRed").textContent = red.present ? `${red.distance_mm} mm` : "nao detectado";

        const obstacle = s.objects.obstacle;
        document.getElementById("roObstacle").textContent = obstacle.present ? "SIM" : "nao";
    } catch (e) { /* Pi reiniciando/etc -- tenta de novo no proximo ciclo */ }
}
setInterval(pollStatus, 500);
pollStatus();

loadConfig();
