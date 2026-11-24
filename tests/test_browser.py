"""Optional browser acceptance test using installed Edge and its DevTools protocol."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from urllib.request import urlopen

from websockets.sync.client import connect


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@unittest.skipUnless(os.getenv("UAV_TEST_BROWSER") == "1", "Pass --browser to run the Web acceptance test")
class BrowserAcceptanceTests(unittest.TestCase):
    def test_web_session_monitor_evidence_review_and_filters(self):
        if os.getenv("UAV_TEST_ISOLATED") != "1":
            self.fail("Refusing to run outside isolated test database")
        edge = Path(os.environ["UAV_TEST_EDGE"])
        run_dir = Path(os.environ["UAV_TEST_RUN_DIR"])
        root = Path(__file__).resolve().parents[1]
        http_port, debug_port = free_port(), free_port()
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        environment = {**os.environ, "UAV_TEST_HTTP_PORT": str(http_port)}
        server = browser = connection = None
        output = (run_dir / "browser.log").open("w", encoding="utf-8")
        try:
            server = subprocess.Popen(
                [sys.executable, "-m", "tests.browser_server"], cwd=root, env=environment,
                stdout=output, stderr=subprocess.STDOUT, creationflags=flags,
            )
            url = f"http://127.0.0.1:{http_port}"
            deadline = time.monotonic() + 40
            while True:
                try:
                    with urlopen(url + "/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    if time.monotonic() >= deadline or server.poll() is not None:
                        self.fail("Browser test server did not start; see browser.log")
                    time.sleep(0.2)
            browser = subprocess.Popen(
                [str(edge), "--headless=new", "--disable-gpu", "--no-first-run",
                 "--no-default-browser-check", "--disable-extensions",
                 f"--user-data-dir={run_dir / 'edge-profile'}",
                 f"--remote-debugging-port={debug_port}", "about:blank"],
                stdout=output, stderr=subprocess.STDOUT, creationflags=flags,
            )
            debug_url = f"http://127.0.0.1:{debug_port}/json"
            deadline = time.monotonic() + 20
            while True:
                try:
                    with urlopen(debug_url, timeout=1) as response:
                        tabs = json.load(response)
                    tab = next(item for item in tabs if item.get("type") == "page")
                    break
                except (OSError, StopIteration):
                    if time.monotonic() >= deadline:
                        self.fail("Headless Edge did not start; see browser.log")
                    time.sleep(0.2)
            connection = connect(tab["webSocketDebuggerUrl"], open_timeout=5, max_size=8 * 1024 * 1024)
            counter = 0
            errors = []

            def command(method, params=None):
                nonlocal counter
                counter += 1
                target = counter
                connection.send(json.dumps({"id": target, "method": method, "params": params or {}}))
                while True:
                    message = json.loads(connection.recv(timeout=20))
                    if message.get("method") == "Runtime.exceptionThrown":
                        errors.append(message["params"])
                    if message.get("id") == target:
                        if "error" in message:
                            self.fail(str(message["error"]))
                        return message.get("result", {})

            def evaluate(expression):
                result = command("Runtime.evaluate", {"expression": expression, "returnByValue": True})
                if "exceptionDetails" in result:
                    self.fail(str(result["exceptionDetails"]))
                return result.get("result", {}).get("value")

            def wait_for(expression):
                deadline = time.monotonic() + 15
                while not evaluate(expression):
                    if time.monotonic() >= deadline:
                        snapshot = evaluate("document.body.innerText")
                        (run_dir / "browser-page.txt").write_text(str(snapshot), encoding="utf-8")
                        self.fail("Browser wait timed out: " + expression)
                    time.sleep(0.1)

            command("Runtime.enable")
            command("Page.enable")
            command("Page.navigate", {"url": url + "/web/"})
            wait_for("document.getElementById('create-session-btn') !== null")
            wait_for("document.getElementById('history-status').textContent.includes('phát hiện')")
            evaluate("document.getElementById('video-source').value='data/videos/test.mp4';"
                     "document.getElementById('create-session-btn').click()")
            wait_for("document.getElementById('status-text').textContent === 'STOPPED'")
            evaluate("document.getElementById('start-btn').click()")
            wait_for("document.getElementById('status-text').textContent === 'RUNNING'")
            wait_for("document.querySelector('#history-body .history-action-image') !== null")
            evaluate("document.getElementById('stop-btn').click()")
            wait_for("document.getElementById('status-text').textContent === 'STOPPED'")
            self.assertTrue(evaluate("document.getElementById('video-stream').hidden"))
            session_id = evaluate("document.getElementById('session-id').value")
            evaluate("document.getElementById('history-session').value=" + json.dumps(session_id) + ";"
                     "document.getElementById('history-label').value='stick';"
                     "document.getElementById('history-filters').requestSubmit()")
            wait_for("document.getElementById('history-status').textContent === 'Tổng 0 phát hiện phù hợp.'")
            evaluate("document.getElementById('history-label').value='knife';"
                     "document.getElementById('history-filters').requestSubmit()")
            wait_for("document.querySelector('#history-body .history-action-image') !== null")
            evaluate("document.querySelector('#history-body .history-action-image').click()")
            wait_for("!document.getElementById('evidence-image').hidden")
            self.assertTrue(evaluate("document.getElementById('evidence-image').naturalWidth > 0"))
            evaluate("document.getElementById('evidence-close').click();"
                     "document.querySelector('#history-body .history-action-confirm').click()")
            wait_for("document.querySelector('#history-body .history-action-reset') !== null")
            evaluate("document.getElementById('history-alert-status').value='CONFIRMED';"
                     "document.getElementById('history-filters').requestSubmit()")
            wait_for("document.getElementById('history-status').textContent === 'Tổng 1 phát hiện phù hợp.'")
            self.assertEqual(errors, [], "JavaScript runtime errors")
            command("Browser.close")
            browser.wait(timeout=10)
        finally:
            if connection:
                connection.close()
            for process in (browser, server):
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            output.close()
