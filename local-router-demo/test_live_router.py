import json, os, subprocess, sys, tempfile, time, unittest, uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=os.path.dirname(__file__)

class LiveRouterSmokeTest(unittest.TestCase):
    def test_worker_router_auth_and_replay_guard(self):
        token="test-token"
        with tempfile.TemporaryDirectory() as tmp:
            env=os.environ.copy()
            env.update({
                "SSE_DEMO_TOKEN":token, "SSE_BIND":"127.0.0.1",
                "SSE_NODE_ID":"TEST-PC", "SSE_PORT":"18101",
                "SSE_ROUTER_PORT":"18100",
                "SSE_NODES":"TEST-PC=http://127.0.0.1:18101",
                "SSE_STATE_DB":os.path.join(tmp,"state.sqlite3"),
            })
            worker=subprocess.Popen([sys.executable,os.path.join(ROOT,"worker.py")],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            router=subprocess.Popen([sys.executable,os.path.join(ROOT,"router.py")],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                ready=False
                for _ in range(50):
                    try:
                        with urlopen("http://127.0.0.1:18100/health",timeout=.2): ready=True; break
                    except Exception: time.sleep(.1)
                self.assertTrue(ready,"router did not become healthy")
                request_id=str(uuid.uuid4())
                payload={"task":"text_stats","text":"hello school AI","request_id":request_id}
                req=Request("http://127.0.0.1:18100/route",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
                with urlopen(req,timeout=3) as response: result=json.loads(response.read())
                self.assertEqual(result["status"],"completed")
                self.assertEqual(result["selected_node"],"TEST-PC")
                self.assertEqual(result["worker_result"]["result"]["words"],3)

                replay=Request("http://127.0.0.1:18100/route",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
                with self.assertRaises(HTTPError) as err: urlopen(replay)
                self.assertEqual(err.exception.code,409)

                bad=Request("http://127.0.0.1:18100/route",data=b'{"task":"echo","text":"x","request_id":"unauth-123"}',headers={"Content-Type":"application/json"})
                with self.assertRaises(HTTPError) as err: urlopen(bad)
                self.assertEqual(err.exception.code,401)
            finally:
                router.terminate(); worker.terminate()
                router.wait(timeout=3); worker.wait(timeout=3)

if __name__=="__main__": unittest.main()
