"""Run backend tests against a fresh, temporary PostgreSQL cluster (no user DB access)."""
import argparse
from datetime import datetime
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parent


def find_pg_bin(value):
    candidates = [Path(value)] if value else []
    executable = shutil.which("initdb")
    if executable:
        candidates.append(Path(executable).parent)
    for base in (Path("D:/PostgreSQL"), Path("C:/Program Files/PostgreSQL")):
        if base.is_dir():
            candidates.extend(sorted(base.glob("*/bin"), reverse=True))
    for candidate in candidates:
        if (candidate / ("initdb.exe" if os.name == "nt" else "initdb")).is_file():
            return candidate
    raise SystemExit("PostgreSQL binaries not found. Pass --pg-bin PATH_TO_POSTGRES_BIN.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", help="Directory containing initdb and pg_ctl")
    parser.add_argument("--browser", action="store_true", help="Also run headless Edge Web acceptance test")
    args = parser.parse_args()
    if args.browser:
        edge_candidates = [Path(os.getenv("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
                           Path(os.getenv("PROGRAMFILES", "C:/Program Files")) / "Microsoft/Edge/Application/msedge.exe"]
        edge = next((p for p in edge_candidates if p.is_file()), None)
        if edge is None:
            raise SystemExit("Microsoft Edge not found for --browser")
        os.environ.update(UAV_TEST_BROWSER="1", UAV_TEST_EDGE=str(edge))
    pg_bin = find_pg_bin(args.pg_bin)
    run_dir = ROOT / "runtime" / "test-runs" / (
        datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
    )
    run_dir.mkdir(parents=True)
    cluster = run_dir / "pgdata"
    log = run_dir / "postgres.log"
    suffix = ".exe" if os.name == "nt" else ""
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def run(binary, *arguments):
        # A real file avoids inherited pipe handles keeping communicate() blocked
        # after pg_ctl starts a background server on Windows.
        command_log = run_dir / f"{binary}.log"
        with command_log.open("w", encoding="utf-8") as output:
            result = subprocess.run(
                [str(pg_bin / (binary + suffix)), *map(str, arguments)],
                cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                creationflags=flags, timeout=90,
            )
        if result.returncode:
            print(command_log.read_text(encoding="utf-8", errors="replace"), file=sys.stderr)
            raise RuntimeError(f"{binary} failed (exit {result.returncode})")
        return result

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    started = False
    try:
        run("initdb", "-D", cluster, "-U", "uav_test",
            "--auth-local=trust", "--auth-host=trust", "--encoding=UTF8", "--locale=C")
        run("pg_ctl", "-D", cluster, "-l", log, "-w", "start",
            "-o", f"-h 127.0.0.1 -p {port}")
        started = True
        os.environ.update(
            UAV_PG_HOST="127.0.0.1", UAV_PG_PORT=str(port),
            UAV_PG_DATABASE="uav_backend_test", UAV_PG_USER="uav_test",
            UAV_PG_PASSWORD="isolated-test-only", UAV_TEST_ISOLATED="1",
            UAV_TEST_RUN_DIR=str(run_dir),
        )
        import psycopg
        with psycopg.connect(host="127.0.0.1", port=port, user="uav_test",
                            dbname="postgres", autocommit=True) as conn:
            conn.execute("CREATE DATABASE uav_backend_test")
        from backend.database.init_pg import init_database
        init_database()
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
        with (run_dir / "results.txt").open("w", encoding="utf-8") as report:
            class Tee:
                def write(self, text):
                    sys.stderr.write(text)
                    report.write(text)
                def flush(self):
                    sys.stderr.flush()
                    report.flush()
            result = unittest.TextTestRunner(stream=Tee(), verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    finally:
        if started and (cluster / "postmaster.pid").exists():
            run("pg_ctl", "-D", cluster, "-w", "stop", "-m", "fast")
        # Only remove the generated cluster after PostgreSQL has stopped.
        resolved = cluster.resolve()
        intended = (ROOT / "runtime" / "test-runs").resolve()
        if resolved.is_relative_to(intended) and resolved.name == "pgdata" and resolved.exists():
            shutil.rmtree(resolved)
        print(f"Test logs: {run_dir}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
