
# ==========================================
# KIEM TRA DUNG LUONG DU AN
# KHONG XOA HOAC DI CHUYEN DU LIEU
# ==========================================

import os
from pathlib import Path


# Thu muc goc UAV_Weapon_Detection
ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    "data",
    "models",
    "project_archive",
    "runtime"
]

errors = []


# ==========================================
# 1. XU LY DUONG DAN DAI TREN WINDOWS
# ==========================================

def long_path(path):

    path = Path(path).resolve()

    if os.name == "nt":
        return "\\\\?\\" + str(path)

    return str(path)


# ==========================================
# 2. TINH DUNG LUONG THU MUC
# ==========================================

def folder_size(folder):

    total = 0
    files_count = 0

    def handle_error(error):
        errors.append(str(error))

    for current, dirs, files in os.walk(
        long_path(folder),
        onerror=handle_error,
        followlinks=False
    ):

        for filename in files:

            file_path = os.path.join(
                current,
                filename
            )

            try:

                file_info = os.stat(
                    file_path,
                    follow_symlinks=False
                )

                total += file_info.st_size
                files_count += 1

            except OSError as error:

                errors.append(str(error))

    return total, files_count


# ==========================================
# 3. DINH DANG DUNG LUONG
# ==========================================

def format_size(size):

    gb = size / (1024 ** 3)
    mb = size / (1024 ** 2)

    if gb >= 1:
        return f"{gb:.2f} GB"

    if mb >= 1:
        return f"{mb:.2f} MB"

    return f"{size / 1024:.1f} KB"


# ==========================================
# 4. KIEM KE CAC THU MUC
# ==========================================

def main():

    print("===== KIEM KE DUNG LUONG =====")
    print("PROJECT:", ROOT)

    results = []

    for target_name in TARGETS:

        target = ROOT / target_name

        if not target.is_dir():
            continue

        print(
            f"\n===== {target_name.upper()} ====="
        )

        group_total = 0

        for item in sorted(target.iterdir()):

            if item.is_dir():

                size, count = folder_size(item)

            elif item.is_file():

                try:
                    size = item.stat().st_size
                    count = 1
                except OSError as error:
                    errors.append(str(error))
                    continue

            else:
                continue

            group_total += size

            results.append(
                (size, target_name, item.name)
            )

            print(
                f"{item.name:<38} "
                f"{format_size(size):>12} "
                f"| {count} files"
            )

        print(
            "TONG:",
            format_size(group_total)
        )

    # ======================================
    # 5. CAC THU MUC CHIEM NHIEU NHAT
    # ======================================

    print("\n===== TOP 10 CHIEM DUNG LUONG =====")

    for size, parent, name in sorted(
        results,
        reverse=True
    )[:10]:

        print(
            f"{parent}/{name}: "
            f"{format_size(size)}"
        )

    # ======================================
    # 6. BAO CAO LOI TRUY CAP
    # ======================================

    print("\n===== KIEM TRA LOI =====")

    print(
        "So loi truy cap:",
        len(errors)
    )

    for error in errors[:5]:
        print(error)

    print("\nHOAN THANH KIEM KE!")
    print("KHONG XOA BAT KY DU LIEU NAO.")


if __name__ == "__main__":
    main()
