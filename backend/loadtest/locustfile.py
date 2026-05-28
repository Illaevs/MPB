"""
Load-test scenarios for the CRM backend.

Run via run_all.ps1 (sets env + server). Direct example:

  locust -f locustfile.py --headless -u 50 -r 10 -t 2m \
         --host http://127.0.0.1:8002 --csv results/read MixedUser

User classes (pick on CLI as the last arg):
  MixedUser  - realistic weighted blend (default)
  ReadUser   - light + heavy reads only
  WriteUser  - task create/update only (SQLite write contention)
  HeavyUser  - data-health PDF + finance only (event-loop blocking)

Auth is cookie-based (HttpOnly crm_access_token). Writes need the
crm_csrf_token cookie echoed back in the X-CSRF-Token header.

Each simulated user sends a unique X-Forwarded-For so the per-IP API
rate limiter gives every user its own bucket - lets us measure true
server capacity instead of the limiter. A separate default-limit run
verifies the limiter itself.
"""
import os
import random
import uuid

from locust import FastHttpUser, task, between

LOGIN_EMAIL = os.getenv("LOAD_EMAIL", "admin@nexus-demo.ru")
LOGIN_PASSWORD = os.getenv("LOAD_PASSWORD", "Nexus123!")
SPOOF_IP = os.getenv("LOAD_SPOOF_IP", "1") == "1"


class _Base(FastHttpUser):
    abstract = True
    wait_time = between(0.1, 0.5)

    def on_start(self):
        # Unique per-user fake client IP -> own rate-limit bucket.
        self._fip = ".".join(str(random.randint(1, 254)) for _ in range(4))
        self.csrf = ""
        self.deal_ids = []
        self.my_task_ids = []

        with self.client.post(
            "/api/v1/auth/login",
            json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
            headers=self._h(),
            name="POST /auth/login",
            catch_response=True,
        ) as r:
            if r.status_code != 200:
                r.failure(f"login {r.status_code}: {r.text[:120]}")
                return
            r.success()

        for c in self.client.cookiejar:
            if c.name == "crm_csrf_token":
                self.csrf = c.value or ""

        with self.client.get(
            "/api/v1/deals/", headers=self._h(), name="GET /deals/",
            catch_response=True,
        ) as r:
            try:
                data = r.json()
                arr = data if isinstance(data, list) else data.get("items", [])
                self.deal_ids = [d["id"] for d in arr if "id" in d]
            except Exception:
                pass

    def _h(self, write=False):
        h = {}
        if SPOOF_IP and getattr(self, "_fip", None):
            h["X-Forwarded-For"] = self._fip
        if write:
            h["X-CSRF-Token"] = self.csrf
        return h

    # ---- read building blocks -------------------------------------
    def _get(self, path, name):
        self.client.get(path, headers=self._h(), name=name)

    def light_reads(self):
        self._get("/api/v1/dashboard/summary", "GET /dashboard/summary")
        self._get("/api/v1/dashboard/activity", "GET /dashboard/activity")
        self._get("/api/v1/deals/", "GET /deals/")
        self._get("/api/v1/contracts/", "GET /contracts/")
        self._get("/api/v1/document-registry/", "GET /document-registry/")

    def heavy_reads(self):
        self._get("/api/v1/finance/overview", "GET /finance/overview")
        self._get("/api/v1/finance/cashflow", "GET /finance/cashflow")
        self._get("/api/v1/data-health/issues", "GET /data-health/issues")

    def cpu_pdf(self):
        # Synchronous reportlab PDF render inside an async endpoint.
        self.client.get(
            "/api/v1/data-health/report.pdf",
            headers=self._h(),
            name="GET /data-health/report.pdf [CPU]",
        )

    def known_bug_outgoing(self):
        # Observed 500 at baseline - quantify failure rate under load.
        with self.client.get(
            "/api/v1/outgoing-registry/",
            headers=self._h(),
            name="GET /outgoing-registry/ [bug?]",
            catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"{r.status_code}")
            else:
                r.success()

    def create_task(self):
        with self.client.post(
            "/api/v1/tasks/",
            json={
                "title": f"LOAD {uuid.uuid4().hex[:8]}",
                "deal_id": random.choice(self.deal_ids) if self.deal_ids else None,
                "status": "new",
                "priority": "normal",
            },
            headers=self._h(write=True),
            name="POST /tasks/ [write]",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.success()
                try:
                    tid = r.json().get("id")
                    if tid:
                        self.my_task_ids.append(tid)
                except Exception:
                    pass
            else:
                r.failure(f"{r.status_code}: {r.text[:120]}")

    def update_task(self):
        if not self.my_task_ids:
            self.create_task()
            return
        tid = random.choice(self.my_task_ids)
        self.client.put(
            f"/api/v1/tasks/{tid}",
            json={"title": f"LOAD upd {uuid.uuid4().hex[:6]}", "status": "in_progress"},
            headers=self._h(write=True),
            name="PUT /tasks/{id} [write]",
        )


class MixedUser(_Base):
    @task(10)
    def t_light(self):
        self.light_reads()

    @task(4)
    def t_heavy(self):
        self.heavy_reads()

    @task(2)
    def t_pdf(self):
        self.cpu_pdf()

    @task(3)
    def t_write(self):
        self.create_task()

    @task(2)
    def t_update(self):
        self.update_task()

    @task(1)
    def t_bug(self):
        self.known_bug_outgoing()


class ReadUser(_Base):
    @task(7)
    def t_light(self):
        self.light_reads()

    @task(3)
    def t_heavy(self):
        self.heavy_reads()


class WriteUser(_Base):
    @task(3)
    def t_create(self):
        self.create_task()

    @task(2)
    def t_update(self):
        self.update_task()


class HeavyUser(_Base):
    @task(3)
    def t_pdf(self):
        self.cpu_pdf()

    @task(2)
    def t_heavy(self):
        self.heavy_reads()
