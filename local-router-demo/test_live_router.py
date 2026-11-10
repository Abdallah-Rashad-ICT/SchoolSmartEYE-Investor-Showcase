import json, os, subprocess, sys, tempfile, time, unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=os.path.dirname(__file__)
class LiveRouterSmokeTest(unittest.TestCase):
    def test_worker_and_router_end_to_end(self):
        token="test-token"
        env=os.environ.copy(); env.update({"SSE_DEMO_TOKEN":token,"SSE_BIND":"127.0.0.1","SSE_NODE_ID":"TEST-PC","SSE_PORT":"18101","SSE_ROUTER_PORT":"18100","SSE_NODES":"TEST-PC=http://127.0.0.1:18101"})
        worker=subprocess.Popen([sys.executable,os.path.join(ROOT,"worker.py")],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        router=subprocess.Popen([sys.executable,os.path.join(ROOT,"router.py")],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for _ in range(40):
                try:
                    with urlopen("http://127.0.0.1:18100/health",timeout=.2): break
                except Exception: time.sleep(.1)
            req=Request("http://127.0.0.1:18100/route",data=json.dumps({"task":"text_stats","text":"hello school AI"}).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
            with urlopen(req,timeout=3) as r: result=json.loads(r.read())
            self.assertEqual(result["status"],"completed")
            self.assertEqual(result["selected_node"],"TEST-PC")
            self.assertEqual(result["worker_result"]["result"]["words"],3)
            bad=Request("http://127.0.0.1:18100/route",data=b'{"task":"echo","text":"x"}',headers={"Content-Type":"application/json"})
            with self.assertRaises(HTTPError) as err: urlopen(bad)
            self.assertEqual(err.exception.code,401)
        finally:
            router.terminate(); worker.terminate()
            router.wait(timeout=3); worker.wait(timeout=3)
if __name__=="__main__": unittest.main()
