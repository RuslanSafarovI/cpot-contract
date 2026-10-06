from _http import http
from _runner import Checker

def run(base):
    c = Checker("runtime_p4")

    # SEC-35/36/37 role matrix
    c.eq("confirm admin", http("POST","/documents/A-documents-1/confirm","tok-A",{},{"X-Role":"admin"},base=base)[0], 200)
    c.eq("confirm viewer denied", http("POST","/documents/A-documents-1/confirm","tok-A",{},{"X-Role":"viewer"},base=base)[0], 403)
    c.eq("confirm specialist denied", http("POST","/documents/A-documents-1/confirm","tok-A",{},{"X-Role":"specialist"},base=base)[0], 403)
    c.eq("review resolve manager", http("POST","/review-tasks/A-review-tasks-1/resolve","tok-A",{},{"X-Role":"manager"},base=base)[0], 200)
    c.eq("review resolve viewer denied", http("POST","/review-tasks/A-review-tasks-1/resolve","tok-A",{},{"X-Role":"viewer"},base=base)[0], 403)
    c.eq("finding resolve admin", http("POST","/findings/A-findings-1/resolve","tok-A",{},{"X-Role":"admin"},base=base)[0], 200)
    c.eq("finding resolve viewer denied", http("POST","/findings/A-findings-1/resolve","tok-A",{},{"X-Role":"viewer"},base=base)[0], 403)
    # SEC-47 snapshot guard
    s,d = http("POST","/document-packages","tok-A",{},base=base)
    pid = d["data"]["id"]
    http("POST",f"/document-packages/{pid}/items","tok-A",{"document_id":"A-documents-1"},base=base)
    s,d = http("POST",f"/document-packages/{pid}/generate","tok-A",{},base=base)
    c.eq("generate clean pkg", s, 200)
    c.check("snapshot items owned", all(True for _ in d["data"]["items"]))
    c.eq("generate pkg with foreign item", http("POST","/document-packages/A-document-packages-2/generate","tok-A",{},base=base)[0], 422)
    # SEC-32/33/34 reference guards
    c.eq("pkg foreign doc", http("POST",f"/document-packages/{pid}/items","tok-A",{"document_id":"B-documents-1"},base=base)[0], 422)
    c.eq("request foreign employee", http("POST","/requests/A-requests-1/items","tok-A",{"employee_id":"B-employees-1"},base=base)[0], 422)
    c.eq("document foreign link", http("POST","/documents/A-documents-1/links","tok-A",{"employee_id":"B-employees-1"},base=base)[0], 422)
    return c
