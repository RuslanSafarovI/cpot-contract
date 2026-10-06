from _http import http
from _runner import Checker

def run(base):
    c = Checker("runtime_p1")

    c.eq("analysis start", http("POST","/analysis/company","tok-A",{},base=base)[0], 200)
    c.eq("analysis get own", http("GET","/analysis/A-analysis-1","tok-A",base=base)[0], 200)
    c.eq("findings own", http("GET","/analysis/A-analysis-1/findings","tok-A",base=base)[0], 200)
    c.eq("recommendations own", http("GET","/analysis/A-analysis-1/recommendations","tok-A",base=base)[0], 200)
    s,d = http("POST","/requests","tok-A",{"source_finding_id":"A-findings-1"},base=base)
    c.eq("request create", s, 201); rid = d["data"]["id"]
    c.eq("request get own", http("GET",f"/requests/{rid}","tok-A",base=base)[0], 200)
    c.eq("assign own executor", http("POST",f"/requests/{rid}/assign-executor","tok-A",{"executor_id":"A-executors-1"},base=base)[0], 200)
    c.eq("assign foreign executor", http("POST",f"/requests/{rid}/assign-executor","tok-A",{"executor_id":"Z-unknown"},base=base)[0], 404)
    s,d = http("POST","/document-packages","tok-A",{},base=base)
    c.eq("package create", s, 201); pid = d["data"]["id"]
    c.eq("package item own", http("POST",f"/document-packages/{pid}/items","tok-A",{"document_id":"A-documents-1"},base=base)[0], 201)
    c.eq("package build", http("POST",f"/document-packages/{pid}/build","tok-A",{"document_ids":["A-documents-1","B-documents-1"]},base=base)[0], 200)
    c.eq("package generate", http("POST",f"/document-packages/{pid}/generate","tok-A",{},base=base)[0], 200)
    c.eq("package download", http("GET",f"/document-packages/{pid}/download","tok-A",base=base)[0], 200)
    c.eq("review tasks list", http("GET","/review-tasks","tok-A",base=base)[0], 200)
    c.eq("review task own", http("GET","/review-tasks/A-review-tasks-1","tok-A",base=base)[0], 200)
    c.eq("review resolve manager", http("POST","/review-tasks/A-review-tasks-1/resolve","tok-A",{},{"X-Role":"manager"},base=base)[0], 200)
    c.eq("executors list", http("GET","/executors","tok-A",base=base)[0], 200)
    return c
