from _http import http
from _runner import Checker

def run(base):
    c = Checker("runtime_p0")

    s,_ = http("POST","/auth/login","tok-A",{"password":"good"},base=base)
    c.eq("login", s, 200)
    s,d = http("GET","/me","tok-A",base=base)
    c.eq("me", s, 200); c.eq("me org from context", d["data"]["organization_id"], "A-organizations-1")
    c.eq("org get own", http("GET","/organizations/A-organizations-1","tok-A",base=base)[0], 200)
    s,d = http("GET","/employees","tok-A",base=base)
    c.eq("employees list", s, 200); c.check("pagination", "pagination" in d.get("meta",{}))
    s,d = http("POST","/employees","tok-A",{"full_name":"Ivanov"},base=base)
    c.eq("employee create", s, 201); new_id = d["data"]["id"]
    c.check("new id not canonical", new_id != "A-employees-1")
    c.eq("employee get own", http("GET",f"/employees/{new_id}","tok-A",base=base)[0], 200)
    c.eq("employee patch stale", http("PATCH",f"/employees/{new_id}","tok-A",{"full_name":"P"},{"If-Match":'"99"'},base=base)[0], 409)
    s,d = http("PATCH",f"/employees/{new_id}","tok-A",{"full_name":"P"},{"If-Match":'"1"'},base=base)
    c.eq("employee patch ok", s, 200); c.eq("version bump", d["data"]["version"], 2)
    c.eq("search", http("GET","/employees/search?q=%D0%98","tok-A",base=base)[0], 200)
    c.eq("documents list", http("GET","/documents","tok-A",base=base)[0], 200)
    s,d = http("POST","/documents/ingest","tok-A",{"refs":["A-documents-1","B-documents-1"]},base=base)
    c.eq("ingest", s, 200)
    c.eq("ingest accepted", d["data"]["accepted_refs"], ["A-documents-1"])
    c.eq("ingest rejected", d["data"]["rejected_refs"], ["B-documents-1"])
    s,d = http("POST","/source-files/upload-sessions","tok-A",{"filename":"a.pdf"},base=base)
    c.eq("upload session", s, 201); sid = d["data"]["id"]
    c.eq("upload complete", http("POST",f"/source-files/upload-sessions/{sid}/complete","tok-A",{},base=base)[0], 200)
    c.eq("source file own", http("GET","/source-files/A-source-files-1","tok-A",base=base)[0], 200)
    c.eq("processing job own", http("GET","/processing-jobs/A-processing-jobs-1","tok-A",base=base)[0], 200)
    c.eq("document confirm admin", http("POST","/documents/A-documents-1/confirm","tok-A",{},{"X-Role":"admin"},base=base)[0], 200)
    return c
