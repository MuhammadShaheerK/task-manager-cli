import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import date
from fastapi.testclient import TestClient
from api import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_api_crud_errors_and_restart(tmp_path):
    path = tmp_path / "tasks.txt"
    with TestClient(create_app(path)) as client:
        assert len(client.get("/tasks").json()["tasks"]) == 3
        added = client.post("/tasks", json={"name": "read, write"})
        assert added.status_code == 201
        number = added.json()["task"]["id"]
        assert client.put(f"/tasks/{number}/done").status_code == 200
        assert client.put(f"/tasks/{number}/done").status_code == 400
        assert client.post("/tasks", json={"name": " GYM "}).status_code == 400
        assert client.post("/tasks", json={"name": "  "}).status_code == 422
        assert client.get("/tasks/999").status_code == 404
        assert client.delete("/tasks/0").status_code == 404
        assert client.get("/progress").json()["completed"] == 1
    with TestClient(create_app(path)) as client:
        assert client.get(f"/tasks/{number}").json()["status"] is True
        assert client.delete(f"/tasks/{number}").status_code == 200
        assert client.get(f"/tasks/{number}").status_code == 404


def test_api_rolls_over_without_restart(tmp_path):
    day = [date(2026, 1, 1)]
    with TestClient(create_app(tmp_path / "tasks.txt", lambda: day[0])) as client:
        client.put("/tasks/1/done")
        day[0] = date(2026, 1, 2)
        assert client.get("/progress").json()["completed"] == 0


def test_cli_visible_output_and_error_exit(tmp_path):
    def run(*args):
        return subprocess.run([sys.executable, str(ROOT / "main.py"), "--file",
                               str(tmp_path / "tasks.txt"), *args],
                              cwd=tmp_path, capture_output=True, text=True)
    assert len(json.loads(run("list").stdout)) == 3
    assert json.loads(run("add", "read, write").stdout)["name"] == "read, write"
    assert json.loads(run("progress").stdout)["total"] == 4
    assert run("done", "999").returncode == 2


def test_import_does_not_create_runtime_files(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run([sys.executable, "-c", "import api"], cwd=tmp_path, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []
