from _http import http
from _runner import Checker

def run(base):
    c = Checker("runtime_p2")

    c.eq("mfa enroll", http("POST","/auth/mfa/enroll","tok-A",{},base=base)[0], 201)
    c.eq("mfa verify ok", http("POST","/auth/mfa/verify","tok-A",{"code":"123456"},base=base)[0], 200)
    c.eq("mfa verify bad", http("POST","/auth/mfa/verify","tok-A",{"code":"000"},base=base)[0], 401)
    c.eq("mfa disable", http("POST","/auth/mfa/disable","tok-A",{},base=base)[0], 204)
    c.eq("reset request", http("POST","/auth/password/reset-request","tok-A",{"email":"u@e"},base=base)[0], 202)
    c.eq("reset ok", http("POST","/auth/password/reset","tok-A",{"token":"valid-token"},base=base)[0], 204)
    c.eq("reset bad", http("POST","/auth/password/reset","tok-A",{"token":"x"},base=base)[0], 422)
    c.eq("change ok", http("POST","/auth/password/change","tok-A",{"old_password":"correct"},base=base)[0], 204)
    c.eq("change bad", http("POST","/auth/password/change","tok-A",{"old_password":"x"},base=base)[0], 401)
    s,d = http("POST","/users","tok-A",{"email":"n@e"},base=base)
    c.eq("user create", s, 201); uid = d["data"]["id"]
    c.eq("users list", http("GET","/users","tok-A",base=base)[0], 200)
    c.eq("user get own", http("GET",f"/users/{uid}","tok-A",base=base)[0], 200)
    c.eq("user get foreign", http("GET","/users/B-users-1","tok-A",base=base)[0], 404)
    c.eq("user patch stale", http("PATCH",f"/users/{uid}","tok-A",{"name":"x"},{"If-Match":'"9"'},base=base)[0], 409)
    c.eq("user patch ok", http("PATCH",f"/users/{uid}","tok-A",{"name":"x"},{"If-Match":'"1"'},base=base)[0], 200)
    c.eq("user delete", http("DELETE",f"/users/{uid}","tok-A",base=base)[0], 204)
    s,d = http("POST","/rules","tok-A",{"name":"r"},base=base)
    c.eq("rule create", s, 201); rule = d["data"]["id"]
    c.eq("rules list", http("GET","/rules","tok-A",base=base)[0], 200)
    c.eq("rule get own", http("GET",f"/rules/{rule}","tok-A",base=base)[0], 200)
    c.eq("rule foreign", http("GET","/rules/B-rules-1","tok-A",base=base)[0], 404)
    c.eq("rule patch stale", http("PATCH",f"/rules/{rule}","tok-A",{"name":"x"},{"If-Match":'"9"'},base=base)[0], 409)
    c.eq("rule delete", http("DELETE",f"/rules/{rule}","tok-A",base=base)[0], 204)
    c.eq("audit list", http("GET","/audit-events","tok-A",base=base)[0], 200)
    c.eq("audit foreign", http("GET","/audit-events/B-audit-events-1","tok-A",base=base)[0], 404)
    for r in ("deadlines","alerts","integrations"):
        c.eq(f"{r} list", http("GET",f"/{r}","tok-A",base=base)[0], 200)
    s,d = http("POST","/dictionaries/departments","tok-A",{"name":"d"},base=base)
    c.eq("department create", s, 201); dep = d["data"]["id"]
    c.eq("department patch stale", http("PATCH",f"/dictionaries/departments/{dep}","tok-A",{"name":"x"},{"If-Match":'"9"'},base=base)[0], 409)
    c.eq("department patch ok", http("PATCH",f"/dictionaries/departments/{dep}","tok-A",{"name":"x"},{"If-Match":'"1"'},base=base)[0], 200)
    c.eq("department archive", http("POST",f"/dictionaries/departments/{dep}/archive","tok-A",{},base=base)[0], 204)
    c.eq("archived -> 410", http("GET",f"/dictionaries/departments/{dep}","tok-A",base=base)[0], 410)
    c.eq("position patch", http("PATCH","/dictionaries/positions/A-positions-1","tok-A",{"name":"x"},{"If-Match":'"1"'},base=base)[0], 200)
    return c
