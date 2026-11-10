"""Local demo router with health checks, round-robin selection and failover."""
import json, os, itertools
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import perf_counter

TOKEN=os.environ.get("SSE_DEMO_TOKEN","local-demo-change-me")
HOST=os.environ.get("SSE_BIND","127.0.0.1")
PORT=int(os.environ.get("SSE_ROUTER_PORT","8100"))
RAW=os.environ.get("SSE_NODES","PC2=http://127.0.0.1:8101,PC3=http://127.0.0.1:8102")
NODES=[tuple(item.split("=",1)) for item in RAW.split(",") if "=" in item]
cycle=itertools.cycle(NODES)
MAX_BODY=16_384

def post_json(url, path, body, timeout=2):
    data=json.dumps(body).encode()
    req=Request(url+path,data=data,headers={"Content-Type":"application/json","Authorization":"Bearer "+TOKEN})
    with urlopen(req,timeout=timeout) as response: return json.loads(response.read())

class Handler(BaseHTTPRequestHandler):
    def send_json(self,status,value):
        data=json.dumps(value).encode(); self.send_response(status)
        self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(data)))
        self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path!="/health": return self.send_json(404,{"error":"not_found"})
        states=[]
        for name,url in NODES:
            try:
                with urlopen(url+"/health",timeout=1) as r: states.append({"node":name,"healthy":r.status==200})
            except Exception: states.append({"node":name,"healthy":False})
        self.send_json(200,{"router":"ok","nodes":states,"mode":"round_robin_with_failover"})
    def do_POST(self):
        if self.path!="/route": return self.send_json(404,{"error":"not_found"})
        if self.headers.get("Authorization")!="Bearer "+TOKEN: return self.send_json(401,{"error":"unauthorized"})
        try:
            n=int(self.headers.get("Content-Length","0"))
            if n<1 or n>MAX_BODY: return self.send_json(413,{"error":"invalid_body_size"})
            body=json.loads(self.rfile.read(n))
        except Exception: return self.send_json(400,{"error":"invalid_json"})
        if body.get("task") not in ("echo","text_stats") or not isinstance(body.get("text",""),str):
            return self.send_json(400,{"error":"unsupported_task_or_text"})
        if len(body.get("text",""))>8000: return self.send_json(400,{"error":"text_too_long"})
        attempts=[]
        # Rotate starting node per request; try every configured node once.
        start=next(cycle) if NODES else None
        ordered=([start]+[x for x in NODES if x!=start]) if start else []
        for name,url in ordered:
            t=perf_counter()
            try:
                result=post_json(url,"/execute",body)
                return self.send_json(200,{"status":"completed","selected_node":name,"router_ms":round((perf_counter()-t)*1000,3),"attempts":attempts,"worker_result":result})
            except Exception as exc:
                attempts.append({"node":name,"error":type(exc).__name__})
        self.send_json(503,{"status":"unavailable","attempts":attempts,"message":"No configured worker accepted the demo task"})
    def log_message(self,*_): pass

if __name__=="__main__":
    if not NODES: raise SystemExit("Configure SSE_NODES with at least one worker")
    print(f"Demo router listening on {HOST}:{PORT}; workers={len(NODES)}")
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
