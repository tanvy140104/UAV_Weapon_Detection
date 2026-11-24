/* History browsing, filtering, paging, evidence and alert review. */
(() => {
    const el = id => document.getElementById(id);
    const body = el("history-body"), status = el("history-status");
    const previous = el("history-prev"), next = el("history-next"), page = el("history-page");
    const refresh = el("history-refresh"), form = el("history-filters");
    const modal = el("evidence-modal"), image = el("evidence-image");
    const labels = {knife: "Dao", stick: "Gậy", gun: "Súng"};
    const statuses = {NEW: "Chưa xác nhận", CONFIRMED: "Đã xác nhận", FALSE_POSITIVE: "Nhận diện sai"};
    const limit = 20;
    let offset = 0, total = 0, controller = null, updating = false;
    let activeFilters = new URLSearchParams();

    function cell(value) {
        const td = document.createElement("td");
        td.textContent = String(value);
        return td;
    }
    function button(text, css, handler) {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "history-action " + css;
        item.textContent = text;
        item.addEventListener("click", handler);
        return item;
    }
    async function api(url, options) {
        const response = await fetch(url, {cache: "no-store", ...options});
        const data = await response.json();
        if (!response.ok) {
            const detail = typeof data.detail === "string" ? data.detail : "Dữ liệu lọc không hợp lệ";
            throw new Error(detail + (data.request_id ? " · Mã lỗi: " + data.request_id : ""));
        }
        return data;
    }
    function formatTime(value) {
        if (!value) return "Không rõ";
        // History API returns UTC without a suffix for compatibility with older records.
        const iso = String(value).replace(" ", "T");
        const date = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : iso + "Z");
        return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("vi-VN", {
            timeZone: "Asia/Ho_Chi_Minh", hour12: false
        });
    }
    function showEvidence(item) {
        el("evidence-title").textContent = "Ảnh bằng chứng #" + item.detection_id;
        el("evidence-message").textContent = "Đang tải ảnh...";
        image.hidden = true;
        modal.hidden = false;
        image.src = "/api/evidence/" + item.detection_id + "/image";
        el("evidence-close").focus();
    }
    function closeEvidence() {
        modal.hidden = true;
        image.hidden = true;
        image.removeAttribute("src");
    }
    image.addEventListener("load", () => {
        if (modal.hidden) return;
        image.hidden = false;
        el("evidence-message").textContent = "Ảnh tại thời điểm phát hiện.";
    });
    image.addEventListener("error", () => {
        if (!modal.hidden) el("evidence-message").textContent = "Không tải được ảnh bằng chứng.";
    });
    el("evidence-close").addEventListener("click", closeEvidence);
    modal.addEventListener("click", event => { if (event.target === modal) closeEvidence(); });
    document.addEventListener("keydown", event => { if (event.key === "Escape") closeEvidence(); });

    async function updateAlert(item, value) {
        if (updating) return;
        updating = true;
        try {
            await api("/api/alerts/" + item.detection_id + "/status", {
                method: "PATCH", headers: {"Content-Type": "application/json"},
                body: JSON.stringify({alert_status: value})
            });
            await load();
        } catch (error) {
            status.textContent = "Cập nhật thất bại: " + error.message;
        } finally {
            updating = false;
        }
    }
    function render(item, index) {
        const row = document.createElement("tr");
        row.append(cell(offset + index + 1), cell(labels[item.label] || item.label),
            cell((Number(item.confidence) * 100).toFixed(1) + "%"),
            cell(formatTime(item.detected_at)));
        const session = cell(String(item.session_id).slice(0, 8) + "...");
        session.title = item.session_id;
        row.append(session);
        const actions = cell(statuses[item.alert_status] || item.alert_status);
        const controls = document.createElement("div");
        controls.className = "history-actions";
        if (item.snapshot_path) controls.append(button("Xem ảnh", "history-action-image", () => showEvidence(item)));
        if (item.alert_status === "NEW") {
            controls.append(
                button("Xác nhận", "history-action-confirm", () => updateAlert(item, "CONFIRMED")),
                button("Nhận diện sai", "history-action-false", () => updateAlert(item, "FALSE_POSITIVE"))
            );
        } else {
            controls.append(button("Đặt lại", "history-action-reset", () => updateAlert(item, "NEW")));
        }
        actions.append(controls);
        row.append(actions);
        return row;
    }
    async function load() {
        if (controller) controller.abort();
        const request = new AbortController();
        controller = request;
        previous.disabled = next.disabled = refresh.disabled = true;
        try {
            const params = new URLSearchParams(activeFilters);
            params.set("limit", limit);
            params.set("offset", offset);
            const data = await api("/api/history?" + params, {signal: request.signal});
            if (controller !== request) return;
            total = data.total;
            if (total > 0 && offset >= total) {
                offset = Math.floor((total - 1) / limit) * limit;
                return await load();
            }
            body.replaceChildren(...data.detections.map(render));
            if (!data.count) {
                const row = document.createElement("tr"), empty = cell("Không có phát hiện phù hợp.");
                empty.colSpan = 6;
                row.append(empty);
                body.append(row);
            }
            status.textContent = "Tổng " + total + " phát hiện phù hợp.";
            page.textContent = total ? (offset + 1) + "–" + (offset + data.count) + " / " + total : "0 / 0";
        } catch (error) {
            if (error.name !== "AbortError") status.textContent = "Không tải được lịch sử: " + error.message;
        } finally {
            if (controller === request) {
                controller = null;
                refresh.disabled = false;
                previous.disabled = offset === 0;
                next.disabled = offset + limit >= total;
            }
        }
    }
    form.addEventListener("submit", event => {
        event.preventDefault();
        const filters = new URLSearchParams();
        for (const [key, id] of [["session_id", "history-session"], ["label", "history-label"],
                                ["alert_status", "history-alert-status"]]) {
            const value = el(id).value.trim();
            if (value) filters.set(key, value);
        }
        const from = el("history-from").value, to = el("history-to").value;
        if (from && to && new Date(from) > new Date(to)) {
            status.textContent = "Thời điểm bắt đầu phải trước thời điểm kết thúc.";
            return;
        }
        if (from) filters.set("date_from", new Date(from).toISOString());
        if (to) filters.set("date_to", new Date(to).toISOString());
        activeFilters = filters;
        offset = 0;
        load();
    });
    previous.addEventListener("click", () => { offset = Math.max(0, offset - limit); load(); });
    next.addEventListener("click", () => { offset += limit; load(); });
    refresh.addEventListener("click", load);
    setInterval(() => {
        if (document.visibilityState === "visible" && !updating && !controller) load();
    }, 5000);
    load();
})();
