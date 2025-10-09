import json
import uuid


def create_minimal_workflow_payload(name: str):
    node_id = f"node_{uuid.uuid4().hex[:6]}"
    return {
        "name": name,
        "description": "Test workflow",
        "nodes": [
            {"id": node_id, "type": "symbol", "x": 100, "y": 100}
        ],
        "connections": [],
        "properties": {node_id: {"ticker": "VN30", "exchange": "HOSE"}},
        "metadata": {"created": "test"}
    }


def test_save_and_load_workflow(client):
    payload = create_minimal_workflow_payload("pytest-wf-save-load")
    resp = client.post("/api/workflow/save", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    wf_id = data.get("workflow_id")
    assert wf_id

    # Load
    resp = client.get(f"/api/workflow/load/{wf_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    assert data.get("workflow", {}).get("id") == wf_id


def test_execute_status_runs_flow(client):
    # Save new workflow
    payload = create_minimal_workflow_payload("pytest-wf-exec")
    resp = client.post("/api/workflow/save", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    wf_id = resp.get_json()["workflow_id"]

    # Initially status should be idle
    resp = client.get(f"/api/workflow/status/{wf_id}")
    assert resp.status_code == 200
    assert resp.get_json().get("status") == "idle"

    # Execute
    resp = client.post(f"/api/workflow/execute/{wf_id}")
    assert resp.status_code == 200
    exec_data = resp.get_json()
    assert exec_data.get("success") is True
    run_id = exec_data.get("run_id")
    assert run_id

    # Status should now be success or running depending on speed
    resp = client.get(f"/api/workflow/status/{wf_id}")
    assert resp.status_code == 200
    status_data = resp.get_json()
    assert status_data.get("status") in ("running", "success", "error")

    # Runs list should have at least one item
    resp = client.get(f"/api/workflow/runs/{wf_id}")
    assert resp.status_code == 200
    runs = resp.get_json().get("runs", [])
    assert isinstance(runs, list)
    assert any(r.get("run_id") == run_id for r in runs)

    # Stop should return 404 if not running, but OK if running
    resp = client.post(f"/api/workflow/stop/{wf_id}")
    # Accept either 200 or 404 depending on current status
    assert resp.status_code in (200, 404)

    # Restart should create a new run
    resp = client.post(f"/api/workflow/restart/{wf_id}")
    assert resp.status_code == 200
    re_data = resp.get_json()
    assert re_data.get("success") is True
    assert re_data.get("run_id")


