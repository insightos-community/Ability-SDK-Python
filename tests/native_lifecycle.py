"""Real SDK IPC/heartbeat integration against a local fake framework.

Windows uses the actual compiled Ability launcher to exercise its venv child
chain. This verifies protocol behavior, not robot motion or safety evidence.
"""
import json
import os
from pathlib import Path
import queue
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request

states = queue.Queue()
identifier = "12345678-1234-1234-1234-123456789abc"

class Framework(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        assert self.path == "/api/cr/" + identifier
        value = {"metadata": {"name": "native-test"}, "spec": {"abilityName": "native-test", "version": "1.0.0"}}
        data = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        value = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert self.path == "/api/ability-heartbeat"
        assert value["id"] == identifier
        states.put(value)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()


def wait_state(expected):
    end = time.monotonic() + 15
    while time.monotonic() < end:
        try:
            value = states.get(timeout=0.5)
        except queue.Empty:
            continue
        if value["state"] == expected:
            return value
    raise AssertionError("Heartbeat state missing: " + expected)


framework = ThreadingHTTPServer(("127.0.0.1", 0), Framework)
thread = threading.Thread(target=framework.serve_forever, daemon=True)
thread.start()
try:
    with tempfile.TemporaryDirectory(prefix="Semantic SDK ") as folder:
        root = Path(folder) / "中文 path's with spaces"
        root.mkdir()
        (root / "main.py").write_text('''from ability_py import AbilityService, AbilityInterface
from pathlib import Path
import os
class Demo(AbilityInterface):
    def record(self, value):
        with (Path(os.environ["ABILITY_ROOT"])/"hooks.txt").open("a",encoding="utf-8") as out: out.write(value+"\\n")
    def on_start(self): self.record("start")
    def on_connect(self): self.record("connect")
    def on_disconnect(self): self.record("disconnect")
    def on_terminate(self): self.record("terminate")
    def get_ability_port(self): return 19001
AbilityService().run(Demo())
''', encoding="utf-8")
        args = [identifier, json.dumps({"port": framework.server_port, "note": "中文 JSON / quotes \\\""})]
        env = {**os.environ, "ABILITY_ROOT": str(root), "SEMANTIC_ABILITY_PYTHON": sys.executable, "PYTHONUTF8": "1", "NO_PROXY": "localhost,127.0.0.1"}
        if os.name == "nt":
            (root / "bin").mkdir()
            executable = root / "bin/ability.exe"
            shutil.copy2(Path(sys.argv[1]).resolve(), executable)
            command = [str(executable), *args]
        else:
            command = [sys.executable, str(root / "main.py"), *args]
        with (root / "process.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
            ipc = None
            try:
                standby = wait_state("Standby")
                ipc = standby["IPCPort"]
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                for operation, expected in [("connect", "Running"), ("disconnect", "Suspend"), ("terminate", "Terminated")]:
                    request = urllib.request.Request(f"http://127.0.0.1:{ipc}/api/lifecycle/{operation}", data=b"", method="POST")
                    with opener.open(request, timeout=5) as response:
                        assert response.status == 200
                    value = wait_state(expected)
                    if expected == "Running": assert value["abilityPort"] == 19001
                    if expected == "Suspend": assert value["abilityPort"] == 0
                assert (root / "hooks.txt").read_text().splitlines() == ["start", "connect", "disconnect", "terminate"]
            except Exception:
                print((root / "process.log").read_text(encoding="utf-8", errors="replace"))
                raise
            finally:
                # Test retirement after Terminated acknowledgment; no robot is connected.
                if process.poll() is None: process.terminate()
                process.wait(timeout=10)
        if ipc:
            for attempt in range(30):
                with socket.socket() as probe:
                    probe.settimeout(0.1)
                    if probe.connect_ex(("127.0.0.1", ipc)) != 0:
                        break
                time.sleep(0.1)
            else:
                raise AssertionError("SDK IPC remained available after launcher retirement")
finally:
    framework.shutdown()
    framework.server_close()
    thread.join()
print("PASS installed SDK: UUID/config, Standby/Running/Suspend/Terminated, native entry and IPC cleanup")
