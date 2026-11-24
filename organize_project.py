
# ==========================================
# UAV WEAPON DETECTION - ORGANIZE PROJECT
# Sap xep script cu, khong xoa du lieu
# ==========================================

from pathlib import Path
import argparse
import ast
import json
import shutil
from datetime import datetime


# ==========================================
# 1. THU MUC DU AN
# ==========================================

ROOT = Path(__file__).resolve().parent

ARCHIVE = ROOT / "project_archive"

MANIFEST = ARCHIVE / "organization_manifest.json"


# ==========================================
# 2. PHAN LOAI SCRIPT
# ==========================================

DATABASE_FILES = {
    "create_detections_table.py",
    "add_snapshot_column.py"
}

AI_TRAIN_PREFIXES = (
    "train_",
    "finetune_",
    "resume_",
    "prepare_",
    "build_",
    "collect_",
    "label_",
    "relabel_",
    "fix_",
    "plan_"
)

AI_EVAL_PREFIXES = (
    "evaluate_",
    "compare_",
    "check_",
    "verify_",
    "review_",
    "inspect_"
)


def classify_file(filename):

    if filename in DATABASE_FILES:
        return "database_setup"

    if filename.startswith("test_"):
        return "tests"

    if filename.startswith(AI_TRAIN_PREFIXES):
        return "ai_training"

    if filename.startswith(AI_EVAL_PREFIXES):
        return "ai_evaluation"

    if filename.startswith("generate_"):
        return "utilities"

    return None


# ==========================================
# 3. KIEM TRA MODULE BACKEND DANG IMPORT
# ==========================================

def get_backend_imports():

    imported = set()

    backend_dir = ROOT / "backend"

    for path in backend_dir.rglob("*.py"):

        try:
            source = path.read_text(
                encoding="utf-8-sig"
            )

            tree = ast.parse(source)

        except (OSError, SyntaxError, UnicodeError):
            continue

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:
                    imported.add(
                        alias.name.split(".")[0]
                    )

            elif isinstance(node, ast.ImportFrom):

                if node.module:
                    imported.add(
                        node.module.split(".")[0]
                    )

    return imported


# ==========================================
# 4. LAP DANH SACH DI CHUYEN
# ==========================================

def create_plan():

    backend_imports = get_backend_imports()

    plan = []
    skipped = []

    # Chi quet file .py o thu muc GOC
    # Khong quet backend, frontend, data, models
    for path in sorted(ROOT.glob("*.py")):

        if path.name == Path(__file__).name:
            continue

        category = classify_file(path.name)

        if category is None:
            skipped.append(
                (path.name, "Chua phan loai")
            )
            continue

        # Khong di chuyen module Backend dang import
        if path.stem in backend_imports:
            skipped.append(
                (path.name, "Backend dang import")
            )
            continue

        destination = ARCHIVE / category / path.name

        plan.append({
            "source": str(path.relative_to(ROOT)),
            "destination": str(
                destination.relative_to(ROOT)
            )
        })

    return plan, skipped


# ==========================================
# 5. HIEN THI KE HOACH
# ==========================================

def show_plan(plan, skipped):

    print("\n===== DU KIEN SAP XEP =====")

    for item in plan:

        print(
            item["source"],
            "=>",
            item["destination"]
        )

    print("\nTONG FILE SE DI CHUYEN:", len(plan))

    if skipped:

        print("\n===== FILE GIU NGUYEN =====")

        for filename, reason in skipped:
            print(filename, "|", reason)

    print("\nKHONG DI CHUYEN:")
    print("- backend/")
    print("- frontend/")
    print("- models/")
    print("- data/")
    print("- runtime/")
    print("- .venv/")
    print("- PostgreSQL")

    print("\nKHONG XOA BAT KY FILE NAO.")


# ==========================================
# 6. THUC HIEN DI CHUYEN
# ==========================================

def apply_plan(plan):

    if MANIFEST.exists():

        print(
            "Da co lich su sap xep."
        )

        print(
            "Hay dung --undo neu muon "
            "khoi phuc truoc khi sap xep lai."
        )

        return

    if not plan:

        print("Khong co file can di chuyen.")
        return

    # Kiem tra trung ten truoc khi di chuyen
    for item in plan:

        source = ROOT / item["source"]
        destination = ROOT / item["destination"]

        if not source.is_file():
            raise RuntimeError(
                f"Khong tim thay: {source}"
            )

        if destination.exists():
            raise RuntimeError(
                f"File dich da ton tai: {destination}"
            )

    ARCHIVE.mkdir(
        parents=True,
        exist_ok=True
    )

    # Luu danh sach de co the hoan tac
    manifest_data = {
        "created_at": datetime.now().isoformat(),
        "moves": plan
    }

    MANIFEST.write_text(
        json.dumps(
            manifest_data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    # Chi di chuyen file, khong xoa
    for item in plan:

        source = ROOT / item["source"]
        destination = ROOT / item["destination"]

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.move(
            str(source),
            str(destination)
        )

        print("DA CHUYEN:", source.name)

    print("\n===== THANH CONG =====")
    print("Da sap xep:", len(plan), "file")
    print("Thu muc:", ARCHIVE)
    print("Khong xoa du lieu.")
    print("Co the khoi phuc bang --undo")


# ==========================================
# 7. HOAN TAC NEU CAN
# ==========================================

def undo_plan():

    if not MANIFEST.exists():

        print("Khong co lich su de hoan tac.")
        return

    data = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    restored = 0
    errors = 0

    for item in reversed(data["moves"]):

        source = ROOT / item["destination"]
        destination = ROOT / item["source"]

        if destination.exists():

            # Neu file goc da co thi khong ghi de
            if source.exists():

                print(
                    "BO QUA - FILE GOC DA CO:",
                    destination
                )

                errors += 1

            continue

        if not source.exists():

            print(
                "KHONG TIM THAY FILE LUU TRU:",
                source
            )

            errors += 1
            continue

        shutil.move(
            str(source),
            str(destination)
        )

        restored += 1

        print("DA KHOI PHUC:", destination.name)

    if errors == 0:

        MANIFEST.unlink()

        print("\nHOAN TAC THANH CONG!")

    else:

        print(
            "\nCo file chua khoi phuc."
        )

        print(
            "Giu nguyen manifest de kiem tra."
        )

    print("So file da khoi phuc:", restored)


# ==========================================
# 8. CHUONG TRINH CHINH
# ==========================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Thuc hien sap xep"
    )

    parser.add_argument(
        "--undo",
        action="store_true",
        help="Khoi phuc file ve thu muc goc"
    )

    args = parser.parse_args()

    if args.apply and args.undo:
        parser.error(
            "Chi chon --apply hoac --undo"
        )

    print("PROJECT:", ROOT)

    if args.undo:
        undo_plan()
        return

    plan, skipped = create_plan()

    show_plan(plan, skipped)

    if args.apply:
        apply_plan(plan)

    else:
        print("\nDAY MOI LA XEM TRUOC.")
        print(
            "Muon thuc hien, chay:"
        )
        print(
            "python organize_project.py --apply"
        )


if __name__ == "__main__":
    main()
