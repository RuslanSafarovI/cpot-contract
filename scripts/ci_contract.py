
"""Contract stage orchestrator: static -> idor -> runtime_p0..p4 -> e2e -> out_of_band."""
import os, sys, threading, time, socket, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CONTRACT = os.path.join(ROOT, "tests", "contract")
sys.path.insert(0, CONTRACT)
sys.path.insert(0, HERE)

OPENAPI = os.path.join(ROOT, "docs", "api", "openapi.yaml")
SCHEMAS = os.path.join(ROOT, "docs", "api", "schemas.yaml")
POLICY = os.path.join(ROOT, "docs", "api", "policy_decisions.yaml")
STRICT = os.environ.get("CPOT_STRICT") == "1"

def run_static():
    import yaml
    if not os.path.exists(OPENAPI):
        if STRICT:
            print("static       FAIL  openapi.yaml missing (strict)")
            return False
        print("static       SKIP  openapi.yaml missing")
        return True
    with open(OPENAPI, encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    paths = spec.get("paths", {})
    ops = [m for p in paths.values() for m, o in p.items() if isinstance(o, dict)]
    ids = [paths[p][m]["operationId"] for p in paths for m in paths[p] if isinstance(paths[p][m], dict)]
    ok = spec.get("openapi") == "3.1.0" and len(ids) == len(set(ids))
    if os.path.exists(SCHEMAS):
        with open(SCHEMAS, encoding="utf-8") as f:
            yaml.safe_load(f)
    if os.path.exists(POLICY):
        with open(POLICY, encoding="utf-8") as f:
            yaml.safe_load(f)
    print(f"static       {'PASS' if ok else 'FAIL'}  openapi {spec.get('openapi')}, {len(paths)} paths, {len(ids)} ops")
    return ok

def pick_port():
    for p in (52868, 52869, 52870):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p)); s.close(); return p
        except OSError:
            continue
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

def main():
    results = []
    results.append(("static", run_static()))

    import mock_api, _http
    importlib.reload(mock_api); importlib.reload(_http)
    port = pick_port()
    srv = mock_api.serve(port)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.3)
    base = f"http://127.0.0.1:{port}"
    _http.BASE = base

    import idor_matrix
    importlib.reload(idor_matrix); idor_matrix.BASE = base
    _, fails = idor_matrix.main(base=base)
    results.append(("idor", fails == 0))

    for name in ("runtime_p0", "runtime_p1", "runtime_p2", "runtime_p3", "runtime_p4", "e2e_smoke", "out_of_band"):
        _http.http("GET", "/_reset", None, base=base) if False else None
        import urllib.request
        urllib.request.urlopen(base + "/_reset").read()
        mod = importlib.import_module(name)
        importlib.reload(mod)
        c = mod.run(base)
        results.append((name, c.report()))

    srv.shutdown()
    ok = all(r[1] for r in results)
    print("OK" if ok else "FAILED", "" if ok else f"({sum(1 for _,x in results if not x)} failing)")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
