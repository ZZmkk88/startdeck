"""Live self-test for startdeck: boots a real uvicorn server on a scratch
database and walks the whole user flow over HTTP.

Run: .venv/bin/python tests/live_selftest.py
"""
import os
import socket
import subprocess
import sys
import tempfile
import time

import httpx

BASE = "http://127.0.0.1:8131"
http = httpx.Client(trust_env=False)


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f" | {extra}" if extra else ""))
    if not cond:
        raise SystemExit(f"selftest failed at: {name}")


def dead_url():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return f"http://127.0.0.1:{port}/"


def main():
    tmp = tempfile.mkdtemp(prefix="sd-live-")
    env = dict(os.environ)
    env["STARTDECK_DB_PATH"] = os.path.join(tmp, "live.db")
    env["PORT"] = "8131"
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                if http.get(BASE + "/", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.2)
        else:
            raise SystemExit("server did not come up")

        page = http.get(BASE + "/")
        check("首页能打开且是 startdeck 页面", "startdeck" in page.text)

        r = http.post(BASE + "/api/login",
                      json={"username": "admin", "password": "admin123"})
        check("登录成功", r.status_code == 200, r.text[:120])
        data = r.json()
        check("首次登录提示改密", data["must_change_password"] is True)
        h = {"Authorization": f"Bearer {data['token']}"}

        r = http.post(BASE + "/api/sections", json={"name": "工作"}, headers=h)
        check("建分组「工作」", r.status_code == 200, r.text[:120])
        work = r.json()
        r = http.post(BASE + "/api/sections", json={"name": "服务"}, headers=h)
        check("建分组「服务」", r.status_code == 200, r.text[:120])
        svc = r.json()

        def add_link(section_id, name, url, desc=""):
            rr = http.post(BASE + "/api/links",
                           json={"section_id": section_id, "name": name,
                                 "url": url, "description": desc},
                           headers=h)
            check(f"加链接：{name}", rr.status_code == 200, rr.text[:120])
            return rr.json()

        self_link = add_link(svc["id"], "本机面板", BASE + "/", "就是这个服务自己")
        dead_link = add_link(svc["id"], "断掉的服务", dead_url(), "没人监听的端口")
        doc_link = add_link(work["id"], "文档站", "https://example.com/", "示例文档")
        check("链接自动带 favicon 地址",
              self_link["icon_url"] == BASE.replace("http://", "http://") + "favicon.ico"
              or self_link["icon_url"].endswith("/favicon.ico"),
              self_link["icon_url"])

        r = http.get(BASE + "/api/sections", headers=h)
        secs = {s["name"]: s for s in r.json()}
        check("分组结构正确：工作 1 条、服务 2 条",
              len(secs["工作"]["links"]) == 1 and len(secs["服务"]["links"]) == 2)

        r = http.get(BASE + "/api/links", params={"q": "文档"}, headers=h)
        check("搜索「文档」命中 1 条", len(r.json()) == 1
              and r.json()[0]["id"] == doc_link["id"])

        r = http.post(BASE + f"/api/links/{self_link['id']}/check", headers=h)
        body = r.json()
        check("单条探测-通", r.status_code == 200 and body["up"] is True
              and body["status_code"] == 200 and body["response_ms"] is not None,
              str(body))

        r = http.post(BASE + f"/api/links/{dead_link['id']}/check", headers=h)
        body = r.json()
        check("单条探测-断", r.status_code == 200 and body["up"] is False
              and body["status_code"] is None, str(body))

        r = http.post(BASE + "/api/check-all", headers=h)
        by_id = {x["link_id"]: x for x in r.json()}
        check("全部探测：本机通、断口断",
              by_id[self_link["id"]]["up"] is True
              and by_id[dead_link["id"]]["up"] is False)

        r = http.put(BASE + f"/api/links/{doc_link['id']}",
                     json={"section_id": svc["id"]}, headers=h)
        check("链接移动到「服务」分组", r.status_code == 200
              and r.json()["section_id"] == svc["id"])
        r = http.get(BASE + "/api/sections", headers=h)
        secs = {s["name"]: s for s in r.json()}
        check("移动后：工作 0 条、服务 3 条",
              len(secs["工作"]["links"]) == 0 and len(secs["服务"]["links"]) == 3)

        r = http.put(BASE + f"/api/links/{doc_link['id']}",
                     json={"name": "文档站（改）"}, headers=h)
        check("编辑链接名称生效", r.status_code == 200
              and r.json()["name"] == "文档站（改）")

        r = http.delete(BASE + f"/api/links/{dead_link['id']}", headers=h)
        check("删除链接成功", r.status_code == 200)
        r = http.get(BASE + f"/api/links/{dead_link['id']}", headers=h)
        check("删后查不到", r.status_code == 404)

        r = http.delete(BASE + f"/api/sections/{svc['id']}", headers=h)
        check("删除分组成功", r.status_code == 200)
        r = http.get(BASE + f"/api/links/{self_link['id']}", headers=h)
        check("分组删除级联删链接", r.status_code == 404)

        print("LIVE SELFTEST: ALL PASS")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
