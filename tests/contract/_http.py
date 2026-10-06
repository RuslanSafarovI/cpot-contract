
import json, urllib.request, urllib.parse, urllib.error

BASE = "http://127.0.0.1:52868"
TOKEN_A = "tok-A"
TOKEN_B = "tok-B"

def _encode(path):
    # path may be "/x?y=z"; encode only path + query, never scheme/host
    if "?" in path:
        p, q = path.split("?", 1)
        return urllib.parse.quote(p, safe="/%") + "?" + urllib.parse.quote(q, safe="=&%")
    return urllib.parse.quote(path, safe="/%")

def http(method, path, token=TOKEN_A, body=None, headers=None, base=None):
    b = base or BASE
    url = path if path.startswith("http") else b + _encode(path)
    data = None
    h = {"Accept": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    if headers:
        h.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode("utf-8")
            try: payload = json.loads(raw) if raw else {}
            except Exception: payload = {"_raw": raw}
            return r.status, payload
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try: payload = json.loads(raw) if raw else {}
        except Exception: payload = {"_raw": raw}
        return e.code, payload
    except Exception as e:
        return 0, {"_error": str(e)}
