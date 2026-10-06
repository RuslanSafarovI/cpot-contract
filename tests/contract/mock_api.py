
import json, os, re, hashlib, hmac, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OPENAPI = os.path.join(ROOT, "docs", "api", "openapi.yaml")
LEAKY = os.environ.get("CPOT_MOCK_LEAKY") == "1"
SECRET = b"cpot-secret"

TOKENS = {"tok-A": "A", "tok-B": "B"}
ROLE_RESTRICTED = {
    ("POST", "/documents/{id}/confirm"),
    ("POST", "/review-tasks/{id}/resolve"),
    ("POST", "/findings/{id}/resolve"),
}
ALLOWED_ROLES = {"admin", "manager"}

STATE = {"store": {}, "owned": set(), "counter": 100, "idem": {}, "outbox": []}

def _load_routes():
    try:
        import yaml
        with open(OPENAPI, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
    except Exception:
        spec = {"paths": {}}
    routes = []
    resources = set()
    for path, item in spec.get("paths", {}).items():
        segs = [s for s in path.strip("/").split("/") if s]
        for i, s in enumerate(segs):
            if s.startswith("{") and i > 0:
                resources.add(segs[i - 1])
        methods = [m.upper() for m in item if m in ("get", "post", "patch", "delete", "put")]
        rx = "^" + re.sub(r"\{[^}]+\}", r"([^/]+)", path) + "$"
        routes.append((re.compile(rx), path, methods, segs))
    return routes, resources

ROUTES, RESOURCES = _load_routes()

def _placeholder_index(segs):
    return [(i, segs[i - 1] if i > 0 else "root") for i, s in enumerate(segs) if s.startswith("{")]

def _seed():
    STATE["store"].clear(); STATE["owned"].clear()
    STATE["counter"] = 100; STATE["idem"].clear()
    STATE["outbox"] = [
        {"id": "A-outbox-1", "tenant_id": "A", "type": "document.confirmed", "payload": {"document_id": "A-documents-1"}},
        {"id": "B-outbox-1", "tenant_id": "B", "type": "document.confirmed", "payload": {"document_id": "B-documents-1"}},
    ]
    for res in sorted(RESOURCES):
        for t in ("A", "B"):
            oid = f"{t}-{res}-1"
            STATE["store"][(res, oid)] = {"tenant": t, "version": 1, "status": "draft", "data": {"id": oid, "organization_id": f"{t}-organizations-1"}}
            STATE["owned"].add(oid)
    # package A-2 carries a foreign item -> SEC-47 snapshot guard
    STATE["store"][("document-packages", "A-document-packages-2")] = {
        "tenant": "A", "version": 1, "status": "draft",
        "data": {"id": "A-document-packages-2", "organization_id": "A-organizations-1", "status": "draft", "version": 1},
        "items": [{"document_id": "B-documents-1"}],
    }
    STATE["owned"].add("A-document-packages-2")

def _tenant(token):
    return TOKENS.get(token)

def _owner(res, oid):
    obj = STATE["store"].get((res, oid))
    return obj["tenant"] if obj else None

def _sign(tenant, key, exp):
    msg = f"{tenant}:{key}:{exp}".encode()
    return hmac.new(SECRET, msg, hashlib.sha256).hexdigest()

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass

    def _send(self, code, payload=None):
        raw = b"" if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if raw: self.wfile.write(raw)

    def _read(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n: return {}
        try: return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception: return {}

    def _handle(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/_reset":
            _seed(); return self._send(200, {"ok": True})
        if path == "/_leaky":
            return self._send(200, {"leaky": LEAKY})

        if path == "/document-packages/download-signed":
            return self._verify_signed(query)

        auth = self.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "").strip() if auth.startswith("Bearer ") else None
        tenant = _tenant(token)
        if tenant is None:
            return self._send(401, {"code": "unauthorized"})

        for rx, template, methods, segs in ROUTES:
            m = rx.match(path)
            if not m: continue
            if method not in methods: continue
            values = list(m.groups())
            ph = _placeholder_index(segs)
            # ownership check
            for (idx, res), val in zip(ph, values):
                own = _owner(res, val)
                if not LEAKY and own is not None and own != tenant:
                    return self._send(404, {"code": "not_found"})
            if not LEAKY:
                for (idx, res), val in zip(ph, values):
                    if (res, val) not in STATE["store"] and val not in STATE["owned"]:
                        return self._send(404, {"code": "not_found"})
            return self._dispatch(method, template, values, segs, tenant, query)

        # collection fallback
        segs = [s for s in path.strip("/").split("/") if s]
        if segs and method == "GET":
            res = segs[-1]
            items = [o["data"] for (r, i), o in STATE["store"].items() if r == res and o["tenant"] == tenant]
            return self._send(200, {"data": items, "meta": {"pagination": {"total": len(items), "limit": 50, "offset": 0}}})
        if segs and method == "POST":
            return self._create(segs[-1], tenant)
        return self._send(404, {"code": "not_found"})

    def _create(self, res, tenant):
        STATE["counter"] += 1
        oid = f"{tenant}-{res}-{STATE['counter']}"
        data = {"id": oid, "organization_id": f"{tenant}-organizations-1", "status": "draft", "version": 1}
        STATE["store"][(res, oid)] = {"tenant": tenant, "version": 1, "status": "draft", "data": data}
        STATE["owned"].add(oid)
        return self._send(201, {"data": data})

    def _dispatch(self, method, template, values, segs, tenant, query):
        ph = _placeholder_index(segs)
        res0 = ph[0][1] if ph else (segs[-1] if segs else "root")
        role = self.headers.get("X-Role", "admin")
        if (method, template) in ROLE_RESTRICTED and role not in ALLOWED_ROLES:
            return self._send(403, {"code": "forbidden"})

        body = self._read()

        # ---- auth ----
        if template == "/auth/login":
            if body.get("password") == "bad":
                return self._send(401, {"code": "invalid_credentials"})
            return self._send(200, {"data": {"access_token": "tok-" + tenant, "refresh_token": "r-" + tenant, "expires_in": 3600}})
        if template == "/auth/mfa/enroll":
            return self._send(201, {"data": {"secret": "S3CR3T", "otpauth_url": "otpauth://totp/cpot", "status": "pending"}})
        if template == "/auth/mfa/verify":
            return self._send(200, {"data": {"status": "enabled"}}) if body.get("code") == "123456" else self._send(401, {"code": "invalid_code"})
        if template == "/auth/mfa/disable":
            return self._send(204)
        if template == "/auth/password/reset-request":
            return self._send(202, {"data": {"status": "accepted"}})
        if template == "/auth/password/reset":
            return self._send(204) if body.get("token") == "valid-token" else self._send(422, {"code": "invalid_token"})
        if template == "/auth/password/change":
            return self._send(204) if body.get("old_password") == "correct" else self._send(401, {"code": "invalid_password"})
        if template == "/me":
            return self._send(200, {"data": {"id": f"{tenant}-users-1", "email": "u@example", "role": role, "organization_id": f"{tenant}-organizations-1"}})

        if template == "/analysis/company":
            return self._send(200, {"data": {"id": f"{tenant}-analysis-1", "organization_id": f"{tenant}-organizations-1", "status": "running"}})

        # ---- documents ----
        if template == "/documents/ingest":
            refs = body.get("refs", [])
            acc, rej = [], []
            for r in refs:
                own = _owner("documents", r)
                (acc if own == tenant else rej).append(r)
            return self._send(200, {"data": {"accepted_refs": acc, "rejected_refs": rej, "job_id": f"{tenant}-processing-jobs-1"}})
        if template == "/documents/{id}/links" and method == "POST":
            emp = body.get("employee_id")
            if emp and _owner("employees", emp) not in (None, tenant):
                return self._send(422, {"code": "foreign_reference"})
            return self._send(200, {"data": {"id": "link-1"}})

        # ---- packages ----
        if template == "/document-packages/{id}/items" and method == "POST":
            doc = body.get("document_id")
            if doc and _owner("documents", doc) not in (None, tenant):
                return self._send(422, {"code": "foreign_reference"})
            obj = STATE["store"].get(("document-packages", values[0]))
            if obj is not None:
                obj.setdefault("items", []).append({"document_id": doc})
            return self._send(201, {"data": {"id": "item-1", "document_id": doc}})
        if template == "/document-packages/{id}/build":
            docs = [d for d in body.get("document_ids", []) if _owner("documents", d) in (None, tenant)]
            return self._send(200, {"data": {"items": [{"document_id": d} for d in docs]}})
        if template == "/document-packages/{id}/generate":
            pid = values[0]
            obj = STATE["store"].get(("document-packages", pid))
            items = (obj or {}).get("items", [])
            for it in items:
                doc = it.get("document_id")
                if doc and _owner("documents", doc) not in (None, tenant):
                    return self._send(422, {"code": "snapshot_foreign_item"})
            if obj is not None:
                obj["status"] = "ready"; obj["data"]["status"] = "ready"
            return self._send(200, {"data": {"package_id": pid, "items": items, "snapshot_at": "2026-01-01T00:00:00Z"}})
        elif template == "/document-packages/{id}/download":
            # Явно проверяем наличие values и берем id из пути, а не из values
            if not values:
                return self._send(404, {"code": "not_found"})
            pid = values
            exp = int(time.time()) + 300
            key = f"packages/{pid}"
            sig = _sign(tenant, key, exp)
            url = (
                f"http://127.0.0.1:{os.environ.get('CPOT_PORT', 52868)}/document-packages/download-signed?"
                f"tenant={tenant}&key={key}&exp={exp}&sig={sig}"
            )
            return self._send(200, {"data": {"url": url, "expires_at": "2026-01-01T00:05:00Z"}})

        # ---- requests ----
        if template == "/requests/{id}/assign-executor":
            ex = body.get("executor_id")
            if ex and ex not in STATE["owned"] and ("executors", ex) not in STATE["store"]:
                return self._send(404, {"code": "executor_not_found"})
            return self._send(200, {"data": {"status": "assigned"}})
        if template == "/requests/{id}/items":
            for k, res in (("employee_id", "employees"), ("document_id", "documents")):
                v = body.get(k)
                if v and _owner(res, v) not in (None, tenant):
                    return self._send(422, {"code": "foreign_reference"})
            return self._send(201, {"data": {"id": "item-1"}})

        # ---- executors ----
        if template == "/executors/{id}/organizations/{organization_id}/access" and method == "POST":
            if values[1] != f"{tenant}-organizations-1":
                return self._send(403, {"code": "foreign_organization"})
            return self._send(201, {"data": {"executor_id": values[0], "organization_id": values[1]}})
        if template == "/executors/{id}/organizations/{organization_id}/access" and method == "DELETE":
            return self._send(204)

        # ---- sout / ppe / workplaces ----
        if template == "/sout-cards/{id}/confirm":
            return self._send(200, {"data": {"status": "approved"}})
        if template == "/ppe/{id}/issue":
            return self._send(200, {"data": {"status": "issued"}})
        if template.endswith("/archive"):
            obj = STATE["store"].get((res0, values[0]))
            if obj is not None:
                obj["status"] = "archived"; obj["data"]["status"] = "archived"
            return self._send(204)

        # ---- webhooks ----
        if template == "/webhooks/{id}/test":
            dest = body.get("destination")
            if dest and not dest.endswith(f"{tenant}.example"):
                return self._send(403, {"code": "foreign_destination"})
            return self._send(200, {"data": {"delivered": True, "tenant_id": tenant}})

        # ---- outbox ----
        if template == "/outbox":
            items = [e for e in STATE["outbox"] if e["tenant_id"] == tenant]
            return self._send(200, {"data": items, "meta": {"pagination": {"total": len(items), "limit": 50, "offset": 0}}})
        if template == "/outbox/{id}":
            for e in STATE["outbox"]:
                if e["id"] == values[0] and e["tenant_id"] == tenant:
                    return self._send(200, {"data": e})
            return self._send(404, {"code": "not_found"})

        # ---- generic PATCH with If-Match ----
        if method == "PATCH":
            res = res0
            oid = values[0]
            obj = STATE["store"].get((res, oid))
            if obj is None:
                return self._send(404, {"code": "not_found"})
            if_match = self.headers.get("If-Match")
            if if_match and if_match.strip('"') != str(obj["version"]):
                return self._send(409, {"code": "version_conflict"})
            obj["version"] += 1; obj["data"]["version"] = obj["version"]
            obj["data"].update({k: v for k, v in body.items() if k in ("name", "title", "full_name", "status")})
            return self._send(200, {"data": obj["data"]})

        if method == "DELETE":
            return self._send(204)

        if method == "GET":
            if not values:
                res = segs[-1]
                items = [o["data"] for (r, i), o in STATE["store"].items() if r == res and o["tenant"] == tenant]
                return self._send(200, {"data": items, "meta": {"pagination": {"total": len(items), "limit": 50, "offset": 0}}})
            res = res0
            oid = values[0] if values else None
            obj = STATE["store"].get((res, oid)) if oid else None
            if obj is None:
                return self._send(404, {"code": "not_found"})
            if obj.get("status") == "archived":
                return self._send(410, {"code": "archived"})
            return self._send(200, {"data": obj["data"]})

        if method == "POST":
            if not values:
                return self._create(res0, tenant)
            return self._send(200, {"data": {"ok": True}})

        return self._send(405, {"code": "method_not_allowed"})

    def _verify_signed(self, query):
        tenant = (query.get("tenant") or [""])[0]
        key = (query.get("key") or [""])[0]
        exp = (query.get("exp") or ["0"])[0]
        sig = (query.get("sig") or [""])[0]
        if _sign(tenant, key, exp) != sig:
            return self._send(403, {"code": "bad_signature"})
        if int(exp) < int(time.time()):
            return self._send(403, {"code": "expired"})
        return self._send(200, {"data": {"ok": True}})

    def do_GET(self): self._handle("GET")
    def do_POST(self): self._handle("POST")
    def do_PATCH(self): self._handle("PATCH")
    def do_DELETE(self): self._handle("DELETE")

def serve(port=52868):
    _seed()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    return httpd

if __name__ == "__main__":
    _seed()
    srv = ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("CPOT_PORT", "52868"))), Handler)
    print("mock on", srv.server_address)
    srv.serve_forever()
