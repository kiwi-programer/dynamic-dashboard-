function pad(n) {
    return String(n).padStart(2, "0");
}

function updateClock() {
    const now = new Date();
    const timeStr = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;

    const el = document.getElementById("live-clock");
    if (el) el.textContent = timeStr;

    const ssClock = document.getElementById("ss-clock");
    if (ssClock) ssClock.textContent = timeStr;

    const ssDate = document.getElementById("ss-date");
    if (ssDate) {
        const days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
        const months = ["January","February","March","April","May","June",
                        "July","August","September","October","November","December"];
        ssDate.textContent = `${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}, ${now.getFullYear()}`;
    }

    const dateEl = document.getElementById("tray-date");
    if (dateEl) {
        dateEl.textContent = `${pad(now.getMonth() + 1)}/${pad(now.getDate())}`;
    }
}

let timerHandle = null;
let timerRemaining = 0;

function renderTimer() {
    const el = document.getElementById("timer-display");
    if (!el) return;
    const mins = Math.floor(timerRemaining / 60);
    const secs = timerRemaining % 60;
    el.textContent = `${pad(mins)}:${pad(secs)}`;
}

function stopTimer() {
    if (timerHandle) {
        clearInterval(timerHandle);
        timerHandle = null;
    }
    timerRemaining = 0;
    renderTimer();
}

function startTimer(seconds) {
    if (timerHandle) clearInterval(timerHandle);
    timerRemaining = Number(seconds) || 0;
    renderTimer();
    timerHandle = setInterval(() => {
        timerRemaining -= 1;
        if (timerRemaining <= 0) {
            stopTimer();
            showToast("Timer finished");
            alert("Timer finished");
            return;
        }
        renderTimer();
    }, 1000);
}

function setupTimers() {
    document.querySelectorAll(".start-timer").forEach((btn) => {
        btn.addEventListener("click", () => {
            startTimer(btn.dataset.seconds);
        });
    });
    const stopBtn = document.getElementById("timer-stop");
    if (stopBtn) stopBtn.addEventListener("click", stopTimer);
    renderTimer();
}

function setupGradeImpact() {
    const btn = document.getElementById("calc-impact");
    const result = document.getElementById("impact-result");
    if (!btn || !result) return;

    btn.addEventListener("click", () => {
        const earned = Number(document.getElementById("points-earned").value);
        const possible = Number(document.getElementById("points-possible").value);
        const assignmentPoints = Number(document.getElementById("assignment-points").value);
        const expectedScore = Number(document.getElementById("expected-score").value);

        if (!possible || !assignmentPoints || Number.isNaN(earned) || Number.isNaN(expectedScore)) {
            result.textContent = "Please enter valid numbers.";
            return;
        }

        const safeExpected = Math.max(0, Math.min(expectedScore, assignmentPoints));
        const newPercent = ((earned + safeExpected) / (possible + assignmentPoints)) * 100;
        result.textContent = `Estimated grade after assignment: ${newPercent.toFixed(2)}%`;
        showToast("Grade impact calculated");
    });
}

// ── Screensaver ──
const SCREENSAVER_DELAY = 30000; // 30 seconds of inactivity
let screensaverTimer = null;
let screensaverActive = false;

function showScreensaver() {
    const el = document.getElementById("screensaver");
    if (el) {
        el.classList.remove("hidden");
        screensaverActive = true;
    }
}

function hideScreensaver() {
    const el = document.getElementById("screensaver");
    if (el) {
        el.classList.add("hidden");
        screensaverActive = false;
    }
}

function resetScreensaverTimer() {
    if (screensaverActive) {
        hideScreensaver();
    }
    clearTimeout(screensaverTimer);
    screensaverTimer = setTimeout(showScreensaver, SCREENSAVER_DELAY);
}

function setupScreensaver() {
    // Dismiss on tap/click
    const el = document.getElementById("screensaver");
    if (el) {
        el.addEventListener("click", hideScreensaver);
        el.addEventListener("touchstart", hideScreensaver);
    }
    // Reset timer on any user interaction
    ["mousemove", "mousedown", "keydown", "touchstart", "scroll"].forEach((evt) => {
        document.addEventListener(evt, resetScreensaverTimer, { passive: true });
    });
    // Start the initial countdown
    screensaverTimer = setTimeout(showScreensaver, SCREENSAVER_DELAY);
}

function showToast(message) {
    const wrap = document.getElementById("toast-wrap");
    if (!wrap) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    wrap.appendChild(toast);
    setTimeout(() => toast.remove(), 2400);
}

function toggleLauncher(forceOpen = null) {
    const launcher = document.getElementById("launcher");
    if (!launcher) return;
    const shouldOpen = forceOpen === null ? launcher.classList.contains("hidden") : forceOpen;
    launcher.classList.toggle("hidden", !shouldOpen);
    launcher.setAttribute("aria-hidden", shouldOpen ? "false" : "true");
    if (shouldOpen) {
        const input = document.getElementById("app-search");
        if (input) input.focus();
    }
}

function filterLauncherApps(value) {
    const q = value.trim().toLowerCase();
    document.querySelectorAll(".launcher-item").forEach((item) => {
        const text = item.textContent.toLowerCase();
        item.classList.toggle("hidden", q && !text.includes(q));
    });
}

function toggleFocusMode() {
    const active = document.body.classList.toggle("os-focus");
    localStorage.setItem("os-focus", active ? "1" : "0");
    showToast(active ? "Focus mode enabled" : "Focus mode disabled");
}

function setupLauncher() {
    const openBtn = document.getElementById("launcher-btn");
    const closeBtn = document.getElementById("launcher-close");
    const launcher = document.getElementById("launcher");
    const search = document.getElementById("app-search");

    if (openBtn) openBtn.addEventListener("click", () => toggleLauncher(true));
    if (closeBtn) closeBtn.addEventListener("click", () => toggleLauncher(false));
    if (launcher) {
        launcher.addEventListener("click", (event) => {
            if (event.target === launcher) toggleLauncher(false);
        });
    }
    if (search) {
        search.addEventListener("input", () => filterLauncherApps(search.value));
    }

    document.querySelectorAll(".launcher-item[data-action]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const action = btn.dataset.action;
            if (action === "focus-mode") toggleFocusMode();
            if (action === "refresh") window.location.reload();
        });
    });

    document.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
            event.preventDefault();
            toggleLauncher(true);
        }
        if (event.key === "Escape") {
            toggleLauncher(false);
        }
    });
}

function setupFormFeedback() {
    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", () => showToast("Saved"));
    });
}

function setupTouchScroll() {
    document.querySelectorAll(".content, .item-list").forEach((el) => {
        el.style.webkitOverflowScrolling = "touch";
        el.style.touchAction = "pan-y";
    });
}

if (typeof lucide !== 'undefined') lucide.createIcons();
updateClock();
setInterval(updateClock, 1000);
setupTimers();
setupGradeImpact();
setupLauncher();
setupFormFeedback();
setupTouchScroll();
setupScreensaver();

if (localStorage.getItem("os-focus") === "1") {
    document.body.classList.add("os-focus");
}