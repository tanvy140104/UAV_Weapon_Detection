
import os
import csv
from pathlib import Path
from datetime import datetime

# ==========================================
# 1. CAU HINH THU MUC TREN O D
# ==========================================

BASE = Path(__file__).resolve().parents[2]
RUNTIME = BASE / "runtime"

for name in ["ultralytics", "matplotlib", "torch", "temp"]:
    (RUNTIME / name).mkdir(parents=True, exist_ok=True)

os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["MPLCONFIGDIR"] = str(RUNTIME / "matplotlib")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")
os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["TMP"] = str(RUNTIME / "temp")

import cv2
import numpy as np
import torch
from ultralytics import YOLO


# ==========================================
# 2. DUONG DAN HAI MODEL
# ==========================================

OLD_MODEL = (
    BASE / "models" / "trained"
    / "gks_yolo11n_30e"
    / "weights" / "best.pt"
)

NEW_MODEL = (
    BASE / "models" / "trained"
    / "gks_field_ft_10e"
    / "weights" / "best.pt"
)

# Bo 30 anh test doc lap
DATA = BASE / "data" / "field_eval_holdout_v1"

KNIFE_DIR = DATA / "knife"
NORMAL_DIR = DATA / "normal"

# ==========================================
# 3. THU MUC LUU KET QUA TREN O D
# ==========================================

# Sua loi WindowsPath + str
# Them microseconds de tranh trung ten
RUN_NAME = (
    "holdout_ab_"
    + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
)

OUTPUT = (
    BASE / "models" / "evaluation" / RUN_NAME
)

IMAGES_OUT = OUTPUT / "images"

# Nguong nhan dien cua hai model
CONF = 0.25
IMAGE_SIZE = 640

CLASS_NAMES = {
    0: "knife",
    1: "stick",
    2: "gun"
}


# ==========================================
# 4. HAM LAY DANH SACH ANH
# ==========================================

def get_images(folder):

    if not folder.is_dir():
        raise FileNotFoundError(
            f"Khong tim thay thu muc: {folder}"
        )

    return sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
    )


knife_images = get_images(KNIFE_DIR)
normal_images = get_images(NORMAL_DIR)

print("\n===== KIEM TRA DU LIEU =====")
print("Knife:", len(knife_images))
print("Normal:", len(normal_images))

if len(knife_images) != 15:
    raise RuntimeError("Can dung 15 anh knife!")

if len(normal_images) != 15:
    raise RuntimeError("Can dung 15 anh normal!")

# Kiem tra hai model da ton tai
for model_path in [OLD_MODEL, NEW_MODEL]:

    if not model_path.is_file():
        raise FileNotFoundError(model_path)

# Kiem tra GPU
if not torch.cuda.is_available():
    raise RuntimeError(
        "Khong tim thay GPU CUDA!"
    )

print("GPU:", torch.cuda.get_device_name(0))

# Tao thu muc sau khi kiem tra thanh cong
IMAGES_OUT.mkdir(parents=True, exist_ok=False)

print("Output:", OUTPUT)


# ==========================================
# 5. NAP HAI MODEL
# ==========================================

print("\nDang nap model goc...")
old_model = YOLO(str(OLD_MODEL))

print("Dang nap model fine-tune...")
new_model = YOLO(str(NEW_MODEL))


# ==========================================
# 6. HAM NHAN DIEN
# ==========================================

def predict(model, frame):

    # Hai model cung dung mot frame
    # Va cung nguong confidence 0.25
    result = model.predict(
        source=frame,
        imgsz=IMAGE_SIZE,
        conf=CONF,
        device=0,
        verbose=False
    )[0]

    detections = []

    for box in result.boxes:

        cls_id = int(box.cls[0].item())
        score = float(box.conf[0].item())

        detections.append({
            "class_id": cls_id,
            "class_name": CLASS_NAMES.get(
                cls_id, str(cls_id)
            ),
            "confidence": score
        })

    return result, detections


# ==========================================
# 7. HAM HIEN THI NHAN DU DOAN
# ==========================================

def format_detections(detections):

    if not detections:
        return "none"

    return "; ".join(
        f"{d['class_name']}:{d['confidence']:.2f}"
        for d in detections
    )


# ==========================================
# 8. DANH GIA THEO TUNG ANH
# ==========================================

def evaluate_prediction(detections, group):

    # Co it nhat mot du doan knife
    detected_knife = any(
        d["class_id"] == 0
        for d in detections
    )

    # Co du doan stick hoac gun
    detected_wrong_class = any(
        d["class_id"] in [1, 2]
        for d in detections
    )

    # Co bat ky du doan vu khi nao
    any_detection = len(detections) > 0

    if group == "knife":

        # Anh co dao:
        # Dung neu co it nhat mot knife
        correct = detected_knife

        # Bo sot neu khong du doan knife
        missed = not detected_knife

        false_alarm = False
        wrong_class = detected_wrong_class

    else:

        # Anh normal:
        # Dung neu khong du doan vu khi
        correct = not any_detection

        missed = False
        false_alarm = any_detection
        wrong_class = False

    return {
        "correct": int(correct),
        "missed": int(missed),
        "false_alarm": int(false_alarm),
        "wrong_class": int(wrong_class)
    }


# ==========================================
# 9. CHAY TEST TREN 30 ANH
# ==========================================

all_images = (
    [("knife", p) for p in knife_images]
    + [("normal", p) for p in normal_images]
)

rows = []

print("\n===== BAT DAU DANH GIA =====")

for index, (group, image_path) in enumerate(
    all_images, start=1
):

    # Doc anh goc
    frame = cv2.imread(str(image_path))

    if frame is None:
        raise RuntimeError(
            f"Khong doc duoc anh: {image_path}"
        )

    # Model goc du doan
    old_result, old_det = predict(
        old_model, frame
    )

    # Model fine-tune du doan
    new_result, new_det = predict(
        new_model, frame
    )

    # Danh gia ket qua
    old_eval = evaluate_prediction(
        old_det, group
    )

    new_eval = evaluate_prediction(
        new_det, group
    )

    # Luu thong tin tung anh
    rows.append({
        "image": image_path.name,
        "group": group,

        "old_prediction": format_detections(old_det),
        "old_correct": old_eval["correct"],
        "old_missed": old_eval["missed"],
        "old_false_alarm": old_eval["false_alarm"],
        "old_wrong_class": old_eval["wrong_class"],

        "new_prediction": format_detections(new_det),
        "new_correct": new_eval["correct"],
        "new_missed": new_eval["missed"],
        "new_false_alarm": new_eval["false_alarm"],
        "new_wrong_class": new_eval["wrong_class"]
    })

    # ======================================
    # 10. TAO ANH SO SANH
    # ======================================

    old_view = cv2.resize(
        old_result.plot(),
        (640, 480)
    )

    new_view = cv2.resize(
        new_result.plot(),
        (640, 480)
    )

    # Ten model ben trai
    cv2.putText(
        old_view,
        "MODEL GOC - 30 EPOCH",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 255),
        2
    )

    # Ten model ben phai
    cv2.putText(
        new_view,
        "FINE-TUNE - 10 EPOCH",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 255),
        2
    )

    # Ghep hai anh canh nhau
    combined = np.hstack(
        [old_view, new_view]
    )

    # Moi anh co ten rieng
    save_path = (
        IMAGES_OUT
        / f"{index:02d}_{group}_{image_path.stem}.jpg"
    )

    saved = cv2.imwrite(
        str(save_path),
        combined
    )

    if not saved:
        raise RuntimeError(
            f"Khong luu duoc anh: {save_path}"
        )

    print(
        f"[{index:02d}/30] {group.upper()} | "
        f"OLD: {format_detections(old_det)} | "
        f"NEW: {format_detections(new_det)}"
    )


# ==========================================
# 11. LUU BANG KET QUA CSV
# ==========================================

CSV_PATH = OUTPUT / "comparison.csv"

with CSV_PATH.open(
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=list(rows[0].keys())
    )

    writer.writeheader()
    writer.writerows(rows)


# ==========================================
# 12. TINH SO LIEU HAI MODEL
# ==========================================

def calculate(prefix):

    knife_rows = [
        row for row in rows
        if row["group"] == "knife"
    ]

    normal_rows = [
        row for row in rows
        if row["group"] == "normal"
    ]

    # So anh dao nhan dien dung
    detected = sum(
        row[f"{prefix}_correct"]
        for row in knife_rows
    )

    # So anh dao bi bo sot
    missed = sum(
        row[f"{prefix}_missed"]
        for row in knife_rows
    )

    # So anh dao co du doan stick/gun
    wrong_class = sum(
        row[f"{prefix}_wrong_class"]
        for row in knife_rows
    )

    # So anh normal bi canh bao nham
    false_alarm = sum(
        row[f"{prefix}_false_alarm"]
        for row in normal_rows
    )

    # So anh normal duoc nhan dien dung
    correct_normal = (
        len(normal_rows) - false_alarm
    )

    return {
        "detected": detected,
        "missed": missed,
        "wrong_class": wrong_class,
        "false_alarm": false_alarm,
        "correct_normal": correct_normal
    }


old = calculate("old")
new = calculate("new")


# ==========================================
# 13. TINH TY LE %
# ==========================================

old_recall = old["detected"] / 15 * 100
new_recall = new["detected"] / 15 * 100

old_normal = old["correct_normal"] / 15 * 100
new_normal = new["correct_normal"] / 15 * 100


# ==========================================
# 14. TONG HOP KET QUA
# ==========================================

summary = f"""
===== KET QUA HOLDOUT TEST =====

Tong so anh: 30
Anh dao: 15
Anh normal: 15
Nguong confidence: {CONF}

                         MODEL GOC   FINE-TUNE
Phat hien dao:           {old['detected']:>3}/15       {new['detected']:>3}/15
Bo sot dao:              {old['missed']:>3}/15       {new['missed']:>3}/15
Co du doan stick/gun:    {old['wrong_class']:>3}/15       {new['wrong_class']:>3}/15
Canh bao nham normal:    {old['false_alarm']:>3}/15       {new['false_alarm']:>3}/15
Normal dung:             {old['correct_normal']:>3}/15       {new['correct_normal']:>3}/15

Ty le phat hien dao:
Model goc:   {old_recall:.2f}%
Fine-tune:   {new_recall:.2f}%

Ty le anh normal khong bi canh bao:
Model goc:   {old_normal:.2f}%
Fine-tune:   {new_normal:.2f}%

GHI CHU:
- Danh gia theo tung anh, khong phai tung vat the.
- Anh dao duoc tinh dung neu co du doan knife.
- Khong kiem tra bbox co trung dao hay khong.
- Co du doan stick/gun la chi so phu.
- Anh normal bi canh bao nham neu co du doan
  knife, stick hoac gun.
- Bo 30 anh nay khong duoc dua vao Train.
- Ket qua khong thay the mAP object detection.
- Can xem anh de kiem tra cac phat hien sai.
"""

print(summary)


# ==========================================
# 15. LUU BAO CAO TXT
# ==========================================

SUMMARY_PATH = OUTPUT / "summary.txt"

SUMMARY_PATH.write_text(
    summary,
    encoding="utf-8"
)

print("===== DA LUU KET QUA =====")
print("CSV:", CSV_PATH)
print("Bao cao:", SUMMARY_PATH)
print("Anh so sanh:", IMAGES_OUT)

print("\nDANH GIA 30 ANH HOAN THANH!")
