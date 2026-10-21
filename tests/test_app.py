"""Automated tests for startdeck. Run: .venv/bin/python -m pytest tests/ -q"""
import http.server
import os
import socket
import tempfile
import threading

import pytest

_tmp = tempfile.mkdtemp(prefix="sd-test-")
os.environ["STARTDECK_DB_PATH"] = os.path.join(_tmp, "test.db")
os.environ["SD_INITIAL_USERNAME"] = "admin"
os.environ["SD_INITIAL_PASSWORD"] = "admin123"

import app as appmod  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


# ------------------------------------------------------------ fake site ----

class _OkHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):  # keep test output quiet
        pass


@pytest.fixture(scope="module")
def fake_site():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _OkHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}/"
    server.shutdown()


@pytest.fixture(scope="module")
def dead_url():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return f"http://127.0.0.1:{port}/"


# -------------------------------------------------------------- fixtures ----

@pytest.fixture(scope="module")
def client():
    with TestClient(appmod.app) as c:
        yield c


def do_login(client, password="admin123"):
    res = client.post("/api/login", json={"username": "admin", "password": password})
    assert res.status_code == 200, res.text
    return res.json()


# 每个用例独立登录：改密会作废同用户的其他会话，用例之间不能共用 token
@pytest.fixture(scope="function")
def auth(client):
    data = do_login(client)
    return {"Authorization": f"Bearer {data['token']}"}


def mk_section(client, auth, name):
    res = client.post("/api/sections", json={"name": name}, headers=auth)
    assert res.status_code == 200, res.text
    return res.json()


def mk_link(client, auth, section_id, name, url, description=""):
    res = client.post(
        "/api/links",
        json={"section_id": section_id, "name": name, "url": url,
              "description": description},
        headers=auth,
    )
    assert res.status_code == 200, res.text
    return res.json()


# ---------------------------------------------------------------- auth ----

def test_login_wrong_password(client):
    res = client.post("/api/login", json={"username": "admin", "password": "nope"})
    assert res.status_code == 401


def test_login_ok_and_must_change(client):
    data = do_login(client)
    assert data["token"]
    assert data["must_change_password"] is True


def test_unauthenticated_rejected(client):
    assert client.get("/api/sections").status_code == 401
    assert client.get("/api/links").status_code == 401
    assert client.post("/api/check-all").status_code == 401
    assert client.post("/api/sections", json={"name": "x"}).status_code == 401


def test_change_password(client, auth):
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123", "new_password": "newpass456"},
        headers=auth,
    )
    assert res.status_code == 200, res.text
    assert do_login(client, "newpass456")["must_change_password"] is False
    # restore for later tests
    token2 = do_login(client, "newpass456")["token"]
    res = client.post(
        "/api/change-password",
        json={"old_password": "newpass456", "new_password": "admin123"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res.status_code == 200


def test_change_password_revokes_other_sessions(client):
    token_a = do_login(client)["token"]
    token_b = do_login(client)["token"]
    ha = {"Authorization": f"Bearer {token_a}"}
    hb = {"Authorization": f"Bearer {token_b}"}
    assert client.get("/api/me", headers=ha).status_code == 200
    assert client.get("/api/me", headers=hb).status_code == 200
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123", "new_password": "temp999"},
        headers=ha,
    )
    assert res.status_code == 200, res.text
    # 本次会话继续有效，其他会话被作废
    assert client.get("/api/me", headers=ha).status_code == 200
    assert client.get("/api/me", headers=hb).status_code == 401
    # 恢复密码
    res = client.post(
        "/api/change-password",
        json={"old_password": "temp999", "new_password": "admin123"},
        headers=ha,
    )
    assert res.status_code == 200


# ------------------------------------------------------------ sections ----

def test_create_and_list_section(client, auth):
    s = mk_section(client, auth, "工作台")
    assert s["name"] == "工作台"
    assert s["links"] == []
    listed = client.get("/api/sections", headers=auth).json()
    assert any(x["id"] == s["id"] for x in listed)


def test_create_section_empty_name_rejected(client, auth):
    res = client.post("/api/sections", json={"name": "   "}, headers=auth)
    assert res.status_code == 400


def test_rename_section(client, auth):
    s = mk_section(client, auth, "旧名字")
    res = client.put(f"/api/sections/{s['id']}", json={"name": "新名字"}, headers=auth)
    assert res.status_code == 200, res.text
    assert res.json()["name"] == "新名字"
    res = client.put("/api/sections/999999", json={"name": "x"}, headers=auth)
    assert res.status_code == 404


def test_delete_section_cascades_links(client, auth):
    s = mk_section(client, auth, "待删分组")
    link = mk_link(client, auth, s["id"], "陪葬链接", "https://example.com/")
    res = client.delete(f"/api/sections/{s['id']}", headers=auth)
    assert res.status_code == 200
    assert client.get(f"/api/links/{link['id']}", headers=auth).status_code == 404
    listed = client.get("/api/sections", headers=auth).json()
    assert all(x["id"] != s["id"] for x in listed)


# --------------------------------------------------------------- links ----

def test_create_link_and_icon(client, auth):
    s = mk_section(client, auth, "图标组")
    link = mk_link(client, auth, s["id"], "示例站",
                   "https://example.com/some/page?x=1", "一个例子")
    assert link["description"] == "一个例子"
    assert link["icon_url"] == "https://example.com/favicon.ico"
    listed = client.get("/api/sections", headers=auth).json()
    sec = [x for x in listed if x["id"] == s["id"]][0]
    assert [l["id"] for l in sec["links"]] == [link["id"]]


def test_create_link_invalid_url_rejected(client, auth):
    s = mk_section(client, auth, "校验组")
    for bad in ("ftp://example.com/", "example.com", "https://", ""):
        res = client.post(
            "/api/links",
            json={"section_id": s["id"], "name": "坏链接", "url": bad},
            headers=auth,
        )
        assert res.status_code == 400, bad


def test_create_link_missing_section_404(client, auth):
    res = client.post(
        "/api/links",
        json={"section_id": 999999, "name": "孤儿", "url": "https://example.com/"},
        headers=auth,
    )
    assert res.status_code == 404


def test_update_link_fields(client, auth):
    s = mk_section(client, auth, "编辑组")
    link = mk_link(client, auth, s["id"], "旧名", "https://a.example.com/", "旧说明")
    res = client.put(
        f"/api/links/{link['id']}",
        json={"name": "新名", "url": "https://b.example.org/x", "description": "新说明"},
        headers=auth,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["name"] == "新名"
    assert body["url"] == "https://b.example.org/x"
    assert body["description"] == "新说明"
    assert body["icon_url"] == "https://b.example.org/favicon.ico"


def test_move_link_between_sections(client, auth):
    a = mk_section(client, auth, "来源组")
    b = mk_section(client, auth, "目标组")
    link = mk_link(client, auth, a["id"], "会搬家的链接", "https://move.example.com/")
    res = client.put(
        f"/api/links/{link['id']}", json={"section_id": b["id"]}, headers=auth
    )
    assert res.status_code == 200, res.text
    assert res.json()["section_id"] == b["id"]
    listed = client.get("/api/sections", headers=auth).json()
    by_id = {x["id"]: x for x in listed}
    assert link["id"] not in [l["id"] for l in by_id[a["id"]]["links"]]
    assert link["id"] in [l["id"] for l in by_id[b["id"]]["links"]]
    # moving to a missing section is a 404
    res = client.put(
        f"/api/links/{link['id']}", json={"section_id": 999999}, headers=auth
    )
    assert res.status_code == 404


def test_delete_link(client, auth):
    s = mk_section(client, auth, "删除组")
    link = mk_link(client, auth, s["id"], "待删链接", "https://del.example.com/")
    res = client.delete(f"/api/links/{link['id']}", headers=auth)
    assert res.status_code == 200
    assert client.get(f"/api/links/{link['id']}", headers=auth).status_code == 404


# -------------------------------------------------------------- search ----

def test_search_filters_name_desc_url(client, auth):
    s = mk_section(client, auth, "搜索组")
    mk_link(client, auth, s["id"], "邮箱入口", "https://mail.corp.example/",
            "公司邮件系统")
    mk_link(client, auth, s["id"], "代码仓库", "https://git.corp.example/",
            "内部 Git 服务")
    by_name = client.get("/api/links", params={"q": "邮箱"}, headers=auth).json()
    assert [l["name"] for l in by_name] == ["邮箱入口"]
    by_desc = client.get("/api/links", params={"q": "Git"}, headers=auth).json()
    assert [l["name"] for l in by_desc] == ["代码仓库"]
    by_url = client.get("/api/links", params={"q": "mail.corp"}, headers=auth).json()
    assert [l["name"] for l in by_url] == ["邮箱入口"]
    none = client.get("/api/links", params={"q": "不存在xyz"}, headers=auth).json()
    assert none == []
    scoped = client.get(
        "/api/links", params={"section_id": s["id"]}, headers=auth
    ).json()
    assert len(scoped) == 2


# --------------------------------------------------------------- probe ----

def test_probe_up(client, auth, fake_site):
    s = mk_section(client, auth, "探测组-通")
    link = mk_link(client, auth, s["id"], "活着的服务", fake_site)
    res = client.post(f"/api/links/{link['id']}/check", headers=auth)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["link_id"] == link["id"]
    assert body["up"] is True
    assert body["status_code"] == 200
    assert body["response_ms"] is not None and body["response_ms"] >= 0
    assert body["error"] is None


def test_probe_down(client, auth, dead_url):
    s = mk_section(client, auth, "探测组-断")
    link = mk_link(client, auth, s["id"], "死掉的服务", dead_url)
    res = client.post(f"/api/links/{link['id']}/check", headers=auth)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["up"] is False
    assert body["status_code"] is None
    assert body["error"]


def test_check_all_mixed(client, auth, fake_site, dead_url):
    s = mk_section(client, auth, "探测组-全部")
    up_link = mk_link(client, auth, s["id"], "批量-通", fake_site)
    down_link = mk_link(client, auth, s["id"], "批量-断", dead_url)
    res = client.post("/api/check-all", headers=auth)
    assert res.status_code == 200, res.text
    by_id = {r["link_id"]: r for r in res.json()}
    assert by_id[up_link["id"]]["up"] is True
    assert by_id[down_link["id"]]["up"] is False


def test_probe_unit_redirect_counts_up():
    class _RedirectHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", "/elsewhere")
            self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _RedirectHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        result = appmod.probe(f"http://127.0.0.1:{port}/")
        assert result["up"] is True
        assert result["status_code"] == 302
    finally:
        server.shutdown()


def test_favicon_url_unit():
    assert appmod.favicon_url_for("https://sub.example.com:8443/a/b?c=d") == \
        "https://sub.example.com:8443/favicon.ico"
    assert appmod.favicon_url_for("http://192.168.1.1/admin") == \
        "http://192.168.1.1/favicon.ico"
