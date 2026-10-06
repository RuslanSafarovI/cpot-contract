
"""IDOR matrix: reads openapi.yaml, probes every {id} path with two tenants."""
import os, re, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "contract"))

from _http import http, BASE

OPENAPI = os.path.join(ROOT, "docs", "api", "openapi.yaml")
POLICY = os.path.join(ROOT, "docs", "api", "policy_decisions.yaml")
DENY = 404

def load_spec():
    import yaml
    with open(OPENAPI, encoding="utf-8") as f:
        return yaml.safe_load(f)

def deny_code():
    global DENY
    try:
        import yaml
        with open(POLICY, encoding="utf-8") as f:
            pol = yaml.safe_load(f) or {}
        for item in pol.get("decisions", []):
            if item.get("id") == "SEC-41" and item.get("decision"):
                DENY = int(item["decision"].get("deny_code", 404))
    except Exception:
        pass

def canonical(tenant, res, n=1):
    return f"{tenant}-{res}-{n}"

def id_paths(spec):
    out = []
    for path, item in spec.get("paths", {}).items():
        if "{" not in path:
            continue
        segs = [s for s in path.strip("/").split("/") if s]
        ph = [(i, segs[i - 1] if i > 0 else "root") for i, s in enumerate(segs) if s.startswith("{")]
        methods = [m.upper() for m in item if m in ("get", "post", "patch", "delete", "put")]
        out.append((path, ph, methods))
    return out

def build_url(path, ph, mode):
    segs = [s for s in path.strip("/").split("/") if s]
    vals = [canonical("A", res) for (_, res) in ph]
    if mode == "attack" and ph:
        vals[0] = canonical("B", ph[0][1])
    it = iter(vals)
    filled = [next(it) if s.startswith("{") else s for s in segs]
    return "/" + "/".join(filled)

def main(base=BASE):
    deny_code()
    spec = load_spec()
    rows, fails = [], 0
    for path, ph, methods in id_paths(spec):
        for method in methods:
            attack = build_url(path, ph, "attack")
            control = build_url(path, ph, "control")
            body = {}
            if method == "POST":
                body = {"document_id": canonical("B", "documents")} if "packages" in path else {}
            code_a, _ = http(method, attack, "tok-A", body if method == "POST" else None, base=base)
            code_c, _ = http(method, control, "tok-A", body if method == "POST" else None, base=base)
            attack_ok = (code_a == DENY)
            control_ok = (code_c != 404)
            status = "PASS" if (attack_ok and control_ok) else "FAIL"
            if status == "FAIL":
                fails += 1
            rows.append({"method": method, "path": path, "attack": code_a, "control": code_c, "status": status})
    passed = len(rows) - fails
    print(f"idor         {'PASS' if not fails else 'FAIL'}  probes={len(rows)} pass={passed} fail={fails} deny={DENY}")
    for r in rows:
        if r["status"] == "FAIL":
            print(f"   - {r['method']} {r['path']}  attack={r['attack']} control={r['control']}")
    return rows, fails

if __name__ == "__main__":
    rows, fails = main()
    os.makedirs(os.path.join(ROOT, "docs", "security"), exist_ok=True)
    import csv
    with open(os.path.join(ROOT, "docs", "security", "idor_matrix.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["method", "path", "attack", "control", "status"])
        w.writeheader(); w.writerows(rows)
    with open(os.path.join(ROOT, "docs", "security", "idor_matrix.md"), "w", encoding="utf-8") as f:
        f.write("# IDOR matrix\n\n")
        f.write("| Method | Path | attack (A->B) | control (A->A) | Status |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['method']} | `{r['path']}` | {r['attack']} | {r['control']} | {r['status']} |\n")
    sys.exit(1 if fails else 0)
