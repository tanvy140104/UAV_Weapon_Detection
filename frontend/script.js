
/* ==========================================
   UAV WEAPON DETECTION - FRONTEND
   Video + Session + AI Detection
   ========================================== */

// ==========================================
// 1. LAY CAC THANH PHAN GIAO DIEN
// ==========================================

// Quan ly phien giam sat
const sessionInput = document.getElementById("session-id");
const sourceInput = document.getElementById("video-source");

const createSessionButton =
    document.getElementById("create-session-btn");

const startButton = document.getElementById("start-btn");
const stopButton = document.getElementById("stop-btn");

const statusText = document.getElementById("status-text");
const messageText = document.getElementById("message-text");

// Video tu Backend
const videoStream = document.getElementById("video-stream");

const videoPlaceholder =
    document.getElementById("video-placeholder");

// Khu vuc AI moi
const aiImageInput =
    document.getElementById("ai-image-input");

const aiDetectButton =
    document.getElementById("ai-detect-btn");

const aiStatus =
    document.getElementById("ai-status");

const aiCanvas =
    document.getElementById("ai-canvas");

const aiContext = aiCanvas.getContext("2d");

const aiDetectionList =
    document.getElementById("ai-detection-list");

const aiResultJson =
    document.getElementById("ai-result-json");


// ==========================================
// 2. CAC BIEN QUAN LY
// ==========================================

let currentStatus = null;
let isBusy = false;
let activeVideoSession = null;
let loadedSessionId = null;

// Kiem tra trang thai xu ly AI
let isDetecting = false;

// Ten doi tuong
const AI_LABELS = {
    knife: "Dao",
    stick: "Gậy",
    gun: "Súng"
};

// Mau hien thi bounding box
const AI_COLORS = {
    knife: "#ef4444",
    stick: "#f59e0b",
    gun: "#8b5cf6"
};


// ==========================================
// 3. HAM HO TRO
// ==========================================

function getSessionId() {
    return sessionInput.value.trim();
}

function showMessage(message) {
    messageText.textContent = message;
}


// ==========================================
// 4. CAP NHAT TRANG THAI PHIEN
// ==========================================

function updateStatus(status) {

    currentStatus = status;

    statusText.textContent =
        status || "CHƯA XÁC ĐỊNH";

    statusText.classList.remove(
        "status-running",
        "status-stopped"
    );

    if (status === "RUNNING") {
        statusText.classList.add("status-running");
    }

    if (status === "STOPPED") {
        statusText.classList.add("status-stopped");
    }

    startButton.disabled =
        isBusy || status !== "STOPPED";

    stopButton.textContent = status === "ERROR" ? "Đặt lại phiên lỗi" : "Dừng giám sát";

    stopButton.disabled =
        isBusy || !["RUNNING", "ERROR"].includes(status);

    createSessionButton.disabled =
        isBusy || status === "RUNNING";

    sessionInput.disabled =
        isBusy || status === "RUNNING";

    sourceInput.disabled =
        isBusy || status === "RUNNING";
}


// ==========================================
// 5. AN VIDEO
// ==========================================

function hideVideo() {

    videoStream.removeAttribute("src");

    videoStream.hidden = true;
    videoPlaceholder.hidden = false;

    videoPlaceholder.textContent =
        "Chưa bắt đầu giám sát";

    activeVideoSession = null;
}


// ==========================================
// 6. PHAT VIDEO MJPEG TU BACKEND
// ==========================================

function showVideo(sessionId) {

    if (activeVideoSession === sessionId) {
        return;
    }

    const videoUrl =
        `/videos/sessions/${encodeURIComponent(sessionId)}/monitor`;

    videoStream.src = videoUrl;

    videoStream.hidden = false;
    videoPlaceholder.hidden = true;

    activeVideoSession = sessionId;
}


// ==========================================
// 7. HAM GOI API JSON
// ==========================================

async function callApi(url, method = "GET", body = null) {

    const options = {
        method: method,
        cache: "no-store"
    };

    if (body !== null) {

        options.headers = {
            "Content-Type": "application/json"
        };

        options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    const data = await response.json();

    if (!response.ok) {

        throw new Error(
            typeof data.detail === "string"
                ? data.detail
                : `HTTP ${response.status}`
        );
    }

    return data;
}


// ==========================================
// 8. TAI TRANG THAI PHIEN
// ==========================================

async function loadSessionStatus() {

    if (isBusy) {
        return;
    }

    const sessionId = getSessionId();

    if (
        currentStatus === "RUNNING" &&
        loadedSessionId &&
        sessionId !== loadedSessionId
    ) {

        sessionInput.value = loadedSessionId;

        showMessage(
            "Hãy dừng giám sát trước khi đổi phiên."
        );

        return;
    }

    hideVideo();

    if (!sessionId) {

        loadedSessionId = null;
        updateStatus(null);

        showMessage(
            "Nhập mã phiên hoặc tạo phiên giám sát mới."
        );

        return;
    }

    isBusy = true;
    updateStatus(currentStatus);

    showMessage("Đang kiểm tra phiên giám sát...");

    try {

        const session = await callApi(
            `/sessions/${encodeURIComponent(sessionId)}`
        );

        loadedSessionId = sessionId;

        updateStatus(session.status);

        if (session.status === "RUNNING") {

            showVideo(sessionId);

            showMessage(
                "Phiên giám sát đang hoạt động."
            );

        } else {

            showMessage(
                "Phiên đã sẵn sàng để bắt đầu."
            );
        }

    } catch (error) {

        loadedSessionId = null;
        currentStatus = null;

        showMessage(
            "Không thể tải phiên: " + error.message
        );

    } finally {

        isBusy = false;
        updateStatus(currentStatus);
    }
}


// ==========================================
// 9. TAO PHIEN GIAM SAT MOI
// ==========================================

async function createSession() {

    if (isBusy || currentStatus === "RUNNING") {
        return;
    }

    const source = sourceInput.value.trim();

    if (!source) {

        showMessage(
            "Vui lòng nhập nguồn video."
        );

        return;
    }

    let sourceType;

    // So 0, 1, 2... la webcam
    if (/^\d+$/.test(source)) {

        sourceType = "camera";

    } else if (
        source.toLowerCase().startsWith("rtsp://")
    ) {

        showMessage(
            "Nguồn RTSP chưa được hỗ trợ."
        );

        return;

    } else {

        // Duong dan video tren laptop
        sourceType = "file";
    }

    isBusy = true;
    updateStatus(currentStatus);

    showMessage("Đang tạo phiên giám sát...");

    try {

        const session = await callApi(
            "/sessions",
            "POST",
            {
                source_type: sourceType,
                source: source
            }
        );

        const newSessionId = session.session_id;
        refreshSessionList();

        sessionInput.value = newSessionId;
        loadedSessionId = newSessionId;

        hideVideo();
        updateStatus(session.status);

        if (sourceType === "camera") {

            showMessage(
                `Đã tạo phiên webcam ${source}. ` +
                "Nhấn Bắt đầu để mở camera."
            );

        } else {

            showMessage(
                "Đã tạo phiên video. " +
                "Nhấn Bắt đầu để phát video."
            );
        }

    } catch (error) {

        showMessage(
            "Không thể tạo phiên: " + error.message
        );

    } finally {

        isBusy = false;
        updateStatus(currentStatus);
    }
}


// ==========================================
// 10. BAT DAU GIAM SAT
// ==========================================

async function startMonitoring() {

    const sessionId = getSessionId();

    if (
        !sessionId ||
        isBusy ||
        currentStatus !== "STOPPED"
    ) {
        return;
    }

    isBusy = true;
    updateStatus(currentStatus);

    showMessage("Đang bắt đầu giám sát...");

    try {

        const session = await callApi(
            `/sessions/${encodeURIComponent(sessionId)}/start`,
            "POST"
        );

        updateStatus(session.status);

        if (session.status === "RUNNING") {

            loadedSessionId = sessionId;
            showVideo(sessionId);
        }

        showMessage("Đã bắt đầu giám sát thành công!");

    } catch (error) {

        showMessage(
            "Không thể bắt đầu: " + error.message
        );

    } finally {

        isBusy = false;
        updateStatus(currentStatus);
    }
}


// ==========================================
// 11. DUNG GIAM SAT
// ==========================================

async function stopMonitoring() {

    const sessionId = getSessionId();

    if (
        !sessionId ||
        isBusy ||
        !["RUNNING", "ERROR"].includes(currentStatus)
    ) {
        return;
    }

    isBusy = true;
    updateStatus(currentStatus);

    showMessage("Đang dừng giám sát...");

    try {

        const session = await callApi(
            `/sessions/${encodeURIComponent(sessionId)}/stop`,
            "POST"
        );

        updateStatus(session.status);

        hideVideo();

        showMessage("Đã dừng giám sát thành công!");

    } catch (error) {

        showMessage(
            "Không thể dừng: " + error.message
        );

    } finally {

        isBusy = false;
        updateStatus(currentStatus);
    }
}


// ==========================================
// 12. VE BOUNDING BOX CUA AI
// ==========================================

function drawDetection(detection) {

    const box = detection.bbox;

    const color =
        AI_COLORS[detection.label] || "#22c55e";

    const x = box.x1;
    const y = box.y1;

    const width = box.x2 - box.x1;
    const height = box.y2 - box.y1;

    // Ve khung bao quanh doi tuong
    aiContext.strokeStyle = color;
    aiContext.lineWidth = 3;

    aiContext.strokeRect(
        x,
        y,
        width,
        height
    );

    const label =
        AI_LABELS[detection.label] ||
        detection.label;

    const confidence =
        (detection.confidence * 100).toFixed(1);

    const text = `${label} ${confidence}%`;

    const fontSize = Math.max(
        16,
        Math.round(aiCanvas.width / 45)
    );

    aiContext.font =
        `bold ${fontSize}px Arial`;

    const textWidth =
        aiContext.measureText(text).width + 12;

    // Tranh de nhan ra ngoai anh
    const labelY = Math.max(
        fontSize + 10,
        y
    );

    const labelX = Math.max(
        0,
        Math.min(
            x,
            aiCanvas.width - textWidth
        )
    );

    aiContext.fillStyle = color;

    aiContext.fillRect(
        labelX,
        labelY - fontSize - 8,
        textWidth,
        fontSize + 12
    );

    aiContext.fillStyle = "#ffffff";

    aiContext.fillText(
        text,
        labelX + 6,
        labelY
    );
}


// ==========================================
// 13. HIEN THI DANH SACH KET QUA AI
// ==========================================

function showAiDetections(detections) {

    aiDetectionList.replaceChildren();

    if (!detections.length) {

        aiDetectionList.textContent =
            "Không phát hiện đối tượng đạt ngưỡng.";

        return;
    }

    const heading = document.createElement("p");

    heading.textContent =
        `Đã phát hiện ${detections.length} đối tượng nghi vấn:`;

    aiDetectionList.appendChild(heading);

    const list = document.createElement("ul");

    for (const detection of detections) {

        const item = document.createElement("li");

        const label =
            AI_LABELS[detection.label] ||
            detection.label;

        const percent =
            (detection.confidence * 100).toFixed(2);

        item.textContent =
            `${label} - Confidence: ${percent}%`;

        list.appendChild(item);
    }

    aiDetectionList.appendChild(list);
}


// ==========================================
// 14. NHAN DIEN ANH QUA BACKEND
// ==========================================

async function detectImageFromWeb() {

    if (isDetecting) {
        return;
    }

    const file = aiImageInput.files[0];

    if (!file) {

        aiStatus.textContent =
            "Vui lòng chọn một ảnh trước.";

        return;
    }

    // Chi ho tro JPG va PNG
    if (!["image/jpeg", "image/png"].includes(file.type)) {

        aiStatus.textContent =
            "Chỉ hỗ trợ ảnh JPG hoặc PNG.";

        return;
    }

    // Dong bo voi gioi han API 10 MB
    if (file.size > 10 * 1024 * 1024) {

        aiStatus.textContent =
            "Ảnh vượt quá giới hạn 10 MB.";

        return;
    }

    isDetecting = true;
    aiDetectButton.disabled = true;

    aiStatus.textContent =
        "Đang gửi ảnh đến FastAPI và chạy YOLO11n...";

    aiResultJson.textContent = "Đang xử lý...";
    aiDetectionList.textContent = "";

    try {

        // Hien thi anh goc tren canvas
        const bitmap = await createImageBitmap(file);

        aiCanvas.width = bitmap.width;
        aiCanvas.height = bitmap.height;

        aiContext.clearRect(
            0,
            0,
            aiCanvas.width,
            aiCanvas.height
        );

        aiContext.drawImage(
            bitmap,
            0,
            0
        );

        bitmap.close();

        aiCanvas.hidden = false;

        // Gui du lieu anh binary den API
        // Khong dung FormData
        const response = await fetch(
            "/api/detection/image",
            {
                method: "POST",
                headers: {
                    "Content-Type": file.type
                },
                body: file,
                cache: "no-store"
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                `HTTP ${response.status}`
            );
        }

        // Ve bounding box theo toa do Backend
        for (const detection of data.detections) {
            drawDetection(detection);
        }

        // Hien thi danh sach doi tuong
        showAiDetections(data.detections);

        // Hien thi JSON de demo Backend
        aiResultJson.textContent =
            JSON.stringify(data, null, 2);

        if (data.has_weapon) {

            aiStatus.textContent =
                `Phát hiện ${data.detection_count} ` +
                "đối tượng nghi vấn.";

        } else {

            aiStatus.textContent =
                "Không có đối tượng đạt ngưỡng.";
        }

    } catch (error) {

        aiStatus.textContent =
            "Lỗi nhận diện: " + error.message;

        aiResultJson.textContent =
            String(error);

    } finally {

        isDetecting = false;
        aiDetectButton.disabled = false;
    }
}


// ==========================================
// 15. GAN SU KIEN CAC NUT
// ==========================================

// Tao phien
createSessionButton.addEventListener(
    "click",
    createSession
);

// Bat dau giam sat
startButton.addEventListener(
    "click",
    startMonitoring
);

// Dung giam sat
stopButton.addEventListener(
    "click",
    stopMonitoring
);

// Nhap ma phien
sessionInput.addEventListener(
    "change",
    loadSessionStatus
);

// Nhan dien anh bang AI
aiDetectButton.addEventListener(
    "click",
    detectImageFromWeb
);


// ==========================================
// 16. KHOI TAO TRANG
// ==========================================

// Hien thi trang thai phien
loadSessionStatus();

// Trang thai ban dau cua AI
aiStatus.textContent =
    "Chọn ảnh và nhấn Nhận diện ảnh để bắt đầu.";

// Keep the server's session state visible when a camera, AI or database fails.
const sessionList = document.getElementById("session-list");
async function refreshSessionList() {
    try {
        const rows = await callApi("/sessions?limit=50");
        sessionList.replaceChildren(new Option("Chọn phiên", ""));
        rows.forEach(row => sessionList.add(new Option(
            row.session_id.slice(0, 8) + " · " + row.status + " · " + row.source,
            row.session_id
        )));
        sessionList.value = loadedSessionId || "";
    } catch (error) {
        showMessage("Không tải được danh sách phiên: " + error.message);
    }
}
document.getElementById("session-refresh").addEventListener("click", refreshSessionList);
sessionList.addEventListener("change", () => {
    if (isBusy || currentStatus === "RUNNING") {
        sessionList.value = loadedSessionId || "";
        showMessage("Hãy dừng phiên hiện tại trước khi đổi phiên.");
        return;
    }
    sessionInput.value = sessionList.value;
    loadSessionStatus();
});
let pollingSession = false;
setInterval(async () => {
    if (isBusy || pollingSession || !loadedSessionId || document.visibilityState !== "visible") return;
    pollingSession = true;
    const id = loadedSessionId;
    try {
        const session = await callApi("/sessions/" + encodeURIComponent(id));
        if (isBusy || loadedSessionId !== id) return;
        if (session.status !== currentStatus) {
            updateStatus(session.status);
            if (session.status !== "RUNNING") {
                hideVideo();
                showMessage(session.status === "ERROR"
                    ? "Giám sát gặp lỗi. Kiểm tra nguồn video và kết nối, sau đó nhấn Đặt lại phiên lỗi."
                    : "Phiên giám sát đã dừng.");
            }
            refreshSessionList();
        }
    } catch (error) {
        showMessage("Không cập nhật được trạng thái phiên: " + error.message);
    } finally {
        pollingSession = false;
    }
}, 2000);
refreshSessionList();
