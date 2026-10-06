from _http import http
from _runner import Checker

def run(base):
    c = Checker("out_of_band")
    # --- Channel 1: signed URL scope (F-03 / SEC-38,39) ---
    s, d = http("GET", "/document-packages/A-document-packages-1/download", "tok-A", base=base)
    c.eq("signed url issued", s, 200)
    url = d["data"]["url"]
    c.eq("own signed url ok", http("GET", url, None, base=base)[0], 200)
    c.eq("tampered signature", http("GET", url.replace("sig=", "sig=dead"), None, base=base)[0], 403)
    c.eq("foreign tenant claim", http("GET", url.replace("tenant=A", "tenant=B"), None, base=base)[0], 403)
    c.eq("expired url", http("GET", url.replace("exp=", "exp=1&_="), None, base=base)[0], 403)

    # --- Channel 2: AI/OCR context isolation (F-05 / SEC-42) ---
    s, d = http("POST", "/documents/ingest", "tok-A", {"refs": ["A-documents-1", "B-documents-1"]}, base=base)
    c.eq("ingest ok", s, 200)
    c.check("ai context only own", d["data"]["accepted_refs"] == ["A-documents-1"])
    c.check("foreign refs rejected", d["data"]["rejected_refs"] == ["B-documents-1"])
    c.eq("job visible to owner", http("GET", "/processing-jobs/A-processing-jobs-1", "tok-A", base=base)[0], 200)
    c.eq("job not visible to B", http("GET", "/processing-jobs/A-processing-jobs-1", "tok-B", base=base)[0], 404)

    # --- Channel 3: outbox envelope (F-06 / SEC-48,49) ---
    s, d = http("GET", "/outbox", "tok-A", base=base)
    c.eq("outbox ok", s, 200)
    c.check("every event carries tenant_id", all(e.get("tenant_id") == "A" for e in d["data"]))
    c.check("no foreign events", all("B" != e.get("tenant_id") for e in d["data"]))
    c.eq("foreign event direct", http("GET", "/outbox/B-outbox-1", "tok-A", base=base)[0], 404)
    c.eq("webhook to own destination", http("POST", "/webhooks/A-webhooks-1/test", "tok-A", {"destination": "https://hook.A.example"}, base=base)[0], 200)
    c.eq("webhook to foreign destination", http("POST", "/webhooks/A-webhooks-1/test", "tok-A", {"destination": "https://hook.B.example"}, base=base)[0], 403)
    return c
