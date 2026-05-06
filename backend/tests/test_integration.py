import time

BASE_URL = "http://127.0.0.1:8010"

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_register_and_login(client):
    ts = int(time.time())
    email = f"test_reg_{ts}@example.com"
    resp_reg = client.post("/api/auth/register", json={"email": email, "password": "strongpassword123"})
    assert resp_reg.status_code == 201
    resp_login = client.post("/api/auth/login", json={"email": email, "password": "strongpassword123"})
    assert resp_login.status_code == 200
    assert "access_token" in resp_login.json()

def test_download_flow(client):
    ts = int(time.time())
    email = f"test_flow_{ts}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "strongpassword123"})
    resp_login = client.post("/api/auth/login", json={"email": email, "password": "strongpassword123"})
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/download", json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "int_test", "height": 720}, headers=headers)
    assert resp.status_code == 201
    task_id = resp.json()["task_id"]

    for _ in range(30):
        st = client.get(f"/api/status/{task_id}", headers=headers).json()
        if st["status"] in ("ready", "error"):
            break
        time.sleep(2)
    assert st["status"] == "ready"

def test_quality_limit(client):
    ts = int(time.time())
    email = f"test_qual_{ts}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "strongpassword123"})
    resp_login = client.post("/api/auth/login", json={"email": email, "password": "strongpassword123"})
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/download", json={"video_url": "https://example.com", "title": "q_test", "height": 1080}, headers=headers)
    assert resp.status_code == 402
    assert resp.json()["detail"]["code"] == "QUALITY_LOCKED"

def test_download_file(client):
    ts = int(time.time())
    email = f"test_file_{ts}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "strongpassword123"})
    resp_login = client.post("/api/auth/login", json={"email": email, "password": "strongpassword123"})
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp_create = client.post("/api/download", json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "file_test", "height": 720}, headers=headers)
    assert resp_create.status_code == 201
    task_id = resp_create.json()["task_id"]

    for _ in range(30):
        st = client.get(f"/api/status/{task_id}", headers=headers).json()
        if st["status"] in ("ready", "error"):
            break
        time.sleep(2)
    assert st["status"] == "ready"

    resp_file = client.get(f"/api/file/{task_id}", headers=headers)
    assert resp_file.status_code == 200
    assert "video" in resp_file.headers.get("content-type", "")
    assert len(resp_file.content) > 1000
    assert resp_file.headers.get("content-disposition", "").startswith("attachment")

def test_history(client):
    ts = int(time.time())
    email = f"test_hist_{ts}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "strongpassword123"})
    resp_login = client.post("/api/auth/login", json={"email": email, "password": "strongpassword123"})
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp_create = client.post("/api/download", json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "hist_test", "height": 720}, headers=headers)
    assert resp_create.status_code == 201
    task_id = resp_create.json()["task_id"]

    resp_hist = client.get("/api/history", headers=headers)
    assert resp_hist.status_code == 200
    history = resp_hist.json()
    assert isinstance(history, list)
    assert len(history) >= 1

    found = next((h for h in history if h["task_id"] == task_id), None)
    assert found is not None
    assert found["title"] == "hist_test"
    assert found["platform"] == "youtube"
    assert found["height"] == 720
    assert "created_at" in found

def test_daily_limit_exceeded(client):
    ts = int(time.time())
    email = f"test_limit_{ts}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "strongpassword123"})
    resp_login = client.post("/api/auth/login", json={"email": email, "password": "strongpassword123"})
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # FREE limit = 3. Создаём 3 задачи
    for i in range(3):
        resp = client.post("/api/download", json={"video_url": f"https://example.com/v{i}", "title": f"limit_{i}", "height": 720}, headers=headers)
        assert resp.status_code == 201

    # 4-я должна вернуть 402 LIMIT_REACHED
    resp = client.post("/api/download", json={"video_url": "https://example.com/v4", "title": "limit_4", "height": 720}, headers=headers)
    assert resp.status_code == 402
    assert resp.json()["detail"]["code"] == "LIMIT_REACHED"
