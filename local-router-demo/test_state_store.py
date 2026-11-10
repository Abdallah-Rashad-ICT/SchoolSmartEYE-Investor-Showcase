import os
import tempfile
import threading
import unittest

from state_store import SQLiteStateStore


class SQLiteStateStoreTests(unittest.TestCase):
    def test_replay_guard_persists_across_store_instances(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=os.path.join(tmp,"state.sqlite3")
            first=SQLiteStateStore(path)
            self.assertTrue(first.claim_request("request-0001"))
            second=SQLiteStateStore(path)
            self.assertFalse(second.claim_request("request-0001"))
            self.assertTrue(second.claim_request("request-0002"))

    def test_concurrent_claim_accepts_same_id_exactly_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=os.path.join(tmp,"state.sqlite3")
            stores=[SQLiteStateStore(path) for _ in range(8)]
            barrier=threading.Barrier(len(stores))
            outcomes=[]
            lock=threading.Lock()

            def claim(store):
                barrier.wait()
                result=store.claim_request("concurrent-request-01")
                with lock:
                    outcomes.append(result)

            threads=[threading.Thread(target=claim,args=(store,)) for store in stores]
            for thread in threads: thread.start()
            for thread in threads: thread.join(timeout=15)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(outcomes.count(True),1)
            self.assertEqual(outcomes.count(False),len(stores)-1)

    def test_node_registration_upserts_and_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=SQLiteStateStore(os.path.join(tmp,"state.sqlite3"))
            store.register_node("PC2","http://192.168.1.20:8101",["text_stats"])
            store.register_node("PC2","http://192.168.1.21:8101",["echo"])
            nodes=store.list_nodes()
            self.assertEqual(len(nodes),1)
            self.assertEqual(nodes[0]["url"],"http://192.168.1.21:8101")
            self.assertEqual(nodes[0]["capabilities"],["echo"])


if __name__=="__main__":
    unittest.main()
