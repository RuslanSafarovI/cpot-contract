from _http import http
from _runner import Checker

def run(base):
    c = Checker("e2e_smoke")

    s,d = http("POST","/auth/login","tok-A",{"password":"good"},base=base); c.eq("login", s, 200)
    s,d = http("POST","/source-files/upload-sessions","tok-A",{"filename":"doc.pdf"},base=base)
    c.eq("upload session", s, 201); sid = d["data"]["id"]
    c.eq("upload complete", http("POST",f"/source-files/upload-sessions/{sid}/complete","tok-A",{},base=base)[0], 200)
    c.eq("ingest", http("POST","/documents/ingest","tok-A",{"refs":["A-documents-1"]},base=base)[0], 200)
    c.eq("confirm", http("POST","/documents/A-documents-1/confirm","tok-A",{},{"X-Role":"admin"},base=base)[0], 200)
    c.eq("analysis", http("POST","/analysis/company","tok-A",{},base=base)[0], 200)
    c.eq("findings", http("GET","/analysis/A-analysis-1/findings","tok-A",base=base)[0], 200)
    s,d = http("POST","/requests","tok-A",{"source_finding_id":"A-findings-1"},base=base); rid = d["data"]["id"]
    c.eq("request", s, 201)
    c.eq("assign", http("POST",f"/requests/{rid}/assign-executor","tok-A",{"executor_id":"A-executors-1"},base=base)[0], 200)
    s,d = http("POST","/document-packages","tok-A",{},base=base); pid = d["data"]["id"]
    c.eq("package", s, 201)
    http("POST",f"/document-packages/{pid}/items","tok-A",{"document_id":"A-documents-1"},base=base)
    c.eq("build", http("POST",f"/document-packages/{pid}/build","tok-A",{"document_ids":["A-documents-1"]},base=base)[0], 200)
    c.eq("generate", http("POST",f"/document-packages/{pid}/generate","tok-A",{},base=base)[0], 200)
    c.eq("download", http("GET",f"/document-packages/{pid}/download","tok-A",base=base)[0], 200)
    c.eq("tenant B sees nothing", http("GET",f"/document-packages/{pid}","tok-B",base=base)[0], 404)
    return c
