from _http import http
from _runner import Checker

def run(base):
    c = Checker("runtime_p3")

    s,d = http("POST","/workplaces","tok-A",{"name":"w"},base=base)
    c.eq("workplace create", s, 201); wid = d["data"]["id"]
    c.eq("workplaces list", http("GET","/workplaces","tok-A",base=base)[0], 200)
    c.eq("workplace get own", http("GET",f"/workplaces/{wid}","tok-A",base=base)[0], 200)
    c.eq("workplace foreign", http("GET","/workplaces/B-workplaces-1","tok-A",base=base)[0], 404)
    c.eq("workplace patch stale", http("PATCH",f"/workplaces/{wid}","tok-A",{"name":"x"},{"If-Match":'"9"'},base=base)[0], 409)
    c.eq("workplace patch ok", http("PATCH",f"/workplaces/{wid}","tok-A",{"name":"x"},{"If-Match":'"1"'},base=base)[0], 200)
    c.eq("workplace archive", http("POST",f"/workplaces/{wid}/archive","tok-A",{},base=base)[0], 204)
    c.eq("archived -> 410", http("GET",f"/workplaces/{wid}","tok-A",base=base)[0], 410)
    s,d = http("POST","/hazards","tok-A",{"name":"h"},base=base)
    c.eq("hazard create", s, 201); hid = d["data"]["id"]
    c.eq("hazards list", http("GET","/hazards","tok-A",base=base)[0], 200)
    c.eq("hazard get own", http("GET",f"/hazards/{hid}","tok-A",base=base)[0], 200)
    c.eq("hazard foreign", http("GET","/hazards/B-hazards-1","tok-A",base=base)[0], 404)
    c.eq("hazard patch", http("PATCH",f"/hazards/{hid}","tok-A",{"name":"x"},{"If-Match":'"1"'},base=base)[0], 200)
    s,d = http("POST","/sout-cards","tok-A",{"workplace_id":wid},base=base)
    c.eq("sout create", s, 201); sid = d["data"]["id"]
    c.eq("sout list", http("GET","/sout-cards","tok-A",base=base)[0], 200)
    c.eq("sout get own", http("GET",f"/sout-cards/{sid}","tok-A",base=base)[0], 200)
    c.eq("sout foreign", http("GET","/sout-cards/B-sout-cards-1","tok-A",base=base)[0], 404)
    c.eq("sout patch", http("PATCH",f"/sout-cards/{sid}","tok-A",{"name":"x"},{"If-Match":'"1"'},base=base)[0], 200)
    c.eq("sout confirm", http("POST",f"/sout-cards/{sid}/confirm","tok-A",{},base=base)[0], 200)
    s,d = http("POST","/ppe","tok-A",{"name":"p"},base=base)
    c.eq("ppe create", s, 201); pid = d["data"]["id"]
    c.eq("ppe list", http("GET","/ppe","tok-A",base=base)[0], 200)
    c.eq("ppe get own", http("GET",f"/ppe/{pid}","tok-A",base=base)[0], 200)
    c.eq("ppe foreign", http("GET","/ppe/B-ppe-1","tok-A",base=base)[0], 404)
    c.eq("ppe patch", http("PATCH",f"/ppe/{pid}","tok-A",{"name":"x"},{"If-Match":'"1"'},base=base)[0], 200)
    c.eq("ppe issue", http("POST",f"/ppe/{pid}/issue","tok-A",{},base=base)[0], 200)
    return c
